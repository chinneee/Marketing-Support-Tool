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

   # Combined Step: Upload, Process & Export Data Files
    st.subheader("📂 Step 4: Upload, Process & Export Data")
    
    uploaded_files = st.file_uploader(
        "Upload Excel files (DD_MM_YYYY format in filename)",
        type=['xlsx'],
        accept_multiple_files=True,
        key="dsp_uploader",
        help="Files are processed automatically upon upload"
    )
    
    if uploaded_files:
        # File upload success indicator
        col1, col2 = st.columns([3, 1])
        with col1:
            st.success(f"✅ {len(uploaded_files)} file(s) uploaded successfully")
        with col2:
            total_size = sum(f.size for f in uploaded_files) / (1024 * 1024)  # Convert to MB
            st.metric("Total Size", f"{total_size:.2f} MB")

        # Auto-process files
        current_file_names = [f.name for f in uploaded_files]
        
        # Initialize session state
        if 'last_processed_files' not in st.session_state:
            st.session_state.last_processed_files = []
        
        # Process if files changed
        if current_file_names != st.session_state.last_processed_files:
            # Processing section
            progress_placeholder = st.empty()
            status_placeholder = st.empty()
            
            with status_placeholder.container():
                st.markdown("### ⚙️ Processing Files...")
                progress_bar = st.progress(0)
                status_text = st.empty()
            
            try:
                # Simulate progress steps
                status_text.text("Initializing processor...")
                progress_bar.progress(20)
                
                processor = DSPProcessor(credentials_dict, sheet_id, selected_market)
                
                status_text.text("Reading and validating files...")
                progress_bar.progress(40)
                
                result_df, processed_files = processor.process_files(uploaded_files)
                
                status_text.text("Finalizing data...")
                progress_bar.progress(80)
                
                # Store in session state
                st.session_state.result_df = result_df
                st.session_state.processor = processor
                st.session_state.processed_files = processed_files
                st.session_state.last_processed_files = current_file_names
                
                progress_bar.progress(100)
                status_text.text("✅ Processing complete!")
                
                # Clear progress indicators after a moment
                import time
                time.sleep(0.5)
                status_placeholder.empty()
                
                if not result_df.empty:
                    # Success message with metrics
                    st.success(f"✅ Successfully processed {len(processed_files)} file(s)")
                    
                    # Key metrics in cards
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("📊 Total Rows", f"{len(result_df):,}")
                    with col2:
                        st.metric("📝 Columns", len(result_df.columns))
                    with col3:
                        st.metric("📁 Files", len(processed_files))
                    with col4:
                        # Calculate data completeness
                        completeness = (1 - result_df.isnull().sum().sum() / (len(result_df) * len(result_df.columns))) * 100
                        st.metric("✓ Completeness", f"{completeness:.1f}%")
                    
                else:
                    st.error("❌ No data found in uploaded files")
                    st.warning("Please verify your files contain data in the expected format.")
                    
            except Exception as e:
                status_placeholder.empty()
                st.error(f"❌ Error processing files: {str(e)}")
                st.exception(e)
                # Clear session state on error
                for key in ['result_df', 'processor', 'processed_files', 'last_processed_files']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.session_state.last_processed_files = []
        
        # Display processed data and export options
        if 'result_df' in st.session_state and not st.session_state.result_df.empty:
            result_df = st.session_state.result_df
            processed_files = st.session_state.processed_files
            
            # Preview controls in one row
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                preview_rows = st.slider(
                    "Preview rows",
                    min_value=5,
                    max_value=min(50, len(result_df)),
                    value=10,
                    step=5
                )
            with col2:
                show_all = st.checkbox("All columns", value=False)

            
            # Display dataframe
            display_df = result_df if show_all else (result_df.iloc[:, :8] if len(result_df.columns) > 8 else result_df)
            st.dataframe(
                display_df.head(preview_rows),
                use_container_width=True,
                height=300
            )
            
            if not show_all and len(result_df.columns) > 8:
                st.caption(f"Showing 8 of {len(result_df.columns)} columns. Enable 'All columns' to see more.")
            
            st.markdown("---")
            
            # Export section - Simplified and prominent
            st.markdown("### 📤 Export Options")
            st.caption("Choose how to save or upload your processed data")
            
            # Helper function for Excel export
            def export_to_excel(df, market):
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Data')
                output.seek(0)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                return output, f"XN_{market}_{timestamp}.xlsx"
            
            # Export buttons in a clean layout
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📥 Download Locally")
                st.caption("Save processed data to your computer")
                
                # Excel download
                excel_data, filename = export_to_excel(result_df, selected_market)
                st.download_button(
                    label="💾 Download Excel",
                    data=excel_data,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    help="Download as Excel file (.xlsx)"
                )
                
                # CSV download
                csv = result_df.to_csv(index=False).encode('utf-8')
                csv_filename = filename.replace('.xlsx', '.csv')
                st.download_button(
                    label="📄 Download CSV",
                    data=csv,
                    file_name=csv_filename,
                    mime="text/csv",
                    use_container_width=True,
                    help="Download as CSV file (lighter format)"
                )
            
            with col2:
                st.markdown("#### ☁️ Upload to Cloud")
                st.caption("Push data directly to Google Sheets")
                
                # Info box
                st.info(f"**Target:** {selected_market} market sheet\n\n**Rows:** {len(result_df):,}")
                
                # Upload button - prominent and clear
                if st.button(
                    "🚀 Push to Google Sheets",
                    type="primary",
                    use_container_width=True,
                    help="Upload data to your Google Sheets"
                ):
                    upload_placeholder = st.empty()
                    
                    with upload_placeholder.container():
                        st.markdown("---")
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        try:
                            status_text.text("Connecting to Google Sheets...")
                            progress_bar.progress(25)
                            
                            status_text.text("Uploading data...")
                            progress_bar.progress(50)
                            
                            success = st.session_state.processor.append_to_sheets(result_df)
                            
                            status_text.text("Verifying upload...")
                            progress_bar.progress(90)
                            
                            if success:
                                progress_bar.progress(100)
                                status_text.text("✅ Upload complete!")
                                time.sleep(0.5)
                                upload_placeholder.empty()
                                
                                st.success(f"✅ Successfully uploaded {len(result_df):,} rows to Google Sheets!")
                                st.balloons()
                                
                                # Show success details
                                with st.expander("📊 Upload Summary", expanded=True):
                                    st.markdown(f"""
                                    - **Market:** {selected_market}
                                    - **Rows uploaded:** {len(result_df):,}
                                    - **Columns:** {len(result_df.columns)}
                                    - **Files processed:** {len(processed_files)}
                                    - **Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                                    """)
                            else:
                                upload_placeholder.empty()
                                st.error("❌ Upload failed - Please check the error messages above")
                                
                        except Exception as e:
                            upload_placeholder.empty()
                            st.error(f"❌ Upload failed: {str(e)}")
                            with st.expander("🔍 Error Details"):
                                st.code(traceback.format_exc())
            
    else:
        # Empty state with helpful instructions
        st.info("👆 **Upload Excel files to get started**")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **📌 File Requirements:**
            - Format: `.xlsx` (Excel 2007+)
            - Filename must contain: `DD_MM_YYYY`
            - Example: `sales_report_15_10_2025.xlsx`
            """)
        
        with col2:
            st.markdown("""
            **⚡ What happens next:**
            1. Files are validated
            2. Data is automatically processed
            3. Preview & export options appear
            4. Choose download or upload to Sheets
            """)
        


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
