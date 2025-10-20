import streamlit as st
import os
import sys
import re
import asyncio
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import io
import json
from typing import List, Tuple
import traceback
import warnings
import time

# Suppress warnings
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)

class SBProcessor:
    """Sellerboard Data Processor"""
    
    def __init__(self, credentials_dict, sheet_id, market):
        self.credentials_dict = credentials_dict
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
                except gspread.exceptions.WorksheetNotFound:
                    self.worksheet = self.spreadsheet.add_worksheet(
                        title=self.worksheet_name,
                        rows="1000",
                        cols="30"
                    )
                    self.worksheet.update(values=[self.standard_columns], range_name='A1')
                    
        except Exception as e:
            raise Exception(f"Error initializing Google Sheets: {e}")
    
    def extract_date_from_filename(self, filename):
        """Extract first DD_MM_YYYY pattern from filename"""
        match = re.search(r"(\d{2}_\d{2}_\d{4})", filename)
        if match:
            return datetime.strptime(match.group(1), "%d_%m_%Y").date()
        return None
    
    def _standardize_columns(self, df):
        """Standardize and select only required columns"""
        df = df.copy()
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
        
        for col in self.standard_columns:
            if col not in df_filtered.columns:
                df_filtered[col] = pd.NA
        
        df_filtered = df_filtered[self.standard_columns]
        return df_filtered
    
    def process_single_excel(self, file_content, filename):
        """Process a single Excel file and return DataFrame with Date column"""
        try:
            df = pd.read_excel(io.BytesIO(file_content))
            df = df.dropna(axis=1, how="all").copy()
            
            date_val = self.extract_date_from_filename(filename)
            if date_val:
                df["Date"] = pd.to_datetime(date_val)
            
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
            valid_dataframes = []
            for df in all_dataframes:
                df_cleaned = df.dropna(axis=1, how="all").copy()
                
                if not df_cleaned.empty:
                    for col in self.standard_columns:
                        if col not in df_cleaned.columns:
                            df_cleaned[col] = pd.NA
                    
                    df_cleaned = df_cleaned[self.standard_columns]
                    valid_dataframes.append(df_cleaned)
            
            if valid_dataframes:
                non_empty_dataframes = [df for df in valid_dataframes if not df.empty and len(df) > 0]
                
                if non_empty_dataframes:
                    merged_df = pd.concat(non_empty_dataframes, ignore_index=True, sort=False)
                    
                    if "Date" in merged_df.columns and "Sales" in merged_df.columns:
                        merged_df = merged_df.sort_values(
                            ["Date", "Sales"], ascending=[True, False]
                        )
                    elif "Date" in merged_df.columns:
                        merged_df = merged_df.sort_values("Date")
                    
                    merged_df = merged_df[self.standard_columns]
                    return merged_df, processed_files
                else:
                    return pd.DataFrame(), []
            else:
                return pd.DataFrame(), []
        else:
            return pd.DataFrame(), []
    
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
            end_row = start_row + len(df) - 1
            
            total_needed_rows = end_row + 1
            current_rows = self.worksheet.row_count
            if total_needed_rows > current_rows:
                self.worksheet.add_rows(total_needed_rows - current_rows)
            
            values_to_append = []
            for _, row in df.iterrows():
                row_values = []
                for col in self.standard_columns:
                    val = row[col]
                    if pd.isna(val):
                        row_values.append("")
                    elif isinstance(val, (pd.Timestamp, datetime)):
                        row_values.append(f"{val.month}/{val.day}/{val.year}")
                    elif isinstance(val, (float, int)):
                        row_values.append(val)
                    else:
                        row_values.append(str(val))
                values_to_append.append(row_values)
            
            end_col_index = len(self.standard_columns)
            end_col_letter = gspread.utils.rowcol_to_a1(1, end_col_index).split('1')[0].strip()
            range_name = f"A{start_row}:{end_col_letter}{end_row}"
            
            self.worksheet.update(
                values=values_to_append,
                range_name=range_name,
                value_input_option="USER_ENTERED"
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


def sellerboard_page():
    """Sellerboard data upload page"""
    
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
        value="1rqH3SePVbpwcj1oD4Bqaa40IbkyKUi7aRBThlBdnEu4",
        help="Find this in your Google Sheet URL: docs.google.com/spreadsheets/d/{SHEET_ID}/edit"
    )
    
    if not sheet_id:
        st.warning("⚠️ Please enter Google Sheet ID to continue")
        return
    
    st.markdown("---")
    
    # Step 3: Select Market
    st.subheader("🌍 Step 3: Select Market")
    
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
    
    # Step 4: Upload, Process & Export Data Files
    st.subheader("📂 Step 4: Upload, Process & Export Data")
    
    uploaded_files = st.file_uploader(
        "Upload Excel files (DD_MM_YYYY format in filename)",
        type=['xlsx'],
        accept_multiple_files=True,
        key="sb_uploader",
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
        
        if 'last_processed_files' not in st.session_state:
            st.session_state.last_processed_files = []
        
        if current_file_names != st.session_state.last_processed_files:
            with st.spinner("⚙️ Processing files..."):
                try:
                    processor = SBProcessor(credentials_dict, sheet_id, selected_market)
                    result_df, processed_files = processor.process_files(uploaded_files)
                    
                    st.session_state.result_df = result_df
                    st.session_state.processor = processor
                    st.session_state.processed_files = processed_files
                    st.session_state.last_processed_files = current_file_names
                    
                    if not result_df.empty:
                        st.success("✅ Processing complete!")
                    else:
                        st.error("❌ No data found in uploaded files")
                        
                except Exception as e:
                    st.error(f"❌ Error processing files: {str(e)}")
                    for key in ['result_df', 'processor', 'processed_files', 'last_processed_files']:
                        if key in st.session_state:
                            del st.session_state[key]
        
        # Display processed data
        if 'result_df' in st.session_state and not st.session_state.result_df.empty:
            result_df = st.session_state.result_df
            processed_files = st.session_state.processed_files
            
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
                    step=5
                )
            with col2:
                show_all = st.checkbox("All columns", value=False)
            
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
                return output, f"SB_{market}_{timestamp}.xlsx"
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📥 Download Locally")
                
                excel_data, filename = export_to_excel(result_df, selected_market)
                st.download_button(
                    label="💾 Download Excel",
                    data=excel_data,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                
                csv = result_df.to_csv(index=False).encode('utf-8')
                csv_filename = filename.replace('.xlsx', '.csv')
                st.download_button(
                    label="📄 Download CSV",
                    data=csv,
                    file_name=csv_filename,
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col2:
                st.markdown("#### ☁️ Upload to Cloud")
                st.info(f"**Target:** {selected_market} market sheet\n\n**Rows:** {len(result_df):,}")
                
                # ✅ KEY FIX: Use unique key for button to prevent state conflicts
                if st.button("🚀 Push to Google Sheets", 
                            type="primary", 
                            use_container_width=True,
                            key="push_to_sheets_btn"):
                    
                    try:
                        with st.spinner("Uploading to Google Sheets..."):
                            success = st.session_state.processor.append_to_sheets(result_df)
                        
                        if success:
                            st.success(f"✅ Successfully uploaded {len(result_df):,} rows!")
                            
                            with st.expander("📊 Upload Summary", expanded=True):
                                st.markdown(f"""
                                - **Market:** {selected_market}
                                - **Rows uploaded:** {len(result_df):,}
                                - **Columns:** {len(result_df.columns)}
                                - **Files processed:** {len(processed_files)}
                                - **Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
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