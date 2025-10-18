import streamlit as st
import os
import re
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import io
import json
from typing import List, Tuple
import traceback

class SBProcessor:
    """Sellerboard Data Processor"""
    
    def __init__(self, credentials_dict, sheet_id, market):
        self.credentials_dict = credentials_dict
        # ❌ LỖI 1: Bạn đang hardcode sheet_id thay vì dùng parameter
        # self.sheet_id = "1rqH3SePVbpwcj1oD4Bqaa40IbkyKUi7aRBThlBdnEu4"
        # ✅ FIXED: Sử dụng parameter được truyền vào
        self.sheet_id = sheet_id
        self.market = market
        self.worksheet_name = f"Raw_SB_H2_2025_{market}"
        
        # Định nghĩa thứ tự cột chuẩn
        self.standard_columns = [
            'Product', 'ASIN', 'Date', 'SKU', 'Units', 'Refunds', 'Sales', 
            'Promo', 'Ads', 'Sponsored products (PPC)', '% Refunds', 
            'Refund сost', 'Amazon fees', 'Cost of Goods', 'Gross profit', 
            'Net profit', 'Estimated payout', 'Real ACOS', 'Sessions', 
            'VAT', 'Shipping'
        ]
        
        self.client = None
        self.spreadsheet = None
        self.worksheet = None
        
    def _init_google_sheets(self):
        """Initialize Google Sheets connection"""
        try:
            if self.client is None:
                st.info(f"🔄 Connecting to Google Sheets: {self.sheet_id}")
                st.info(f"📋 Looking for worksheet: {self.worksheet_name}")
                
                scopes = [
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive"
                ]
                creds = Credentials.from_service_account_info(
                    self.credentials_dict, scopes=scopes
                )
                self.client = gspread.authorize(creds)
                self.spreadsheet = self.client.open_by_key(self.sheet_id)
                
                # Try to get worksheet, if not exists, create it
                try:
                    self.worksheet = self.spreadsheet.worksheet(self.worksheet_name)
                    st.success(f"✅ Found worksheet: {self.worksheet_name}")
                except gspread.exceptions.WorksheetNotFound:
                    st.warning(f"⚠️ Worksheet '{self.worksheet_name}' not found. Creating new one...")
                    self.worksheet = self.spreadsheet.add_worksheet(
                        title=self.worksheet_name,
                        rows="1000",
                        cols="30"
                    )
                    # Add headers
                    self.worksheet.update('A1', [self.standard_columns])
                    st.success(f"✅ Created new worksheet: {self.worksheet_name}")
                    
        except Exception as e:
            st.error(f"❌ Error initializing Google Sheets: {e}")
            st.text(traceback.format_exc())
            raise
    
    def extract_date_from_filename(self, filename):
        """Extract first DD_MM_YYYY pattern from filename"""
        match = re.search(r"(\d{2}_\d{2}_\d{4})", filename)
        if match:
            return datetime.strptime(match.group(1), "%d_%m_%Y").date()
        return None
    
    def _standardize_columns(self, df):
        """Standardize and select only required columns"""
        df.columns = [str(c).strip() for c in df.columns]
        
        column_mapping = {}
        for std_col in self.standard_columns:
            std_col_lower = std_col.lower()
            for df_col in df.columns:
                df_col_lower = df_col.lower()
                if std_col_lower == df_col_lower:
                    column_mapping[df_col] = std_col
                    break
                elif 'sponsored' in std_col_lower and 'sponsored' in df_col_lower and 'ppc' in df_col_lower:
                    column_mapping[df_col] = std_col
                    break
                elif 'refund' in std_col_lower and 'cost' in std_col_lower and 'refund' in df_col_lower and ('cost' in df_col_lower or 'сost' in df_col_lower):
                    column_mapping[df_col] = std_col
                    break
        
        df = df.rename(columns=column_mapping)
        available_columns = [col for col in self.standard_columns if col in df.columns]
        df_filtered = df[available_columns].copy()
        
        # Thêm các cột thiếu
        for col in self.standard_columns:
            if col not in df_filtered.columns:
                df_filtered[col] = pd.NA
        
        # Sắp xếp đúng thứ tự chuẩn
        df_filtered = df_filtered[self.standard_columns]
        return df_filtered
    
    def process_single_excel(self, file_content, filename):
        """Process a single Excel file and return DataFrame with Date column"""
        try:
            df = pd.read_excel(io.BytesIO(file_content))
            df = df.dropna(axis=1, how="all")
            
            # Extract date from filename
            date_val = self.extract_date_from_filename(filename)
            if date_val:
                df["Date"] = pd.to_datetime(date_val)
            
            # Standardize columns
            df = self._standardize_columns(df)
            return df
        except Exception as e:
            st.error(f"⚠️ Error processing {filename}: {e}")
            return pd.DataFrame()
    
    def process_files(self, uploaded_files):
        """Process multiple uploaded files"""
        all_dataframes = []
        processed_files = []
        
        for uploaded_file in uploaded_files:
            file_content = uploaded_file.read()
            df = self.process_single_excel(file_content, uploaded_file.name)
            if not df.empty:
                all_dataframes.append(df)
                processed_files.append(uploaded_file.name)
        
        if all_dataframes:
            # ❌ LỖI 2: Indentation sai - phần code này nằm trong vòng lặp for
            # ✅ FIXED: Di chuyển ra ngoài vòng lặp
            valid_dataframes = []
            for df in all_dataframes:
                df_cleaned = df.dropna(axis=1, how="all")
                
                if not df_cleaned.empty:
                    for col in self.standard_columns:
                        if col not in df_cleaned.columns:
                            df_cleaned[col] = pd.NA
                    
                    df_cleaned = df_cleaned[self.standard_columns]
                    valid_dataframes.append(df_cleaned)
            
            if valid_dataframes:
                merged_df = pd.concat(valid_dataframes, ignore_index=True, sort=False)
                
                # Sort by Date then Sales
                if "Date" in merged_df.columns and "Sales" in merged_df.columns:
                    merged_df = merged_df.sort_values(
                        ["Date", "Sales"], ascending=[True, False]
                    )
                elif "Date" in merged_df.columns:
                    merged_df = merged_df.sort_values("Date")
                
                # Sắp xếp đúng thứ tự chuẩn
                merged_df = merged_df[self.standard_columns]
                
                return merged_df, processed_files
            else:
                st.warning("⚠️ All uploaded files are empty or invalid.")
                return pd.DataFrame(), []
        else:
            return pd.DataFrame(), []
    
    def get_existing_sheet_data_count(self):
        """Get current number of rows in the sheet"""
        try:
            all_values = self.worksheet.col_values(1)
            data_rows = len([val for val in all_values if val.strip()]) - 1 if all_values else 0
            st.info(f"📊 Existing rows in sheet: {data_rows}")
            return data_rows
        except Exception as e:
            st.error(f"⚠️ Error getting sheet data count: {e}")
            return 0
    
    def append_to_sheets(self, df):
        """Append DataFrame to Google Sheets"""
        if df.empty:
            st.warning("⚠️ No data to upload")
            return False
        
        try:
            st.info(f"📤 Starting upload of {len(df)} rows...")
            
            # Initialize connection
            self._init_google_sheets()
            
            existing_rows = self.get_existing_sheet_data_count()
            start_row = max(existing_rows + 2, 2)
            
            st.info(f"📍 Will upload to row {start_row}")
            
            values_to_append = []
            for _, row in df.iterrows():
                row_values = []
                for col in self.standard_columns:
                    val = row[col]
                    if pd.isna(val):
                        row_values.append("")
                    elif isinstance(val, (pd.Timestamp, datetime)):
                        row_values.append(val.strftime("%m/%d/%Y"))
                    elif isinstance(val, (float, int)):
                        row_values.append(str(val))
                    else:
                        row_values.append(str(val))
                values_to_append.append(row_values)
            
            # Safe range definition
            end_col_index = len(self.standard_columns)
            end_col_letter = gspread.utils.rowcol_to_a1(1, end_col_index).split('1')[0].strip()
            end_row = start_row + len(df) - 1
            range_name = f"A{start_row}:{end_col_letter}{end_row}"
            
            st.info(f"📊 Uploading to range: {range_name}")
            
            # Upload data
            self.worksheet.update(range_name, values_to_append)
            
            st.success(f"✅ Successfully uploaded {len(df)} rows!")
            return True
            
        except Exception as e:
            st.error(f"❌ Error uploading to Google Sheets: {e}")
            st.text("Full error trace:")
            st.text(traceback.format_exc())
            return False

def load_credentials_from_file(uploaded_file):
    """Load Google Sheets credentials from uploaded JSON file"""
    try:
        credentials_dict = json.load(uploaded_file)
        
        # Validate required fields
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

def sellerboard_page():
    """Sellerboard data upload page"""
    st.header("📊 Sellerboard Data Upload")
    
    # Step 1: Upload credentials
    st.subheader("🔐 Step 1: Upload Google Credentials")
    
    credentials_file = st.file_uploader(
        "Upload your credential.json file",
        type=['json'],
        key="credentials_uploader",
        help="Upload your Google Service Account credentials JSON file"
    )
    
    credentials_dict = None
    if credentials_file:
        credentials_dict = load_credentials_from_file(credentials_file)
        if credentials_dict:
            st.success("✅ Credentials loaded successfully!")
            with st.expander("📋 Credential Info"):
                st.write(f"**Project ID:** {credentials_dict.get('project_id', 'N/A')}")
                st.write(f"**Client Email:** {credentials_dict.get('client_email', 'N/A')}")
        else:
            st.error("❌ Failed to load credentials. Please check your JSON file.")
            return
    else:
        st.warning("⚠️ Please upload credential.json file to continue")
        st.info("💡 You need Google Service Account credentials to push data to Google Sheets")
        return
    
    st.markdown("---")
    
    # Step 2: Enter Sheet ID
    st.subheader("📝 Step 2: Enter Google Sheet ID")
    
    # ✅ FIXED: Thêm giá trị mặc định
    sheet_id = st.text_input(
        "Google Sheet ID",
        value="1rqH3SePVbpwcj1oD4Bqaa40IbkyKUi7aRBThlBdnEu4",  # Giá trị mặc định
        help="Find this in your Google Sheet URL: docs.google.com/spreadsheets/d/{SHEET_ID}/edit"
    )
    
    if not sheet_id:
        st.warning("⚠️ Please enter Google Sheet ID to continue")
        return
    
    st.markdown("---")
    
    # Step 3: Select Market
    st.subheader("🌍 Step 3: Select Market")
    
    # ✅ FIXED: Sử dụng session_state để lưu market đã chọn
    if 'selected_market' not in st.session_state:
        st.session_state.selected_market = "US"
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🇺🇸 US Market", use_container_width=True, 
                    type="primary" if st.session_state.selected_market == "US" else "secondary"):
            st.session_state.selected_market = "US"
    with col2:
        if st.button("🇨🇦 CA Market", use_container_width=True,
                    type="primary" if st.session_state.selected_market == "CA" else "secondary"):
            st.session_state.selected_market = "CA"
    with col3:
        if st.button("🇬🇧 UK Market", use_container_width=True,
                    type="primary" if st.session_state.selected_market == "UK" else "secondary"):
            st.session_state.selected_market = "UK"
    
    selected_market = st.session_state.selected_market
    st.info(f"📍 Selected Market: **{selected_market}**")
    
    st.markdown("---")
    
    # Step 4: Upload data files
    st.subheader("📂 Step 4: Upload Data Files")
    
    uploaded_files = st.file_uploader(
        "Upload Excel files (DD_MM_YYYY format in filename)",
        type=['xlsx'],
        accept_multiple_files=True,
        key="sb_uploader"
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} file(s) uploaded")
        
        with st.expander("📁 Uploaded Files"):
            for file in uploaded_files:
                st.text(f"• {file.name}")
        
        st.markdown("---")
        
        # Step 5: Process Files
        st.subheader("⚙️ Step 5: Process Files")
        if st.button("🔄 Process Files", type="primary", use_container_width=True):
            with st.spinner("Processing files..."):
                # ✅ FIXED: Truyền đúng sheet_id
                processor = SBProcessor(credentials_dict, sheet_id, selected_market)
                result_df, processed_files = processor.process_files(uploaded_files)
                
                # ✅ FIXED: Lưu vào session_state để dùng cho các button khác
                st.session_state.result_df = result_df
                st.session_state.processor = processor
                st.session_state.processed_files = processed_files
                
                if not result_df.empty:
                    st.success(f"✅ Successfully processed {len(processed_files)} files")
                    st.info(f"📊 Total rows: {len(result_df)}")
                    
                    with st.expander("👁️ Preview Data (First 10 rows)"):
                        st.dataframe(result_df.head(10), use_container_width=True)
                else:
                    st.error("❌ No data to process")
    
    # ✅ FIXED: Hiển thị action buttons nếu đã có data processed
    if 'result_df' in st.session_state and not st.session_state.result_df.empty:
        st.markdown("---")
        st.subheader("📤 Step 6: Select Action")
        st.caption("Choose how to export your processed data")
        
        def export_to_excel(df, market):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Data')
            output.seek(0)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return output, f"SB_{market}_{timestamp}.xlsx"
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            excel_data, filename = export_to_excel(st.session_state.result_df, selected_market)
            st.download_button(
                label="📥 Export to Excel",
                data=excel_data,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        with col2:
            if st.button("☁️ Push to Google Sheets", use_container_width=True, key="push_sheets_btn"):
                try:
                    with st.spinner("Uploading to Google Sheets..."):
                        success = st.session_state.processor.append_to_sheets(st.session_state.result_df)
                        if success:
                            st.success(f"✅ Uploaded {len(st.session_state.result_df)} rows to Google Sheets!")
                            st.balloons()
                        else:
                            st.error("❌ Upload failed - Check error messages above")
                except Exception as e:
                    st.error(f"❌ Upload failed: {str(e)}")
                    st.text(traceback.format_exc())
        
        with col3:
            if st.button("📤 Export Both", use_container_width=True, key="export_both_btn"):
                try:
                    excel_data, filename = export_to_excel(st.session_state.result_df, selected_market)
                    
                    with st.spinner("Uploading to Google Sheets..."):
                        success = st.session_state.processor.append_to_sheets(st.session_state.result_df)
                        if success:
                            st.success(f"✅ Uploaded {len(st.session_state.result_df)} rows to Google Sheets!")
                            st.download_button(
                                label="⬇️ Download Excel",
                                data=excel_data,
                                file_name=filename,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True,
                                key="download_after_both"
                            )
                            st.balloons()
                        else:
                            st.error("❌ Google Sheets upload failed")
                except Exception as e:
                    st.error(f"❌ Export failed: {str(e)}")
    else:
        st.info("📁 Please upload and process Excel files to continue")

def main():
    st.set_page_config(
        page_title="Marketing Data Upload Tool",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.markdown("""
        <style>
        .main {
            padding-top: 2rem;
        }
        .stButton>button {
            height: 3rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("🚀 Marketing Data Upload Tool")
    st.markdown("### Upload and manage your marketing data efficiently")
    st.markdown("---")
    
    st.sidebar.title("📋 Navigation")
    st.sidebar.markdown("Select the tool you want to use:")
    
    page = st.sidebar.radio(
        label="Select a page",
        options=[
            "📊 Sellerboard",
            "💰 PPC XNurta",
            "📺 DSP XNurta",
            "📦 FBA Inventory",
            "🔍 ASIN - Dimension",
            "🚀 Launching - Dimension"
        ],
        label_visibility="collapsed"
    )
    
    if page == "📊 Sellerboard":
        sellerboard_page()
    else:
        st.info(f"🚧 {page} module - Coming soon...")
        st.write("This module will be implemented next.")
    
    st.sidebar.markdown("---")
    st.sidebar.info(
        "📝 **How to use:**\n\n"
        "1. Upload credential.json file\n"
        "2. Enter Google Sheet ID\n"
        "3. Select market (US/CA/UK)\n"
        "4. Upload your Excel files\n"
        "5. Process and choose action\n\n"
        "💡 **File Format:**\n"
        "Files must have DD_MM_YYYY in filename\n"
        "Example: report_15_10_2025.xlsx"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.success(
        "🔒 **Security:**\n\n"
        "Your credentials are only stored\n"
        "in memory during the session\n"
        "and never saved to disk."
    )

if __name__ == "__main__":
    main()