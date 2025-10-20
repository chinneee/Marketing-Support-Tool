import streamlit as st
import pandas as pd
import numpy as np
import io
import re
import traceback
import time
from datetime import datetime
from google.oauth2.service_account import Credentials
import gspread
import json
import pytz

# ============================================================
# DSP Processor Class
# ============================================================
class DSPProcessor:
    """DSP XNurta Data Processor"""
    
    def __init__(self, credentials_dict: dict, sheet_id: str, worksheet_base_name: str = "Raw_DSP_H2_2025"):
        self.credentials_dict = credentials_dict
        self.sheet_id = sheet_id
        self.worksheet_base_name = worksheet_base_name
        self.client = None
        self.spreadsheet = None
        self.worksheet = None
    
    def _init_google_sheets(self, market: str):
        """Initialize Google Sheets client and worksheet"""
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
            except gspread.exceptions.WorksheetNotFound:
                self.worksheet = self.spreadsheet.add_worksheet(
                    title=worksheet_name, 
                    rows="2000", 
                    cols="50"
                )
            
            return True
            
        except Exception as e:
            raise Exception(f"Error initializing Google Sheets: {e}")
    
    @staticmethod
    def extract_date_from_filename(filename: str):
        """Extract YYYYMMDD pattern from filename"""
        match = re.search(r"(\d{8})", filename)
        if match:
            try:
                return datetime.strptime(match.group(1), "%Y%m%d").date()
            except Exception:
                return None
        return None
    
    @staticmethod
    def process_single_file_content(file_content: bytes, filename: str) -> pd.DataFrame:
        """Process a single Excel file"""
        try:
            df = pd.read_excel(io.BytesIO(file_content))
        except Exception as e:
            raise ValueError(f"Failed to read Excel {filename}: {e}")
        
        if df.empty:
            raise ValueError(f"File {filename} contains no data")
        
        # Drop 'Creative Asset' if exists
        if "Creative Asset" in df.columns:
            df = df.drop(columns=["Creative Asset"])
        
        # Drop last row (totals)
        if len(df) > 1:
            df = df.iloc[:-1, :].copy()
        else:
            df = df.copy()
        
        # Ensure 'Creative' column exists
        if "Creative" not in df.columns:
            raise ValueError(f"'Creative' column not found in {filename}")
        
        # Create ASIN column
        df.insert(0, "ASIN", df["Creative"].astype(str).str[:10].str.upper())
        
        # Extract date
        file_date = DSPProcessor.extract_date_from_filename(filename)
        date_val = pd.to_datetime(file_date) if file_date else pd.NaT
        
        # Insert Date column after Creative
        try:
            creative_idx = list(df.columns).index("Creative")
            before = df.iloc[:, :creative_idx + 1].copy()
            after = df.iloc[:, creative_idx + 1:].copy()
            date_series = pd.Series([date_val] * len(df), name="Date", index=df.index)
            df = pd.concat([before, date_series, after], axis=1)
        except Exception:
            df["Date"] = date_val
        
        # Define required columns
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
        
        # Add missing columns
        for col in required_columns:
            if col not in df.columns:
                df[col] = np.nan
        
        # Reorder columns
        df = df.loc[:, required_columns]
        
        return df
    
    def process_files(self, uploaded_files: list) -> tuple:
        """Process multiple uploaded files"""
        all_dfs = []
        processed_files = []
        
        for uploaded_file in uploaded_files:
            try:
                content = uploaded_file.read()
                df = self.process_single_file_content(content, uploaded_file.name)
                all_dfs.append(df)
                processed_files.append({
                    'file_name': uploaded_file.name,
                    'rows_count': len(df)
                })
            except Exception as e:
                st.error(f"⚠️ Error processing {uploaded_file.name}: {e}")
        
        if not all_dfs:
            return pd.DataFrame(), []
        
        merged_df = pd.concat(all_dfs, ignore_index=True, sort=False)
        
        # Reorder columns
        cols = list(merged_df.columns)
        desired_front = ["ASIN", "Creative", "Date"]
        new_cols = [c for c in desired_front if c in cols] + [c for c in cols if c not in desired_front]
        merged_df = merged_df.loc[:, new_cols]
        
        return merged_df, processed_files
    
    def append_to_sheets(self, df: pd.DataFrame, market: str) -> bool:
        """Append DataFrame to Google Sheets"""
        if df.empty:
            return False
        
        ok = self._init_google_sheets(market)
        if not ok:
            return False
        
        try:
            safe_df = df.copy()
            
            # Format datetime columns
            datetime_cols = safe_df.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns
            for col in datetime_cols:
                safe_df[col] = safe_df[col].apply(lambda x: f"{x.month}/{x.day}/{x.year}" if pd.notna(x) else "")
            
            safe_df = safe_df.fillna("")
            values_to_append = safe_df.values.tolist()
            
            # Calculate rows needed
            existing_vals = self.worksheet.get_all_values()
            existing_rows = len(existing_vals)
            start_row = max(existing_rows + 1, 2)
            end_row = start_row + len(values_to_append) - 1
            
            current_rows = self.worksheet.row_count
            if end_row > current_rows:
                add_count = end_row - current_rows
                self.worksheet.add_rows(add_count)
            
            # Calculate range
            end_col_index = safe_df.shape[1]
            end_col_letter = gspread.utils.rowcol_to_a1(1, end_col_index).split('1')[0]
            range_name = f"A{start_row}:{end_col_letter}{end_row}"
            
            # Upload data
            self.worksheet.update(
                values=values_to_append, 
                range_name=range_name, 
                value_input_option="USER_ENTERED"
            )
            
            return True
            
        except Exception as e:
            raise Exception(f"Error uploading to Google Sheets: {e}")


# ============================================================
# Helper Functions
# ============================================================
def export_to_excel_bytes(df: pd.DataFrame, market: str):
    """Export DataFrame to Excel bytes"""
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=f"DSP_{market}")
    out.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"DSP_{market}_{timestamp}.xlsx"
    return out, filename


def json_load_stream(uploaded_file):
    """Load JSON from uploaded file"""
    try:
        uploaded_file.seek(0)
        j = json.load(uploaded_file)
        return j
    finally:
        try:
            uploaded_file.seek(0)
        except Exception:
            pass


# ============================================================
# Main Page Function
# ============================================================
def dsp_xnurta_page():
    """DSP XNurta data upload page"""
    
    # Step 1: Upload credentials
    st.subheader("🔐 Step 1: Upload Google Credentials")
    
    credentials_file = st.file_uploader(
        "Upload credential.json file",
        type=["json"],
        key="dsp_credentials_uploader",
        help="Google Service Account credentials JSON"
    )
    
    credentials_dict = None
    if credentials_file:
        try:
            credentials_dict = json_load_stream(credentials_file)
            st.success("✅ Credentials loaded successfully")
        except Exception as e:
            st.error(f"❌ Invalid credentials file: {e}")
            return
    else:
        st.warning("⚠️ Please upload credential.json file to continue")
        return
    
    st.markdown("---")
    
    # Step 2: Enter Sheet ID
    st.subheader("📝 Step 2: Enter Google Sheet ID")
    
    sheet_id = st.text_input(
        "Google Sheet ID",
        value="1GpPsWt_fWCfHnEdFQJIsNBebhqFnIiExsHA8SjNUhFk",
        help="Format: docs.google.com/spreadsheets/d/{SHEET_ID}/edit",
        key="dsp_sheet_id"
    )
    
    if not sheet_id:
        st.warning("⚠️ Please enter Google Sheet ID to continue")
        return
    
    st.markdown("---")
    
    # Step 3: Select Market
    st.subheader("🌍 Step 3: Select Target Market")
    
    if "dsp_selected_market" not in st.session_state:
        st.session_state.dsp_selected_market = "US"
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button(
            "🇺🇸 US Market", 
            use_container_width=True,
            type="primary" if st.session_state.dsp_selected_market == "US" else "secondary",
            key="dsp_us"
        ):
            st.session_state.dsp_selected_market = "US"
    
    with col2:
        if st.button(
            "🇨🇦 CA Market",
            use_container_width=True,
            type="primary" if st.session_state.dsp_selected_market == "CA" else "secondary",
            key="dsp_ca"
        ):
            st.session_state.dsp_selected_market = "CA"
    
    with col3:
        if st.button(
            "🇬🇧 UK Market",
            use_container_width=True,
            type="primary" if st.session_state.dsp_selected_market == "UK" else "secondary",
            key="dsp_uk"
        ):
            st.session_state.dsp_selected_market = "UK"
    
    selected_market = st.session_state.dsp_selected_market
    st.info(f"📍 Selected Market: **{selected_market}**")
    
    st.markdown("---")
    
    # Step 4: Upload, Process & Export Data
    st.subheader("📂 Step 4: Upload, Process & Export Data")
    
    uploaded_files = st.file_uploader(
        "Upload DSP Excel files (YYYYMMDD format in filename)",
        type=['xlsx'],
        accept_multiple_files=True,
        key="dsp_uploader",
        help="Files are processed automatically upon upload"
    )
    
    if uploaded_files:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.success(f"✅ {len(uploaded_files)} file(s) uploaded successfully")
        with col2:
            total_size = sum(f.size for f in uploaded_files) / (1024 * 1024)
            st.metric("Total Size", f"{total_size:.2f} MB")
        
        current_file_names = [f.name for f in uploaded_files]
        
        if 'dsp_last_processed_files' not in st.session_state:
            st.session_state.dsp_last_processed_files = []
        
        if current_file_names != st.session_state.dsp_last_processed_files:
            with st.spinner("⚙️ Processing files..."):
                try:
                    processor = DSPProcessor(credentials_dict, sheet_id)
                    result_df, processed_files = processor.process_files(uploaded_files)
                    
                    st.session_state.dsp_result_df = result_df
                    st.session_state.dsp_processor = processor
                    st.session_state.dsp_processed_files = processed_files
                    st.session_state.dsp_last_processed_files = current_file_names
                    
                    if not result_df.empty:
                        st.success("✅ Processing complete!")
                    else:
                        st.error("❌ No data found in uploaded files")
                        
                except Exception as e:
                    st.error(f"❌ Error processing files: {str(e)}")
                    for key in ['dsp_result_df', 'dsp_processor', 'dsp_processed_files', 'dsp_last_processed_files']:
                        if key in st.session_state:
                            del st.session_state[key]
        
        # Display processed data
        if 'dsp_result_df' in st.session_state and not st.session_state.dsp_result_df.empty:
            result_df = st.session_state.dsp_result_df
            processed_files = st.session_state.dsp_processed_files
            
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📊 Total Rows", f"{len(result_df):,}")
            with col2:
                st.metric("📝 Columns", len(result_df.columns))
            with col3:
                st.metric("📁 Files", len(processed_files))
            with col4:
                completeness = (1 - result_df.isnull().sum().sum() / (len(result_df) * len(result_df.columns))) * 100
                st.metric("✓ Completeness", f"{completeness:.1f}%")
            
            # Preview
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                preview_rows = st.slider(
                    "Preview rows",
                    min_value=5,
                    max_value=min(50, len(result_df)),
                    value=10,
                    step=5,
                    key="dsp_preview_slider"
                )
            with col2:
                show_all = st.checkbox("All columns", value=False, key="dsp_show_all")
            
            display_df = result_df if show_all else (result_df.iloc[:, :8] if len(result_df.columns) > 8 else result_df)
            st.dataframe(display_df.head(preview_rows), use_container_width=True, height=300)
            
            if not show_all and len(result_df.columns) > 8:
                st.caption(f"Showing 8 of {len(result_df.columns)} columns. Enable 'All columns' to see more.")
            
            st.markdown("---")
            
            # Export section
            st.markdown("### 📤 Export Options")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📥 Download Locally")
                
                excel_data, filename = export_to_excel_bytes(result_df, selected_market)
                st.download_button(
                    label="💾 Download Excel",
                    data=excel_data,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key="dsp_download_excel"
                )
                
                csv = result_df.to_csv(index=False).encode('utf-8')
                csv_filename = filename.replace('.xlsx', '.csv')
                st.download_button(
                    label="📄 Download CSV",
                    data=csv,
                    file_name=csv_filename,
                    mime="text/csv",
                    use_container_width=True,
                    key="dsp_download_csv"
                )
            
            with col2:
                st.markdown("#### ☁️ Upload to Cloud")
                st.info(f"**Target:** {selected_market} market sheet\n\n**Rows:** {len(result_df):,}")
                
                if st.button(
                    "🚀 Push to Google Sheets",
                    type="primary",
                    use_container_width=True,
                    key="dsp_push_to_sheets_btn"
                ):
                    try:
                        with st.spinner("Uploading to Google Sheets..."):
                            success = st.session_state.dsp_processor.append_to_sheets(result_df, selected_market)
                        
                        if success:
                            st.success(f"✅ Successfully uploaded {len(result_df):,} rows!")
                            
                            with st.expander("📊 Upload Summary", expanded=True):
                                st.markdown(f"""
                                - **Market:** {selected_market}
                                - **Rows uploaded:** {len(result_df):,}
                                - **Columns:** {len(result_df.columns)}
                                - **Files processed:** {len(processed_files)}
                                - **Timestamp:** {datetime.now(pytz.timezone('Asia/Ho_Chi_Minh')).strftime('%Y-%m-%d %H:%M:%S')}
                                """)
                        else:
                            st.error("❌ Upload failed")
                            
                    except Exception as e:
                        st.error(f"❌ Upload failed: {str(e)}")
                        with st.expander("🔍 Error Details"):
                            st.code(traceback.format_exc())
    
    else:
        st.info("👆 **Upload Excel files to get started**")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **📌 File Requirements:**
            - Format: `.xlsx` (Excel 2007+)
            - Filename must contain: `YYYYMMDD`
            - Example: `dsp_report_20251015.xlsx`
            - Must have 'Creative' column
            """)
        
        with col2:
            st.markdown("""
            **⚡ What happens next:**
            1. Files are validated
            2. Data is automatically processed
            3. Preview & export options appear
            4. Choose download or upload to Sheets
            """)