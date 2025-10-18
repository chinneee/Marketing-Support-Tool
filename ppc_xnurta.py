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

# Suppress warnings
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)

class PPCProcessor:
    """PPC XNurta Data Processor"""
    
    def __init__(self, credentials_dict, sheet_id, market):
        self.credentials_dict = credentials_dict
        self.sheet_id = "1rqH3SePVbpwcj1oD4Bqaa40IbkyKUi7aRBThlBdnEu4"
        self.market = market
        self.worksheet_name = f"Raw_XN_Q4_2025_{market}"
        
        # Define standard columns (from your original code)
        self.required_columns = [
            'ASIN', 'Date', 'Campaign type', 'Campaign', 'Status', 'Country', 'Portfolio',
            'Daily Budget', 'Bidding Strategy', 'Top-of-search IS', 'Avg.time in Budget',
            'Impressions', 'Clicks', 'CTR', 'Spend', 'CPC', 'Orders', 'Sales', 'Units', 'CVR'
        ]
        
        # Columns to drop
        self.columns_to_drop = [
            'Profile', 'Labels', 'Budget group', 'ACOS', 'ROAS', 'CPA', 
            'Sales Same SKU', 'Sales Other SKU', 'Orders Same SKU', 'Orders Other SKU', 
            'Units Same SKU', 'Units Other SKU', 'Target type', 'Current Budget', 
            'SP Off-site Ads Strategy'
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
                    self.worksheet.update(values=[self.required_columns], range_name='A1')
                    st.success(f"✅ Created new worksheet: {self.worksheet_name}")
                    
        except Exception as e:
            st.error(f"❌ Error initializing Google Sheets: {e}")
            st.text(traceback.format_exc())
            raise
    
    def extract_date_from_filename(self, filename):
        """Extract date from filename with multiple patterns"""
        patterns = [
            r'SA_Campaign_List_(\d{8})_\d{8}_.*\.xlsx',
            r'(\d{8})',
            r'(\d{2}_\d{2}_\d{4})',
            r'(\d{4}-\d{2}-\d{2})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                date_str = match.group(1)
                try:
                    if '_' in date_str:
                        return pd.to_datetime(date_str, format='%d_%m_%Y')
                    elif '-' in date_str:
                        return pd.to_datetime(date_str, format='%Y-%m-%d')
                    else:
                        return pd.to_datetime(date_str, format='%Y%m%d')
                except:
                    continue
        
        # Fallback: use current date
        return pd.to_datetime(datetime.now().date())
    
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
    
    def safe_normalize_campaign_types(self, text):
        """Normalize campaign type keywords"""
        if pd.isna(text) or text == '':
            return text
        
        try:
            text = str(text)
            normalizations = {
                'sponsoredBrands': 'SB',
                'sponsoredDisplay': 'SD', 
                'sponsoredProducts': 'SP',
                'sponsoredbrands': 'SB',
                'sponsoreddisplay': 'SD',
                'sponsoredproducts': 'SP',
                'Sponsored Brands': 'SB',
                'Sponsored Display': 'SD',
                'Sponsored Products': 'SP'
            }
            
            for original, normalized in normalizations.items():
                text = text.replace(original, normalized)
            
            return text
        except Exception as e:
            return text
    
    def safe_clean_currency_column(self, column):
        """Remove $ symbol and convert to float"""
        if column.dtype == 'object':
            try:
                cleaned = column.astype(str).str.replace(r'[C$,]', '', regex=True)
                cleaned = cleaned.replace(['', 'nan', 'NaN', '--', 'N/A'], np.nan)
                result = pd.to_numeric(cleaned, errors='coerce')
                return result
            except:
                return column
        return column
    
    def safe_convert_to_float(self, column):
        """Convert to float"""
        if column.dtype == 'object':
            try:
                cleaned = column.astype(str).str.replace(r'[%,]', '', regex=True)
                cleaned = cleaned.replace(['', 'nan', 'NaN', '--', 'N/A'], np.nan)
                result = pd.to_numeric(cleaned, errors='coerce')
                return result
            except:
                return column
        return column
    
    def safe_convert_to_int(self, column):
        """Convert to int"""
        if column.dtype == 'object':
            try:
                cleaned = column.astype(str).str.replace(r'[,]', '', regex=True)
                cleaned = cleaned.replace(['', 'nan', 'NaN', '--', 'N/A'], np.nan)
                float_col = pd.to_numeric(cleaned, errors='coerce')
                return float_col.astype('Int64')
            except:
                return column
        return column
    
    def process_single_excel(self, file_content, filename):
        """Process a single Excel file"""
        try:
            df = pd.read_excel(io.BytesIO(file_content))
            df = df.dropna(axis=0, how='all').dropna(axis=1, how='all').copy()
            
            # Clean column names
            df.columns = [str(col).strip() for col in df.columns]
            
            # Extract date
            date_extracted = self.extract_date_from_filename(filename)
            
            # Drop unwanted columns
            existing_columns_to_drop = [col for col in self.columns_to_drop if col in df.columns]
            if existing_columns_to_drop:
                df = df.drop(columns=existing_columns_to_drop)
            
            # Create ASIN column
            if 'Portfolio' in df.columns:
                asin_values = df['Portfolio'].apply(self.safe_extract_asin_from_portfolio)
            else:
                asin_values = [None] * len(df)
            
            # Normalize campaign types
            if 'Campaign type' in df.columns:
                df['Campaign type'] = df['Campaign type'].apply(self.safe_normalize_campaign_types)
            
            # Clean currency columns
            currency_columns = ['Daily Budget', 'Spend', 'Sales']
            for col in currency_columns:
                if col in df.columns:
                    df[col] = self.safe_clean_currency_column(df[col])
            
            # Convert float columns
            float_columns = ['Avg.time in Budget', 'Top-of-search IS', 'CPC', 'CVR', 'CTR']
            for col in float_columns:
                if col in df.columns:
                    df[col] = self.safe_convert_to_float(df[col])
            
            # Convert int columns
            int_columns = ['Impressions', 'Clicks', 'Orders', 'Units']
            for col in int_columns:
                if col in df.columns:
                    df[col] = self.safe_convert_to_int(df[col])
            
            # Create ordered DataFrame
            ordered_df = pd.DataFrame()
            ordered_df['ASIN'] = asin_values
            ordered_df['Date'] = [date_extracted] * len(df)
            
            # Add required columns
            for col in self.required_columns[2:]:
                if col in df.columns:
                    ordered_df[col] = df[col]
                else:
                    ordered_df[col] = np.nan
            
            return ordered_df
            
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
            non_empty_dataframes = [df for df in all_dataframes if not df.empty and len(df) > 0]
            
            if non_empty_dataframes:
                merged_df = pd.concat(non_empty_dataframes, ignore_index=True, sort=False)
                
                # Remove duplicates
                if 'ASIN' in merged_df.columns and 'Campaign' in merged_df.columns and 'Date' in merged_df.columns:
                    original_rows = len(merged_df)
                    merged_df = merged_df.drop_duplicates(subset=['ASIN', 'Date', 'Campaign'], keep='last')
                    removed = original_rows - len(merged_df)
                    if removed > 0:
                        st.info(f"🔄 Removed {removed} duplicate rows")
                
                # Sort by Date and Sales
                try:
                    if 'Date' in merged_df.columns and 'Sales' in merged_df.columns:
                        merged_df = merged_df.sort_values(['Date', 'Sales'], ascending=[True, False])
                    elif 'Date' in merged_df.columns:
                        merged_df = merged_df.sort_values('Date')
                except:
                    pass
                
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
            
            self._init_google_sheets()
            existing_rows = self.get_existing_sheet_data_count()
            start_row = max(existing_rows + 2, 2)
            
            st.info(f"📍 Will upload to row {start_row}")
            
            # Prepare values
            safe_df = df.copy()
            
            # Format datetime columns
            datetime_cols = safe_df.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns
            for col in datetime_cols:
                safe_df[col] = safe_df[col].apply(lambda x: f"{x.month}/{x.day}/{x.year}" if pd.notna(x) else "")
            
            # Replace NaN with empty string
            safe_df = safe_df.fillna("")
            
            # Convert to list of lists
            values_to_append = safe_df.values.tolist()
            
            # Ensure sheet has enough rows
            needed_rows = start_row + len(values_to_append) - 1
            if needed_rows > self.worksheet.row_count:
                add_count = needed_rows - self.worksheet.row_count
                st.info(f"📈 Adding {add_count} new rows to sheet...")
                self.worksheet.add_rows(add_count)
            
            # Calculate range
            end_col_index = len(self.required_columns)
            end_col_letter = gspread.utils.rowcol_to_a1(1, end_col_index).split('1')[0].strip()
            end_row = start_row + len(df) - 1
            range_name = f"A{start_row}:{end_col_letter}{end_row}"
            
            st.info(f"📊 Uploading to range: {range_name}")
            
            # Upload with USER_ENTERED to auto-detect data types
            self.worksheet.update(
                values=values_to_append, 
                range_name=range_name,
                value_input_option='USER_ENTERED'
            )
            
            st.success(f"✅ Successfully uploaded {len(df)} rows!")
            return True
            
        except Exception as e:
            st.error(f"❌ Error uploading to Google Sheets: {e}")
            st.text(traceback.format_exc())
            return False

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
    st.header("💰 PPC XNurta Data Upload")
    
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
    
    sheet_id = st.text_input(
        "Google Sheet ID",
        value="1lZ4dsi94HaeWshsEizKTyNHeOOG0tpLJhzL9pMxvd6k",
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
        if st.button("🇺🇸 US Market", width="stretch", key="ppc_us",
                    type="primary" if st.session_state.ppc_selected_market == "US" else "secondary"):
            st.session_state.ppc_selected_market = "US"
    with col2:
        if st.button("🇨🇦 CA Market", width="stretch", key="ppc_ca",
                    type="primary" if st.session_state.ppc_selected_market == "CA" else "secondary"):
            st.session_state.ppc_selected_market = "CA"
    with col3:
        if st.button("🇬🇧 UK Market", width="stretch", key="ppc_uk",
                    type="primary" if st.session_state.ppc_selected_market == "UK" else "secondary"):
            st.session_state.ppc_selected_market = "UK"
    
    selected_market = st.session_state.ppc_selected_market
    st.info(f"📍 Selected Market: **{selected_market}**")
    
    st.markdown("---")
    
    # Step 4: Upload data files
    st.subheader("📂 Step 4: Upload PPC Data Files")
    
    uploaded_files = st.file_uploader(
        "Upload Excel files (SA_Campaign_List format)",
        type=['xlsx'],
        accept_multiple_files=True,
        key="ppc_uploader"
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} file(s) uploaded")
        
        with st.expander("📁 Uploaded Files"):
            for file in uploaded_files:
                st.text(f"• {file.name}")
        
        st.markdown("---")
        
        # Step 5: Process Files
        st.subheader("⚙️ Step 5: Process Files")
        if st.button("🔄 Process Files", type="primary", width="stretch", key="ppc_process"):
            with st.spinner("Processing PPC files..."):
                processor = PPCProcessor(credentials_dict, sheet_id, selected_market)
                result_df, processed_files = processor.process_files(uploaded_files)
                
                st.session_state.ppc_result_df = result_df
                st.session_state.ppc_processor = processor
                st.session_state.ppc_processed_files = processed_files
                
                if not result_df.empty:
                    st.success(f"✅ Successfully processed {len(processed_files)} files")
                    st.info(f"📊 Total rows: {len(result_df)}")
                    
                    # Show statistics
                    if 'ASIN' in result_df.columns:
                        unique_asins = result_df['ASIN'].nunique()
                        st.info(f"🔖 Unique ASINs: {unique_asins}")
                    
                    if 'Date' in result_df.columns:
                        date_min = result_df['Date'].min()
                        date_max = result_df['Date'].max()
                        st.info(f"📅 Date range: {date_min.date()} to {date_max.date()}")
                    
                    with st.expander("👁️ Preview Data (First 10 rows)"):
                        st.dataframe(result_df.head(10), use_container_width=True)
                else:
                    st.error("❌ No data to process")
    
    # Step 6: Action buttons
    if 'ppc_result_df' in st.session_state and not st.session_state.ppc_result_df.empty:
        st.markdown("---")
        st.subheader("📤 Step 6: Select Action")
        st.caption("Choose how to export your processed data")
        
        def export_to_excel(df, market):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='PPC_Data')
            output.seek(0)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return output, f"PPC_{market}_{timestamp}.xlsx"
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            excel_data, filename = export_to_excel(st.session_state.ppc_result_df, selected_market)
            st.download_button(
                label="📥 Export to Excel",
                data=excel_data,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="stretch"
            )
        
        with col2:
            if st.button("☁️ Push to Google Sheets", width="stretch", key="ppc_push"):
                try:
                    with st.spinner("Uploading to Google Sheets..."):
                        success = st.session_state.ppc_processor.append_to_sheets(st.session_state.ppc_result_df)
                        if success:
                            st.success(f"✅ Uploaded {len(st.session_state.ppc_result_df)} rows!")
                            st.balloons()
                        else:
                            st.error("❌ Upload failed - Check error messages above")
                except Exception as e:
                    st.error(f"❌ Upload failed: {str(e)}")
                    st.text(traceback.format_exc())
        
        with col3:
            if st.button("📤 Export Both", width="stretch", key="ppc_both"):
                try:
                    excel_data, filename = export_to_excel(st.session_state.ppc_result_df, selected_market)
                    
                    with st.spinner("Uploading to Google Sheets..."):
                        success = st.session_state.ppc_processor.append_to_sheets(st.session_state.ppc_result_df)
                        if success:
                            st.success(f"✅ Uploaded {len(st.session_state.ppc_result_df)} rows!")
                            st.download_button(
                                label="⬇️ Download Excel",
                                data=excel_data,
                                file_name=filename,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                width="stretch",
                                key="ppc_download_after_both"
                            )
                            st.balloons()
                        else:
                            st.error("❌ Google Sheets upload failed")
                except Exception as e:
                    st.error(f"❌ Export failed: {str(e)}")
    else:
        st.info("📁 Please upload and process PPC files to continue")