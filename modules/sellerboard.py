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
import pytz
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

# Suppress warnings
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)

class SBProcessor:
    """Sellerboard Data Processor - Optimized Version"""
    
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
        """Initialize Google Sheets connection with caching"""
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
        """Standardize and select only required columns - Optimized"""
        df = df.copy()
        df.columns = [str(c).strip() for c in df.columns]
        
        # Pre-compute lowercase mappings for faster lookup
        std_col_map = {col.lower(): col for col in self.standard_columns}
        df_col_map = {col.lower(): col for col in df.columns}
        
        column_mapping = {}
        for std_col_lower, std_col in std_col_map.items():
            if std_col_lower in df_col_map:
                column_mapping[df_col_map[std_col_lower]] = std_col
            elif 'sponsored' in std_col_lower and 'ppc' in std_col_lower:
                for df_col_lower, df_col in df_col_map.items():
                    if 'sponsored' in df_col_lower and 'ppc' in df_col_lower:
                        column_mapping[df_col] = std_col
                        break
            elif 'refund' in std_col_lower and 'cost' in std_col_lower:
                for df_col_lower, df_col in df_col_map.items():
                    if 'refund' in df_col_lower and ('cost' in df_col_lower or 'сost' in df_col_lower):
                        column_mapping[df_col] = std_col
                        break
        
        df = df.rename(columns=column_mapping)
        available_columns = [col for col in self.standard_columns if col in df.columns]
        df_filtered = df[available_columns].copy()
        
        # Add missing columns efficiently
        for col in self.standard_columns:
            if col not in df_filtered.columns:
                df_filtered[col] = pd.NA
        
        return df_filtered[self.standard_columns]
    
    def process_single_excel(self, file_content, filename):
        """Process a single Excel file - Optimized with dtype inference"""
        try:
            # Read with optimized settings
            df = pd.read_excel(
                io.BytesIO(file_content),
                engine='openpyxl',
                # Use string dtype for text columns to avoid mixed type issues
            )
            
            # Drop empty columns in one go
            df = df.dropna(axis=1, how="all")
            
            date_val = self.extract_date_from_filename(filename)
            if date_val:
                df["Date"] = pd.to_datetime(date_val)
            
            df = self._standardize_columns(df)
            return df
        except Exception as e:
            st.error(f"⚠️ Error processing {filename}: {e}")
            return pd.DataFrame()
    
    def process_files(self, uploaded_files):
        """Process multiple uploaded files with parallel processing"""
        all_dataframes = []
        processed_files = []
        
        # Use ThreadPoolExecutor for parallel file processing
        with ThreadPoolExecutor(max_workers=min(4, len(uploaded_files))) as executor:
            future_to_file = {
                executor.submit(
                    self.process_single_excel, 
                    uploaded_file.read(), 
                    uploaded_file.name
                ): uploaded_file.name 
                for uploaded_file in uploaded_files
            }
            
            for future in as_completed(future_to_file):
                filename = future_to_file[future]
                try:
                    df = future.result()
                    if not df.empty:
                        all_dataframes.append(df)
                        processed_files.append(filename)
                except Exception as e:
                    st.error(f"⚠️ Error processing {filename}: {e}")
        
        if not all_dataframes:
            return pd.DataFrame(), []
        
        # Filter and validate dataframes efficiently
        valid_dataframes = []
        for df in all_dataframes:
            df_cleaned = df.dropna(axis=1, how="all")
            
            if not df_cleaned.empty and len(df_cleaned) > 0:
                # Ensure all standard columns exist
                for col in self.standard_columns:
                    if col not in df_cleaned.columns:
                        df_cleaned[col] = pd.NA
                
                valid_dataframes.append(df_cleaned[self.standard_columns])
        
        if not valid_dataframes:
            return pd.DataFrame(), []
        
        # Concatenate all dataframes at once
        merged_df = pd.concat(valid_dataframes, ignore_index=True, sort=False)
        
        # Sort efficiently
        if "Date" in merged_df.columns and "Sales" in merged_df.columns:
            merged_df = merged_df.sort_values(
                ["Date", "Sales"], 
                ascending=[True, False],
                ignore_index=True
            )
        elif "Date" in merged_df.columns:
            merged_df = merged_df.sort_values("Date", ignore_index=True)
        
        return merged_df, processed_files
    
    def get_existing_sheet_data_count(self):
        """Get current number of rows in the sheet - Optimized"""
        try:
            # Use get_all_values with specific range for faster fetch
            all_values = self.worksheet.col_values(1)
            data_rows = sum(1 for val in all_values if val and val.strip()) - 1
            return max(0, data_rows)
        except Exception as e:
            return 0
    
    def delete_data_from_date(self, from_date):
        """Delete all data from specified date onwards - Optimized with batch operations"""
        try:
            self._init_google_sheets()
            
            # Get all data in one batch request
            all_data = self.worksheet.get_all_values()
            
            if len(all_data) <= 1:
                return 0, "No data to delete"
            
            headers = all_data[0]
            data_rows = all_data[1:]
            
            # Find Date column index
            try:
                date_col_idx = headers.index('Date')
            except ValueError:
                return 0, "Date column not found in sheet"
            
            # Pre-compile date formats for faster parsing
            date_formats = ['%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d', '%m-%d-%Y']
            
            def parse_date_fast(date_str):
                """Fast date parsing with format caching"""
                if not date_str or not date_str.strip():
                    return None
                
                for fmt in date_formats:
                    try:
                        return datetime.strptime(date_str.strip(), fmt).date()
                    except:
                        continue
                return None
            
            # Filter rows efficiently using list comprehension
            rows_to_keep = []
            rows_deleted = 0
            
            for row in data_rows:
                if len(row) > date_col_idx:
                    row_date = parse_date_fast(row[date_col_idx])
                    if row_date and row_date >= from_date:
                        rows_deleted += 1
                        continue
                
                rows_to_keep.append(row)
            
            if rows_deleted > 0:
                # Batch clear and update in one operation
                data_to_write = [headers] + rows_to_keep
                
                # Clear and update in one API call
                self.worksheet.clear()
                if data_to_write:
                    # Use batch update for better performance
                    end_col = len(headers)
                    end_row = len(data_to_write)
                    range_name = f'A1:{gspread.utils.rowcol_to_a1(end_row, end_col)}'
                    
                    self.worksheet.update(
                        values=data_to_write, 
                        range_name=range_name,
                        value_input_option='USER_ENTERED'
                    )
                
                return rows_deleted, f"Successfully deleted {rows_deleted} rows from {from_date.strftime('%d/%m/%Y')} onwards"
            else:
                return 0, f"No data found from {from_date.strftime('%d/%m/%Y')} onwards"
                
        except Exception as e:
            raise Exception(f"Error deleting data: {str(e)}")
    
    def append_to_sheets(self, df, delete_from_date=None):
        """Append DataFrame to Google Sheets - Optimized with batch operations"""
        if df.empty:
            return False, "No data to upload"
            
        try:
            self._init_google_sheets()
            
            # Delete data if date is specified
            delete_info = ""
            if delete_from_date:
                rows_deleted, msg = self.delete_data_from_date(delete_from_date)
                delete_info = msg
            
            # Get current data count after deletion
            existing_rows = self.get_existing_sheet_data_count()
            start_row = max(existing_rows + 2, 2)
            end_row = start_row + len(df) - 1
            
            # Ensure enough rows exist
            total_needed_rows = end_row + 1
            current_rows = self.worksheet.row_count
            if total_needed_rows > current_rows:
                self.worksheet.add_rows(total_needed_rows - current_rows)
            
            # Prepare data efficiently using vectorized operations
            values_to_append = []
            
            # Convert DataFrame to list of lists efficiently
            for idx, row in df.iterrows():
                row_values = []
                for col in self.standard_columns:
                    val = row[col]
                    if pd.isna(val):
                        row_values.append("")
                    elif isinstance(val, (pd.Timestamp, datetime)):
                        row_values.append(f"{val.month}/{val.day}/{val.year}")
                    elif isinstance(val, (float, np.floating)):
                        # Handle float efficiently
                        row_values.append(float(val))
                    elif isinstance(val, (int, np.integer)):
                        row_values.append(int(val))
                    else:
                        row_values.append(str(val))
                values_to_append.append(row_values)
            
            # Calculate range
            end_col_index = len(self.standard_columns)
            end_col_letter = gspread.utils.rowcol_to_a1(1, end_col_index).split('1')[0]
            range_name = f"A{start_row}:{end_col_letter}{end_row}"
            
            # Use batch update with chunking for large datasets
            chunk_size = 5000  # Google Sheets API limit
            
            if len(values_to_append) <= chunk_size:
                # Single batch update
                self.worksheet.update(
                    values=values_to_append,
                    range_name=range_name,
                    value_input_option="USER_ENTERED"
                )
            else:
                # Chunked batch updates
                for i in range(0, len(values_to_append), chunk_size):
                    chunk = values_to_append[i:i + chunk_size]
                    chunk_start_row = start_row + i
                    chunk_end_row = chunk_start_row + len(chunk) - 1
                    chunk_range = f"A{chunk_start_row}:{end_col_letter}{chunk_end_row}"
                    
                    self.worksheet.update(
                        values=chunk,
                        range_name=chunk_range,
                        value_input_option="USER_ENTERED"
                    )
                    
                    # Small delay to avoid rate limiting
                    if i + chunk_size < len(values_to_append):
                        time.sleep(0.5)
            
            return True, delete_info
            
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
        value="1GpPsWt_fWCfHnEdFQJIsNBebhqFnIiExsHA8SjNUhFk",
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
                start_time = time.time()
                try:
                    processor = SBProcessor(credentials_dict, sheet_id, selected_market)
                    result_df, processed_files = processor.process_files(uploaded_files)
                    
                    processing_time = time.time() - start_time
                    
                    st.session_state.result_df = result_df
                    st.session_state.processor = processor
                    st.session_state.processed_files = processed_files
                    st.session_state.last_processed_files = current_file_names
                    
                    if not result_df.empty:
                        st.success(f"✅ Processing complete in {processing_time:.2f}s!")
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
                
                # Optional: Delete data from date
                with st.expander("🗑️ Optional: Delete Data from Date", expanded=False):
                    st.caption("⚠️ This will delete all existing data from the selected date onwards before uploading new data")
                    
                    enable_delete = st.checkbox(
                        "Enable data deletion",
                        value=False,
                        key="enable_delete_checkbox"
                    )
                    
                    delete_from_date = None
                    if enable_delete:
                        # Get min and max dates from uploaded data for reference
                        if 'Date' in result_df.columns:
                            result_df_temp = result_df.copy()
                            result_df_temp['Date'] = pd.to_datetime(result_df_temp['Date'])
                            min_date = result_df_temp['Date'].min().date()
                            max_date = result_df_temp['Date'].max().date()
                            
                            st.info(f"📅 Your uploaded data range: {min_date.strftime('%d/%m/%Y')} to {max_date.strftime('%d/%m/%Y')}")
                        
                        delete_from_date = st.date_input(
                            "Delete data from this date onwards:",
                            value=datetime.now().date(),
                            help="All data from this date onwards will be deleted before uploading new data",
                            key="delete_from_date_input"
                        )
                        
                        if delete_from_date:
                            st.warning(f"⚠️ Will delete all data from **{delete_from_date.strftime('%d/%m/%Y')}** onwards")
                
                # Push to Google Sheets button
                if st.button("🚀 Push to Google Sheets", 
                            type="primary", 
                            use_container_width=True,
                            key="push_to_sheets_btn"):
                    
                    try:
                        upload_start_time = time.time()
                        
                        with st.spinner("Uploading to Google Sheets..."):
                            success, info_msg = st.session_state.processor.append_to_sheets(
                                result_df, 
                                delete_from_date=delete_from_date if enable_delete else None
                            )
                        
                        upload_time = time.time() - upload_start_time
                        
                        if success:
                            st.success(f"✅ Successfully uploaded {len(result_df):,} rows in {upload_time:.2f}s!")
                            
                            with st.expander("📊 Upload Summary", expanded=True):
                                summary_text = f"""
                                - **Market:** {selected_market}
                                - **Rows uploaded:** {len(result_df):,}
                                - **Columns:** {len(result_df.columns)}
                                - **Files processed:** {len(processed_files)}
                                - **Upload time:** {upload_time:.2f}s
                                - **Timestamp:** {datetime.now(pytz.timezone('Asia/Ho_Chi_Minh')).strftime('%Y-%m-%d %H:%M:%S')}
                                """
                                
                                if info_msg:
                                    summary_text += f"\n- **Deletion:** {info_msg}"
                                
                                st.markdown(summary_text)
                        else:
                            st.error(f"❌ Upload failed: {info_msg}")
                            
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

# For testing
if __name__ == "__main__":
    st.set_page_config(page_title="Sellerboard Uploader", layout="wide")
    sellerboard_page()