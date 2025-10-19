# dsp_xnurta.py
import streamlit as st
import pandas as pd
import numpy as np
import io
import re
import traceback
from datetime import datetime
from google.oauth2.service_account import Credentials
import gspread

# ---------------------------
#  DSP Processor
# ---------------------------

class DSPProcessor:
    """
    DSP XNurta Processor
    - Process uploaded Excel files (folder -> in local version)
    - Logic:
      * Drop "Creative Asset" column if exists
      * Drop last row (assumed totals)
      * Create "ASIN" from first 10 chars of "Creative"
      * Extract date from filename (YYYYMMDD pattern) -> datetime.date
      * Insert "Date" column next to "Creative"
    """

    def __init__(self, credentials_dict: dict, sheet_id: str, worksheet_base_name: str = "Raw_DSP_H2_2025"):
        self.credentials_dict = credentials_dict
        self.sheet_id = sheet_id
        self.worksheet_base_name = worksheet_base_name
        self.client = None
        self.spreadsheet = None
        self.worksheet = None

    def _init_google_sheets(self, market: str):
        """Initialize Google Sheets client and worksheet (create if missing)."""
        try:
            if self.client is None:
                scopes = [
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive"
                ]
                creds = Credentials.from_service_account_info(self.credentials_dict, scopes=scopes)
                self.client = gspread.authorize(creds)
                self.spreadsheet = self.client.open_by_key(self.sheet_id)

            worksheet_name = f"{self.worksheet_base_name}_{market}"
            try:
                self.worksheet = self.spreadsheet.worksheet(worksheet_name)
                st.success(f"✅ Found worksheet: {worksheet_name}")
            except gspread.exceptions.WorksheetNotFound:
                st.warning(f"⚠️ Worksheet '{worksheet_name}' not found. Creating new one...")
                self.worksheet = self.spreadsheet.add_worksheet(title=worksheet_name, rows="2000", cols="50")
                st.success(f"✅ Created new worksheet: {worksheet_name}")

            return True

        except Exception as e:
            st.error(f"❌ Error initializing Google Sheets: {e}")
            st.text(traceback.format_exc())
            return False

    @staticmethod
    def extract_date_from_filename(filename: str):
        """
        Extract first 8-digit pattern like YYYYMMDD from filename and return a datetime.date object.
        If not found, returns None.
        """
        match = re.search(r"(\d{8})", filename)
        if match:
            try:
                return datetime.strptime(match.group(1), "%Y%m%d").date()
            except Exception:
                return None
        return None

    @staticmethod
    def process_single_file_content(file_content: bytes, filename: str) -> pd.DataFrame:
        """
        Process an in-memory Excel file (bytes). Returns processed DataFrame or empty df on error.
        """
        try:
            df = pd.read_excel(io.BytesIO(file_content))
        except Exception as e:
            raise ValueError(f"Failed to read Excel {filename}: {e}")

        if df.empty:
            raise ValueError(f"File {filename} contains no data")

        # Drop 'Creative Asset' if exists
        if "Creative Asset" in df.columns:
            try:
                df = df.drop(columns=["Creative Asset"])
            except Exception:
                pass

        # Drop last row (commonly totals)
        if len(df) > 1:
            df = df.iloc[:-1, :].copy()
        else:
            # nothing meaningful to keep
            df = df.copy()

        # Ensure 'Creative' column exists
        if "Creative" not in df.columns:
            raise ValueError(f"'Creative' column not found in {filename}")

        # Create ASIN column (first 10 chars of Creative, uppercased)
        df.insert(0, "ASIN", df["Creative"].astype(str).str[:10].str.upper())

        # Extract date from filename and insert after 'Creative' column
        file_date = DSPProcessor.extract_date_from_filename(filename)
        # Use pandas datetime for consistency
        if file_date is not None:
            date_val = pd.to_datetime(file_date)
        else:
            date_val = pd.NaT

        # Find index of Creative column (after insertion ASIN, the index shifted)
        try:
            creative_idx = list(df.columns).index("Creative")
            # Insert Date after Creative column
            before = df.iloc[:, :creative_idx + 1].copy()
            after = df.iloc[:, creative_idx + 1:].copy()
            date_series = pd.Series([date_val] * len(df), name="Date", index=df.index)
            df = pd.concat([before, date_series, after], axis=1)
        except Exception:
            # fallback: just add Date as a new column at the end
            df["Date"] = date_val
        
        required_columns = [
            "ASIN", "Creative", "Date", "Total cost", "Total product sales", "eCPM",
            "Total CPDPV", "Total ROAS", "Total percent of purchases new-to-brand",
            "CTR", "Total DPVR", "Total ATCR", "Total eCPP", "ROAS", "VCR",
            "Impressions", "Click-throughs", "Total DPV", "Total ATC", "Total purchase",
            "Total units sold", "Branded Searches", "eCPC", "DPV", "DPVR", "CPDPV",
            "ATC", "ATCR", "Total CPATC", "CPATC", "Product sales",
            "Total new-to-brand product sales", "New-to-brand product Sales",
            "Total new-to-brand ROAS", "New-to-brand return on advertising spend",
            "Purchases", "Total new-to-brand purchases", "New-to-brand purchases",
            "Total Purchase Rate"
        ]

        # Thêm cột trống nếu thiếu
        for col in required_columns:
            if col not in df.columns:
                df[col] = np.nan

        # Sắp xếp lại thứ tự cột theo chuẩn
        df = df.loc[:, required_columns]
        return df

    def process_files(self, uploaded_files: list) -> tuple:
        """
        uploaded_files: list of streamlit UploadedFile objects
        Returns (merged_df, processed_filenames)
        """
        all_dfs = []
        processed_files = []

        for uploaded_file in uploaded_files:
            try:
                content = uploaded_file.read()
                df = self.process_single_file_content(content, uploaded_file.name)
                all_dfs.append(df)
                processed_files.append(uploaded_file.name)
            except Exception as e:
                st.error(f"⚠️ Error processing {uploaded_file.name}: {e}")
                st.text(traceback.format_exc())

        if not all_dfs:
            return pd.DataFrame(), []

        merged_df = pd.concat(all_dfs, ignore_index=True, sort=False)

        # Optionally reorder columns to put ASIN, Date at front
        cols = list(merged_df.columns)
        desired_front = ["ASIN", "Creative", "Date"]
        new_cols = [c for c in desired_front if c in cols] + [c for c in cols if c not in desired_front]
        merged_df = merged_df.loc[:, new_cols]

        return merged_df, processed_files

    def append_to_sheets(self, df: pd.DataFrame, market: str) -> bool:
        """
        Append df to the Google Sheet worksheet for the given market.
        Responsible for ensuring enough rows and writing with USER_ENTERED.
        """
        if df.empty:
            st.warning("⚠️ No data to upload")
            return False

        ok = self._init_google_sheets(market)
        if not ok:
            return False

        try:
            # Format datetime columns to M/D/YYYY for Google Sheets to parse
            safe_df = df.copy()
            datetime_cols = safe_df.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns
            for col in datetime_cols:
                safe_df[col] = safe_df[col].apply(lambda x: f"{x.month}/{x.day}/{x.year}" if pd.notna(x) else "")

            # Replace NaN with empty string
            safe_df = safe_df.fillna("")

            values_to_append = safe_df.values.tolist()

            # Ensure enough rows
            needed_rows = (len(values_to_append) + 1)  # +1 if header exists already; we'll append without header
            current_rows = self.worksheet.row_count
            # If the worksheet is mostly empty, we append starting from the first empty row
            existing_vals = self.worksheet.get_all_values()
            existing_rows = len(existing_vals)

            start_row = max(existing_rows + 1, 2)  # leave header row as row 1 (assuming header exists)
            end_row = start_row + len(values_to_append) - 1

            if end_row > current_rows:
                add_count = end_row - current_rows
                self.worksheet.add_rows(add_count)
                st.info(f"📈 Added {add_count} rows to sheet to fit data.")

            # Calculate end column
            end_col_index = safe_df.shape[1]
            end_col_letter = gspread.utils.rowcol_to_a1(1, end_col_index).split('1')[0]

            range_name = f"A{start_row}:{end_col_letter}{end_row}"
            st.info(f"📊 Uploading to range: {range_name}")

            # Append values using update (USER_ENTERED) — write without header
            self.worksheet.update(values=values_to_append, range_name=range_name, value_input_option="USER_ENTERED")

            st.success(f"✅ Successfully uploaded {len(values_to_append)} rows to sheet!")
            return True

        except Exception as e:
            st.error(f"❌ Error uploading to Google Sheets: {e}")
            st.text(traceback.format_exc())
            return False


# ---------------------------
#  Helper: Export to Excel
# ---------------------------

def export_to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Data"):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    out.seek(0)
    return out


# ---------------------------
#  Streamlit page: dsp_xnurta_page
# ---------------------------

def dsp_xnurta_page():
    st.subheader("🔐 Step 1: Upload Google Credentials")
    credentials_file = st.file_uploader(
        "Upload your credential.json file",
        type=["json"],
        key="dsp_credentials_uploader",
        help="Google Service Account credentials JSON (do not push to GitHub)"
    )

    credentials_dict = None
    if credentials_file:
        try:
            credentials_dict = json_load_stream(credentials_file)
            st.success("✅ Credentials loaded")
            with st.expander("📋 Credential Info"):
                st.write(f"**Project ID:** {credentials_dict.get('project_id', 'N/A')}")
                st.write(f"**Client Email:** {credentials_dict.get('client_email', 'N/A')}")
        except Exception as e:
            st.error(f"❌ Invalid credentials file: {e}")
            st.text(traceback.format_exc())
            return
    else:
        st.warning("⚠️ Please upload credential.json to continue")
        st.info("💡 You need Google Service Account credentials to push data to Google Sheets")
        return

    st.markdown("---")

    # Step 2: Sheet ID
    st.subheader("📝 Step 2: Enter Google Sheet ID")
    sheet_id = st.text_input(
        "Google Sheet ID",
        value="1rqH3SePVbpwcj1oD4Bqaa40IbkyKUi7aRBThlBdnEu4",
        help="Find this in your Google Sheet URL: docs.google.com/spreadsheets/d/{SHEET_ID}/edit",
        key="dsp_sheet_id"
    )
    if not sheet_id:
        st.warning("⚠️ Please enter Google Sheet ID to continue")
        return

    st.markdown("---")

    # Step 3: Select Market
    st.subheader("🌍 Step 3: Select Market")
    if "dsp_selected_market" not in st.session_state:
        st.session_state.dsp_selected_market = "US"

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🇺🇸 US Market", use_container_width=True, key="dsp_us"):
            st.session_state.dsp_selected_market = "US"
    with col2:
        if st.button("🇨🇦 CA Market", use_container_width=True, key="dsp_ca"):
            st.session_state.dsp_selected_market = "CA"
    with col3:
        if st.button("🇬🇧 UK Market", use_container_width=True, key="dsp_uk"):
            st.session_state.dsp_selected_market = "UK"

    selected_market = st.session_state.dsp_selected_market
    st.info(f"📍 Selected Market: **{selected_market}**")

    st.markdown("---")

    # Step 4: Upload files
    st.subheader("📂 Step 4: Upload DSP Excel files (.xlsx)")
    uploaded_files = st.file_uploader(
        "Upload monthly DSP files (multiple allowed)",
        type=["xlsx"],
        accept_multiple_files=True,
        key="dsp_uploaded_files"
    )

    if not uploaded_files:
        st.info("📁 Please upload DSP files to continue")
        return

    st.success(f"✅ {len(uploaded_files)} file(s) uploaded")
    with st.expander("📁 Uploaded Files"):
        for f in uploaded_files:
            st.text(f"• {f.name}")

    st.markdown("---")

    # Step 5: Process files
    st.subheader("⚙️ Step 5: Process Files")
    if st.button("🔄 Process Files", use_container_width=True, key="dsp_process"):
        with st.spinner("Processing DSP files..."):
            processor = DSPProcessor(credentials_dict, sheet_id)
            merged_df, processed_files = processor.process_files(uploaded_files)
            if merged_df.empty:
                st.error("❌ No data processed")
                return

            # Save to session state
            st.session_state.dsp_merged_df = merged_df
            st.session_state.dsp_processor = processor
            st.session_state.dsp_processed_files = processed_files

            st.success(f"✅ Successfully processed {len(processed_files)} files")
            st.info(f"📊 Total rows: {len(merged_df)}")

            # Show sample preview
            with st.expander("👁️ Preview Data (First 10 rows)"):
                st.dataframe(merged_df.head(10), use_container_width=True)

    # Step 6: Export / Push
    if "dsp_merged_df" in st.session_state and not st.session_state.dsp_merged_df.empty:
        st.markdown("---")
        st.subheader("📤 Step 6: Export / Push")
        st.caption("Export to Excel, push to Google Sheets, or both")

        def export_action(df, market):
            excel_bytes = export_to_excel_bytes(df, sheet_name=f"DSP_{market}")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"DSP_{market}_{timestamp}.xlsx"
            return excel_bytes, filename

        col1, col2, col3 = st.columns(3)

        with col1:
            excel_bytes, filename = export_action(st.session_state.dsp_merged_df, selected_market)
            st.download_button(
                label="📥 Export to Excel",
                data=excel_bytes,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        with col2:
            if st.button("☁️ Push to Google Sheets", use_container_width=True, key="dsp_push"):
                with st.spinner("Uploading to Google Sheets..."):
                    success = st.session_state.dsp_processor.append_to_sheets(st.session_state.dsp_merged_df, selected_market)
                    if success:
                        st.success(f"✅ Uploaded {len(st.session_state.dsp_merged_df)} rows to Google Sheets!")
                        st.balloons()
                    else:
                        st.error("❌ Upload failed - check logs above")

    else:
        st.info("📁 Please process files to access export/upload actions")


# ---------------------------
#  Small utility to load json from uploaded file
# ---------------------------

def json_load_stream(uploaded_file):
    """
    uploaded_file: streamlit UploadedFile
    returns loaded json dict
    """
    try:
        # uploaded_file may be a SpooledTemporaryFile-like object
        uploaded_file.seek(0)
        import json
        j = json.load(uploaded_file)
        return j
    finally:
        try:
            uploaded_file.seek(0)
        except Exception:
            pass
