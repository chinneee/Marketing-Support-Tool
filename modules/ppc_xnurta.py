import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import io
import json
import re
import traceback
import warnings
import time
import pytz

# Suppress warnings
warnings.filterwarnings('ignore', category=FutureWarning)
class PPCProcessor:
    """PPC XNurta Data Processor"""
    
    def __init__(self, credentials_dict, sheet_id, market):
        self.credentials_dict = credentials_dict
        self.sheet_id = sheet_id
        self.market = market
        self.worksheet_name = f"Copy of Raw_XN_Q4_2025_{market}"

        self.client = None
        self.spreadsheet = None
        self.worksheet = None
    
    def _init_google_sheets(self):
        """Initialize Google Sheets connection"""
        try:
            if self.client is None:
                scopes = [
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive"
                ]
                creds = Credentials.from_service_account_info(
                    self.credentials_dict, scopes=scopes
                )
                self.client = gspread.authorize(creds)
                self.spreadsheet = self.client.open_by_key(self.sheet_id)
                
                try:
                    self.worksheet = self.spreadsheet.worksheet(self.worksheet_name)
                except gspread.exceptions.WorksheetNotFound:
                    self.worksheet = self.spreadsheet.add_worksheet(
                        title=self.worksheet_name,
                        rows="1000",
                        cols="30"
                    )
                    self.worksheet.update(values=[self.required_columns], range_name='A1')
                    
        except Exception as e:
            raise Exception(f"Error initializing Google Sheets: {e}")

    def safe_extract_asin_from_portfolio(self, portfolio_str):
        """Extract ASIN from Portfolio string"""
        if pd.isna(portfolio_str) or portfolio_str == '':
            return portfolio_str
        
        try:
            portfolio_str = str(portfolio_str).strip()
            
            # Pattern 1: B + 9 alphanumeric
            pattern1 = r'B[A-Z0-9]{9}'
            match1 = re.search(pattern1, portfolio_str.upper())
            if match1:
                return match1.group()
            
            # Pattern 2: Any 10 consecutive alphanumeric
            pattern2 = r'[A-Z0-9]{10}'
            match2 = re.search(pattern2, portfolio_str.upper())
            if match2:
                return match2.group()
            
            # Pattern 3: Extract first 10 alphanumeric
            clean_str = re.sub(r'[^A-Za-z0-9]', '', portfolio_str)
            if len(clean_str) >= 10:
                return clean_str[:10].upper()
            
            return portfolio_str
        except Exception as e:
            return portfolio_str

    def get_existing_sheet_data_count(self):
        """Get current number of rows in the sheet"""
        try:
            all_values = self.worksheet.col_values(1)
            data_rows = len([val for val in all_values if val.strip()]) - 1 if all_values else 0
            return data_rows
        except Exception as e:
            return 0
    
    def append_to_sheets(self, df):
        """Append DataFrame to Google Sheets"""
        if df.empty:
            return False
        
        try:
            self._init_google_sheets()
            existing_rows = self.get_existing_sheet_data_count()
            start_row = max(existing_rows + 2, 2)
            
            safe_df = df.copy()
            
            datetime_cols = safe_df.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns
            for col in datetime_cols:
                safe_df[col] = safe_df[col].apply(lambda x: f"{x.month}/{x.day}/{x.year}" if pd.notna(x) else "")
            
            safe_df = safe_df.fillna("")
            values_to_append = safe_df.values.tolist()
            
            needed_rows = start_row + len(values_to_append) - 1
            if needed_rows > self.worksheet.row_count:
                add_count = needed_rows - self.worksheet.row_count
                self.worksheet.add_rows(add_count)
            
            end_col_index = len(self.required_columns)
            end_col_letter = gspread.utils.rowcol_to_a1(1, end_col_index).split('1')[0].strip()
            end_row = start_row + len(df) - 1
            range_name = f"A{start_row}:{end_col_letter}{end_row}"
            
            self.worksheet.update(
                values=values_to_append, 
                range_name=range_name,
                value_input_option='USER_ENTERED'
            )
            
            return True
            
        except Exception as e:
            raise Exception(f"Error uploading to Google Sheets: {e}")


def load_credentials_from_file(uploaded_file):
    """Load Google Sheets credentials from uploaded JSON file"""
    try:
        credentials_dict = json.load(uploaded_file)
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        for field in required_fields:
            if field not in credentials_dict:
                st.error(f"❌ Missing required field: {field}")
                return None
        return credentials_dict
    except json.JSONDecodeError:
        st.error("❌ Invalid JSON file format")
        return None
    except Exception as e:
        st.error(f"❌ Error loading credentials: {e}")
        return None


def ppc_xnurta_page():
    """PPC XNurta data upload page"""
    
    # Step 1: Upload credentials
    st.subheader("🔐 Step 1: Upload Google Credentials")
    
    credentials_file = st.file_uploader(
        "Upload your credential.json file",
        type=['json'],
        key="ppc_credentials_uploader",
        help="Upload your Google Service Account credentials JSON file"
    )
    
    credentials_dict = None
    if credentials_file:
        credentials_dict = load_credentials_from_file(credentials_file)
        if credentials_dict:
            st.success("✅ Credentials loaded successfully!")
        else:
            st.error("❌ Failed to load credentials. Please check your JSON file.")
            return
    else:
        st.warning("⚠️ Please upload credential.json file to continue")
        return
    
    st.markdown("---")
    
    # Step 2: Enter Sheet ID
    st.subheader("📝 Step 2: Enter Google Sheet ID")
    
    sheet_id = st.text_input(
        "Google Sheet ID",
        value="1r6bWx_JlvEPn_YYszN8y6Wc8Q6Vm5FE-56aLHXhMSZk",
        help="Find this in your Google Sheet URL"
    )
    
    if not sheet_id:
        st.warning("⚠️ Please enter Google Sheet ID to continue")
        return
    
    st.markdown("---")
    
    # Step 3: Select Market
    st.subheader("🌍 Step 3: Select Market")
    
    if 'ppc_selected_market' not in st.session_state:
        st.session_state.ppc_selected_market = "US"
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🇺🇸 US Market", use_container_width=True, key="ppc_us",
                    type="primary" if st.session_state.ppc_selected_market == "US" else "secondary"):
            st.session_state.ppc_selected_market = "US"
    with col2:
        if st.button("🇨🇦 CA Market", use_container_width=True, key="ppc_ca",
                    type="primary" if st.session_state.ppc_selected_market == "CA" else "secondary"):
            st.session_state.ppc_selected_market = "CA"
    with col3:
        if st.button("🇬🇧 UK Market", use_container_width=True, key="ppc_uk",
                    type="primary" if st.session_state.ppc_selected_market == "UK" else "secondary"):
            st.session_state.ppc_selected_market = "UK"
    
    selected_market = st.session_state.ppc_selected_market
    st.info(f"📍 Selected Market: **{selected_market}**")
    
    st.markdown("---")
    
    # Step 4: Upload, Process & Export Data Files
    st.subheader("📂 Step 4: Upload, Process & Export Data")
    
    uploaded_files = st.file_uploader(
        "Upload Excel files (DD_MM_YYYY format in filename)",
        type=['xlsx', 'xls'],
        accept_multiple_files=True,
        key="ppc_uploader",
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
        
        if 'ppc_last_processed_files' not in st.session_state:
            st.session_state.ppc_last_processed_files = []
        
        if current_file_names != st.session_state.ppc_last_processed_files:
            with st.spinner("⚙️ Processing files..."):
                try:
                    processor = PPCProcessor(credentials_dict, sheet_id, selected_market)
                    result_df, processed_files = processor.process_files(uploaded_files)
                    
                    st.session_state.ppc_result_df = result_df
                    st.session_state.ppc_processor = processor
                    st.session_state.ppc_processed_files = processed_files
                    st.session_state.ppc_last_processed_files = current_file_names
                    
                    if not result_df.empty:
                        st.success("✅ Processing complete!")
                    else:
                        st.error("❌ No data found in uploaded files")
                        
                except Exception as e:
                    st.error(f"❌ Error processing files: {str(e)}")
                    for key in ['ppc_result_df', 'ppc_processor', 'ppc_processed_files', 'ppc_last_processed_files']:
                        if key in st.session_state:
                            del st.session_state[key]
        
        # Display processed data
        if 'ppc_result_df' in st.session_state and not st.session_state.ppc_result_df.empty:
            result_df = st.session_state.ppc_result_df
            processed_files = st.session_state.ppc_processed_files
            
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
                    key="ppc_preview_slider"
                )
            with col2:
                show_all = st.checkbox("All columns", value=False, key="ppc_show_all")
            
            display_df = result_df if show_all else (result_df.iloc[:, :8] if len(result_df.columns) > 8 else result_df)
            st.dataframe(display_df.head(preview_rows), use_container_width=True, height=300)
            
            if not show_all and len(result_df.columns) > 8:
                st.caption(f"Showing 8 of {len(result_df.columns)} columns. Enable 'All columns' to see more.")
            
            st.markdown("---")
            
            # Export section
            st.markdown("### 📤 Export Options")
            
            def export_to_excel(df, market):
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Data')
                output.seek(0)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                return output, f"PPC_XN_{market}_{timestamp}.xlsx"
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📥 Download Locally")
                
                excel_data, filename = export_to_excel(result_df, selected_market)
                st.download_button(
                    label="💾 Download Excel",
                    data=excel_data,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key="ppc_download_excel"
                )
                
                csv = result_df.to_csv(index=False).encode('utf-8')
                csv_filename = filename.replace('.xlsx', '.csv')
                st.download_button(
                    label="📄 Download CSV",
                    data=csv,
                    file_name=csv_filename,
                    mime="text/csv",
                    use_container_width=True,
                    key="ppc_download_csv"
                )
            
            with col2:
                st.markdown("#### ☁️ Upload to Cloud")
                st.info(f"**Target:** {selected_market} market sheet\n\n**Rows:** {len(result_df):,}")
                
                if st.button("🚀 Push to Google Sheets", 
                            type="primary", 
                            use_container_width=True,
                            key="ppc_push_to_sheets_btn"):
                    
                    try:
                        with st.spinner("Uploading to Google Sheets..."):
                            success = st.session_state.ppc_processor.append_to_sheets(result_df)
                        
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
            - Filename format: `SA_Campaign_List_YYYYMMDD_HHMMSS_*.xlsx`
            - Example: `SA_Campaign_List_20251015_143022_US.xlsx`
            """)
        
        with col2:
            st.markdown("""
            **⚡ What happens next:**
            1. Files are validated
            2. Data is automatically processed
            3. Preview & export options appear
            4. Choose download or upload to Sheets
            """)