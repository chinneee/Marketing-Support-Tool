import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json
import io
from datetime import datetime
import pytz
import traceback

class FBAInventoryProcessor:
    """FBA Inventory Data Processor"""
    
    def __init__(self, credentials_dict, sheet_id, market):
        self.credentials_dict = credentials_dict
        self.sheet_id = sheet_id
        self.market = market
        self.worksheet_name = f"FBA Stock_{market}"
        
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
                    
        except Exception as e:
            raise Exception(f"Error initializing Google Sheets: {e}")
    
    def process_single_file(self, file_content, filename):
        """Process a single file and return DataFrame"""
        try:
            # Try different file formats
            if filename.endswith('.xlsx') or filename.endswith('.xls'):
                df = pd.read_excel(io.BytesIO(file_content))
            elif filename.endswith('.csv'):
                # Try different encodings for CSV
                try:
                    df = pd.read_csv(io.BytesIO(file_content), encoding='utf-8')
                except:
                    try:
                        df = pd.read_csv(io.BytesIO(file_content), encoding='latin-1')
                    except:
                        df = pd.read_csv(io.BytesIO(file_content), encoding='iso-8859-1')
            elif filename.endswith('.txt'):
                # Try tab-separated first, then comma-separated
                try:
                    df = pd.read_csv(io.BytesIO(file_content), sep='\t', encoding='utf-8')
                except:
                    try:
                        df = pd.read_csv(io.BytesIO(file_content), sep=',', encoding='utf-8')
                    except:
                        df = pd.read_csv(io.BytesIO(file_content), sep='\t', encoding='latin-1')
            else:
                raise ValueError(f"Unsupported file format: {filename}")
            
            df = df.dropna(axis=1, how="all").copy()
            
            # Add Last Updated timestamp
            df["Last Updated"] = datetime.now(pytz.timezone('Asia/Ho_Chi_Minh')).strftime('%Y-%m-%d %H:%M:%S')
            
            return df
        except Exception as e:
            st.error(f"⚠️ Error processing {filename}: {e}")
            return pd.DataFrame()
    
    def clear_and_upload_to_sheets(self, df):
        """Clear existing data and upload new DataFrame to Google Sheets"""
        if df.empty:
            return False
            
        try:
            self._init_google_sheets()
            
            # Clear all data
            self.worksheet.clear()
            
            # Get column names from DataFrame
            columns = df.columns.tolist()
            
            # Update header
            self.worksheet.update(values=[columns], range_name='A1')
            
            # Prepare data
            values_to_append = []
            for _, row in df.iterrows():
                row_values = []
                for col in columns:
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
            
            # Upload data starting from row 2
            if values_to_append:
                end_row = len(values_to_append) + 1
                end_col_index = len(columns)
                end_col_letter = gspread.utils.rowcol_to_a1(1, end_col_index).split('1')[0].strip()
                range_name = f"A2:{end_col_letter}{end_row}"
                
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


def fba_inventory_page():
    """FBA Inventory data upload page"""
    
    
    # Step 1: Upload credentials
    st.subheader("🔐 Step 1: Upload Google Credentials")
    
    credentials_file = st.file_uploader(
        "Upload your credential.json file",
        type=['json'],
        key="fba_credentials_uploader",
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
    
    # Step 3: Upload FBA Inventory Files
    st.subheader("📂 Step 3: Upload FBA Inventory Files")
    
    # Initialize session state for uploaded files
    if 'fba_files' not in st.session_state:
        st.session_state.fba_files = {'US': None, 'CA': None, 'UK': None}
    if 'fba_processed_data' not in st.session_state:
        st.session_state.fba_processed_data = {'US': None, 'CA': None, 'UK': None}
    
    # Create three columns for three markets
    col1, col2, col3 = st.columns(3)
    
    markets = ['US', 'CA', 'UK']
    flags = ['🇺🇸', '🇨🇦', '🇬🇧']
    columns = [col1, col2, col3]
    
    # File uploaders for each market
    for market, flag, col in zip(markets, flags, columns):
        with col:
            st.markdown(f"### {flag} {market} Market")
            uploaded_file = st.file_uploader(
                f"FBA Inventory {market}",
                type=['xlsx', 'xls', 'csv', 'txt'],
                key=f"fba_uploader_{market}",
                help=f"Upload FBA Inventory file for {market} market (Excel, CSV, or Text)"
            )
            
            if uploaded_file:
                # Check if file changed
                if st.session_state.fba_files[market] != uploaded_file.name:
                    st.session_state.fba_files[market] = uploaded_file.name
                    
                    # Process file
                    with st.spinner(f"Processing {market}..."):
                        try:
                            processor = FBAInventoryProcessor(credentials_dict, sheet_id, market)
                            file_content = uploaded_file.read()
                            df = processor.process_single_file(file_content, uploaded_file.name)
                            
                            if not df.empty:
                                st.session_state.fba_processed_data[market] = {
                                    'df': df,
                                    'processor': processor,
                                    'filename': uploaded_file.name
                                }
                                st.success(f"✅ {len(df):,} rows")
                            else:
                                st.error("❌ No data found")
                                st.session_state.fba_processed_data[market] = None
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                            st.session_state.fba_processed_data[market] = None
                else:
                    # Display existing data info
                    if st.session_state.fba_processed_data[market]:
                        df = st.session_state.fba_processed_data[market]['df']
                        st.success(f"✅ {len(df):,} rows")
            else:
                st.session_state.fba_files[market] = None
                st.session_state.fba_processed_data[market] = None
                st.info("No file uploaded")
    
    st.markdown("---")
    
    # Display summary and preview
    uploaded_markets = [m for m in markets if st.session_state.fba_processed_data[m] is not None]
    
    if uploaded_markets:
        st.subheader("📊 Data Summary")
        
        # Summary metrics
        cols = st.columns(len(uploaded_markets))
        for i, market in enumerate(uploaded_markets):
            with cols[i]:
                data = st.session_state.fba_processed_data[market]
                df = data['df']
                
                flag = flags[markets.index(market)]
                st.markdown(f"### {flag} {market}")
                st.metric("Total SKUs", f"{len(df):,}")
                
                if 'Total Quantity' in df.columns:
                    total_qty = df['Total Quantity'].sum() if pd.notna(df['Total Quantity'].sum()) else 0
                    st.metric("Total Units", f"{int(total_qty):,}")
                
                if 'Available' in df.columns:
                    available = df['Available'].sum() if pd.notna(df['Available'].sum()) else 0
                    st.metric("Available", f"{int(available):,}")
        
        st.markdown("---")
        
        # Preview data
        st.subheader("👁️ Data Preview")
        
        preview_market = st.selectbox(
            "Select market to preview",
            uploaded_markets,
            format_func=lambda x: f"{flags[markets.index(x)]} {x} Market"
        )
        
        if preview_market:
            data = st.session_state.fba_processed_data[preview_market]
            df = data['df']
            
            col1, col2 = st.columns([2, 1])
            with col1:
                preview_rows = st.slider(
                    "Preview rows",
                    min_value=5,
                    max_value=min(50, len(df)),
                    value=10,
                    step=5,
                    key="fba_preview_slider"
                )
            with col2:
                show_all = st.checkbox("All columns", value=False, key="fba_show_all")
            
            display_df = df if show_all else (df.iloc[:, :8] if len(df.columns) > 8 else df)
            st.dataframe(display_df.head(preview_rows), use_container_width=True, height=300)
            
            if not show_all and len(df.columns) > 8:
                st.caption(f"Showing 8 of {len(df.columns)} columns. Enable 'All columns' to see more.")
        
        st.markdown("---")
        
        # Export Options
        st.subheader("📤 Export & Upload Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📥 Download Locally")
            
            download_market = st.selectbox(
                "Select market to download",
                uploaded_markets,
                format_func=lambda x: f"{flags[markets.index(x)]} {x} Market",
                key="download_market_select"
            )
            
            if download_market:
                data = st.session_state.fba_processed_data[download_market]
                df = data['df']
                
                # Excel download
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='FBA_Inventory')
                output.seek(0)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"FBA_Inventory_{download_market}_{timestamp}.xlsx"
                
                st.download_button(
                    label=f"💾 Download {download_market} Excel",
                    data=output,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                
                # CSV download
                csv = df.to_csv(index=False).encode('utf-8')
                csv_filename = filename.replace('.xlsx', '.csv')
                st.download_button(
                    label=f"📄 Download {download_market} CSV",
                    data=csv,
                    file_name=csv_filename,
                    mime="text/csv",
                    use_container_width=True
                )
        
        with col2:
            st.markdown("#### ☁️ Upload to Google Sheets")
            
            st.info(f"**Ready to upload:** {len(uploaded_markets)} market(s)\n\n" + 
                   "\n".join([f"• {flags[markets.index(m)]} {m}: {len(st.session_state.fba_processed_data[m]['df']):,} rows" 
                             for m in uploaded_markets]))
            
            if st.button("🚀 Push All to Google Sheets", 
                        type="primary", 
                        use_container_width=True,
                        key="push_fba_all_btn"):
                
                success_count = 0
                failed_markets = []
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, market in enumerate(uploaded_markets):
                    status_text.text(f"Uploading {market} market...")
                    
                    try:
                        data = st.session_state.fba_processed_data[market]
                        processor = data['processor']
                        df = data['df']
                        
                        success = processor.clear_and_upload_to_sheets(df)
                        
                        if success:
                            success_count += 1
                        else:
                            failed_markets.append(market)
                            
                    except Exception as e:
                        failed_markets.append(market)
                        st.error(f"❌ {market} failed: {str(e)}")
                    
                    progress_bar.progress((i + 1) / len(uploaded_markets))
                
                status_text.empty()
                progress_bar.empty()
                
                # Show results
                if success_count == len(uploaded_markets):
                    st.success(f"✅ Successfully uploaded all {success_count} market(s)!")
                elif success_count > 0:
                    st.warning(f"⚠️ Uploaded {success_count} of {len(uploaded_markets)} markets. Failed: {', '.join(failed_markets)}")
                else:
                    st.error(f"❌ All uploads failed")
                
                # Show summary
                with st.expander("📊 Upload Summary", expanded=True):
                    st.markdown(f"""
                    **Upload completed at:** {datetime.now(pytz.timezone('Asia/Ho_Chi_Minh')).strftime('%Y-%m-%d %H:%M:%S')}
                    
                    **Results:**
                    """)
                    for market in uploaded_markets:
                        if market not in failed_markets:
                            df = st.session_state.fba_processed_data[market]['df']
                            st.markdown(f"- ✅ {flags[markets.index(market)]} **{market}**: {len(df):,} rows uploaded to `FBA Stock_{market}`")
                        else:
                            st.markdown(f"- ❌ {flags[markets.index(market)]} **{market}**: Upload failed")
    
    else:
        st.info("👆 **Upload FBA Inventory files to get started**")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **📌 File Requirements:**
            - Format: `.xlsx`, `.xls`, `.csv`, or `.txt`
            - Must contain FBA inventory data
            - Standard Amazon FBA inventory report format
            - Text files can be tab or comma separated
            """)
        
        with col2:
            st.markdown("""
            **⚡ How it works:**
            1. Upload files for one or more markets
            2. Data is automatically validated
            3. Preview processed data
            4. Download locally or push to Google Sheets
            """)


# Main execution
if __name__ == "__main__":
    fba_inventory_page()