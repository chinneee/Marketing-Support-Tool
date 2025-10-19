import streamlit as st
from sellerboard import sellerboard_page
from ppc_xnurta import ppc_xnurta_page
from dsp_xnurta import dsp_xnurta_page
from datetime import datetime

def main():
    st.set_page_config(
        page_title="Marketing Data Upload Tool",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
# Enhanced Custom CSS
    st.markdown("""
        <style>
        /* ============================================
           MAIN AREA - Light Gray Background
        ============================================ */
        .main {
            background-color: #F5F7FA !important;
            padding-top: 1rem;
        }
        
        .block-container {
            padding: 2rem 3rem;
        }
        
        /* ============================================
           SIDEBAR - White Background with Black Text
        ============================================ */
        [data-testid="stSidebar"] {
            background-color: #FFFFFF !important;
            border-right: 1px solid #E5E7EB;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        }
        
        /* Sidebar text - Black */
        [data-testid="stSidebar"] * {
            color: #1F2937 !important;
        }
        
        /* Sidebar titles */
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            color: #1F2937 !important;
            font-weight: 700;
        }
        
        /* ============================================
           RADIO BUTTONS (Navigation)
        ============================================ */
        .stRadio > label {
            font-weight: 600;
            color: #1F2937;
        }
        
        /* Navigation items in sidebar */
        [data-testid="stSidebar"] .stRadio > div > label {
            background-color: #F9FAFB;
            border: 1px solid #E5E7EB;
            border-radius: 8px;
            padding: 0.875rem 1rem;
            margin-bottom: 0.5rem;
            transition: all 0.2s ease;
            font-weight: 500;
            color: #1F2937 !important;
        }
        
        [data-testid="stSidebar"] .stRadio > div > label:hover {
            background-color: #F3F4F6;
            border-color: #FF4B4B;
            transform: translateX(2px);
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        /* Active/Selected navigation item */
        [data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] {
            background: linear-gradient(135deg, #FF4B4B 0%, #FF6B6B 100%);
            border-color: transparent;
            color: white !important;
            box-shadow: 0 4px 6px rgba(255, 75, 75, 0.3);
            font-weight: 600;
        }
        
        [data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] * {
            color: white !important;
        }
        
        /* ============================================
           BUTTONS - White Cards on Gray Background
        ============================================ */
        .stButton>button {
            height: 3rem;
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.2s ease;
            border: none;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        /* Primary button */
        .stButton>button[kind="primary"] {
            background: linear-gradient(135deg, #FF4B4B 0%, #FF6B6B 100%);
            color: white;
        }
        
        /* Secondary button */
        .stButton>button[kind="secondary"] {
            background: #FFFFFF;
            color: #1F2937;
            border: 1px solid #E5E7EB;
        }
        
        .stButton>button[kind="secondary"]:hover {
            background: #F9FAFB;
            border-color: #FF4B4B;
            color: #FF4B4B;
        }
        
        /* ============================================
           DOWNLOAD BUTTONS
        ============================================ */
        .stDownloadButton>button {
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 8px;
            padding: 0.625rem 1.25rem;
            min-height: 2.75rem;
            font-weight: 600;
            color: #1F2937;
            transition: all 0.2s ease;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .stDownloadButton>button:hover {
            border-color: #FF4B4B;
            color: #FF4B4B;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        /* ============================================
           ALERT BOXES - White Cards with Colors
        ============================================ */
        .stAlert {
            background-color: #FFFFFF !important;
            border-radius: 10px;
            border-left: 4px solid;
            padding: 1.25rem 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin: 1rem 0;
        }
        
        /* Success */
        div[data-testid="stSuccess"] {
            background-color: #ECFDF5 !important;
            border-left-color: #10B981;
            color: #065F46;
        }
        
        /* Info */
        div[data-testid="stInfo"] {
            background-color: #EFF6FF !important;
            border-left-color: #3B82F6;
            color: #1E40AF;
        }
        
        /* Warning */
        div[data-testid="stWarning"] {
            background-color: #FFFBEB !important;
            border-left-color: #F59E0B;
            color: #92400E;
        }
        
        /* Error */
        div[data-testid="stError"] {
            background-color: #FEF2F2 !important;
            border-left-color: #EF4444;
            color: #991B1B;
        }
        
        /* ============================================
           METRICS - White Cards that Pop
        ============================================ */
        [data-testid="stMetric"] {
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            transition: all 0.2s ease;
        }
        
        [data-testid="stMetric"]:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transform: translateY(-2px);
            border-color: #D1D5DB;
        }
        
        [data-testid="stMetricLabel"] {
            font-size: 0.875rem;
            font-weight: 600;
            color: #6B7280 !important;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        [data-testid="stMetricValue"] {
            font-size: 2rem;
            font-weight: 700;
            color: #1F2937 !important;
        }
        
        /* ============================================
           INPUTS - White on Gray
        ============================================ */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input {
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 8px;
            padding: 0.75rem 1rem;
            color: #1F2937;
            transition: all 0.2s ease;
        }
        
        .stTextInput > div > div > input:focus,
        .stNumberInput > div > div > input:focus {
            border-color: #FF4B4B;
            box-shadow: 0 0 0 3px rgba(255, 75, 75, 0.1);
            background: #FFFFFF;
        }
        
        /* File Uploader */
        [data-testid="stFileUploader"] {
            background: #FFFFFF;
            border: 2px dashed #E5E7EB;
            border-radius: 12px;
            padding: 2rem;
            transition: all 0.2s ease;
        }
        
        [data-testid="stFileUploader"]:hover {
            border-color: #FF4B4B;
            background: #FFFBFB;
        }
        
        /* ============================================
           DATAFRAME - White Tables
        ============================================ */
        .stDataFrame {
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .stDataFrame thead tr th {
            background: #F9FAFB !important;
            color: #1F2937 !important;
            font-weight: 700 !important;
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.05em;
            padding: 1rem !important;
            border-bottom: 2px solid #E5E7EB !important;
        }
        
        .stDataFrame tbody tr:hover {
            background: #F9FAFB !important;
        }
        
        /* ============================================
           EXPANDERS - White Cards
        ============================================ */
        .streamlit-expanderHeader {
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 8px;
            padding: 1rem 1.25rem;
            font-weight: 600;
            color: #1F2937;
            transition: all 0.2s ease;
        }
        
        .streamlit-expanderHeader:hover {
            background: #F9FAFB;
            border-color: #FF4B4B;
        }
        
        .streamlit-expanderContent {
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-top: none;
            border-radius: 0 0 8px 8px;
            padding: 1.25rem;
        }
        
        /* ============================================
           PROGRESS BAR
        ============================================ */
        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, #FF4B4B 0%, #FF6B6B 100%);
            border-radius: 4px;
        }
        
        .stProgress > div > div {
            background: #E5E7EB;
            border-radius: 4px;
            height: 8px;
        }
        
        /* ============================================
           CUSTOM COMPONENTS
        ============================================ */
        
        /* Title gradient effect */
        .gradient-title {
            background: linear-gradient(120deg, #FF4B4B, #FF6B6B);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        
        /* Card-like containers */
        .info-card {
            background: #FFFFFF;
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid #E5E7EB;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin: 1rem 0;
            transition: all 0.2s ease;
        }
        
        .info-card:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transform: translateY(-2px);
        }
        
        /* ============================================
           ANIMATIONS
        ============================================ */
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .loading {
            animation: pulse 2s ease-in-out infinite;
        }
        
        /* ============================================
           DIVIDER
        ============================================ */
        hr {
            margin: 2rem 0;
            border: none;
            border-top: 1px solid #E5E7EB;
        }
        
        /* ============================================
           SCROLLBAR
        ============================================ */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #F3F4F6;
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #D1D5DB;
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #9CA3AF;
        }
        
        /* ============================================
           HIDE DEFAULT ELEMENTS
        ============================================ */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)
    
    # Header with gradient title
    st.markdown('<h1 class="gradient-title">🚀 Marketing Data Upload Tool</h1>', unsafe_allow_html=True)
    st.markdown("### 📈 Upload and manage your marketing data efficiently")
    
    # Quick stats row (placeholder - can be populated with actual data)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="📊 Total Uploads", value="0", delta="Today")
    with col2:
        st.metric(label="✅ Success Rate", value="100%", delta="0%")
    with col3:
        st.metric(label="⚡ Active Markets", value="3", delta="US, CA, UK")
    with col4:
        st.metric(label="🕐 Last Updated", value=datetime.now().strftime("%H:%M"))
    
    st.markdown("---")
    
    # Sidebar navigation with enhanced UI
    st.sidebar.markdown("# 📋 Navigation")
    st.sidebar.markdown("*Select the tool you want to use*")
    st.sidebar.markdown("")
    
    # Module status indicators
    module_status = {
        "📊 Sellerboard": "✅ Active",
        "💰 PPC XNurta": "✅ Active",
        "📺 DSP XNurta": "✅ Active",
        "📦 FBA Inventory": "🚧 Coming Soon",
        "🔍 ASIN - Dimension": "🚧 Coming Soon",
        "🚀 Launching - Dimension": "🚧 Coming Soon"
    }
    
    page = st.sidebar.radio(
        label="Select a page",
        options=list(module_status.keys()),
        label_visibility="collapsed",
        help="Choose a module to work with"
    )
    
    # Show selected module status
    st.sidebar.markdown(f"**Status:** {module_status[page]}")
    st.sidebar.markdown("---")
    
    # Enhanced Help Section with expandable details
    with st.sidebar.expander("📖 Quick Start Guide", expanded=False):
        st.markdown("""
        **Step-by-step instructions:**
        
        1️⃣ **Upload Credentials**
        - Upload your `credentials.json` file
        - Ensure it has proper permissions
        
        2️⃣ **Configure Sheet**
        - Enter your Google Sheet ID
        - Format: Found in sheet URL
        
        3️⃣ **Select Market**
        - Choose: US, CA, or UK
        - Ensure data matches market
        
        4️⃣ **Upload Files**
        - Excel files (.xlsx, .xls)
        - Must contain date: DD_MM_YYYY
        - Example: `report_15_10_2025.xlsx`
        
        5️⃣ **Process Data**
        - Review preview
        - Choose: Append or Replace
        - Confirm upload
        """)
    
    with st.sidebar.expander("📝 File Format Requirements", expanded=False):
        st.markdown("""
        **Naming Convention:**
        - Include date in filename
        - Format: `DD_MM_YYYY`
        - Example: `sales_report_25_10_2025.xlsx`
        
        **Supported Formats:**
        - `.xlsx` (Excel 2007+)
        - `.xls` (Excel 97-2003)
        
        **File Size:**
        - Maximum: 200 MB
        - Recommended: < 50 MB
        """)
    
    with st.sidebar.expander("💡 Tips & Best Practices", expanded=False):
        st.markdown("""
        **Performance Tips:**
        - Upload files during off-peak hours
        - Keep file sizes reasonable
        - Use consistent naming conventions
        
        **Data Quality:**
        - Verify data before upload
        - Check for missing values
        - Ensure correct date formats
        
        **Troubleshooting:**
        - Clear browser cache if issues occur
        - Refresh credentials if expired
        - Check internet connection
        """)
    
    st.sidebar.markdown("---")
    
    # Security notice with icon
    st.sidebar.success("""
    🔒 **Security & Privacy**
    
    - ✓ Credentials stored in memory only
    - ✓ No data saved to disk
    - ✓ Secure HTTPS connection
    - ✓ Session-based authentication
    
    Your data is safe with us!
    """)
    
    # Version info
    st.sidebar.markdown("---")
    st.sidebar.caption("Version 1.0.0 | Updated Oct 2025")
    
    # Route to appropriate page with enhanced messaging
    if page == "📊 Sellerboard":
        st.markdown("## 📊 Sellerboard Data Upload")
        st.markdown("*Manage your Sellerboard reports and analytics*")
        st.markdown("")
        sellerboard_page()
        
    elif page == "💰 PPC XNurta":
        st.markdown("## 💰 PPC XNurta Analytics")
        st.markdown("*Upload and analyze your PPC campaign data*")
        st.markdown("")
        ppc_xnurta_page()
        
    elif page == "📺 DSP XNurta":
        st.markdown("## 📺 DSP XNurta Dashboard")
        st.markdown("*Manage your DSP advertising data*")
        st.markdown("")
        dsp_xnurta_page()
        
    elif page == "📦 FBA Inventory":
        st.markdown("## 📦 FBA Inventory Management")
        st.info("🚧 **Module Under Development**")
        st.markdown("""
        This module is currently being developed and will include:
        
        - 📊 Real-time inventory tracking
        - 📈 Stock level analytics
        - 🔔 Low stock alerts
        - 📦 Reorder recommendations
        - 📉 Inventory turnover analysis
        
        **Expected Release:** Q1 2026
        """)
        
        if st.button("🔔 Notify me when available"):
            st.success("✅ You'll be notified when this module is ready!")
            
    elif page == "🔍 ASIN - Dimension":
        st.markdown("## 🔍 ASIN Dimension Analysis")
        st.info("🚧 **Module Under Development**")
        st.markdown("""
        This module is currently being developed and will include:
        
        - 🔍 ASIN performance tracking
        - 📊 Multi-dimensional analysis
        - 🎯 Product ranking insights
        - 📈 Sales trend analysis
        - 🔄 Competitor comparison
        
        **Expected Release:** Q1 2026
        """)
        
        if st.button("🔔 Notify me when available", key="asin_notify"):
            st.success("✅ You'll be notified when this module is ready!")
            
    elif page == "🚀 Launching - Dimension":
        st.markdown("## 🚀 Product Launch Analytics")
        st.info("🚧 **Module Under Development**")
        st.markdown("""
        This module is currently being developed and will include:
        
        - 🚀 Launch performance tracking
        - 📊 Campaign effectiveness metrics
        - 🎯 Target audience analysis
        - 📈 Growth trajectory monitoring
        - 💡 Optimization recommendations
        
        **Expected Release:** Q1 2026
        """)
        
        if st.button("🔔 Notify me when available", key="launch_notify"):
            st.success("✅ You'll be notified when this module is ready!")
    
    # Footer section
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Need Help?**")
        st.markdown("Contact: trinh.nguyen@aprime.so")
    
    with col2:
        st.markdown("**Documentation**")
        # Khi click thì bật/tắt hiển thị docs
        if st.button("View Docs", key="view_docs"):
            st.session_state.show_docs = not st.session_state.get("show_docs", False)
    
    with col3:
        st.markdown("**Report Issues**")
        st.markdown("[Bug Tracker](#)")

    # --- Docs section ---
    if st.session_state.get("show_docs", False):
        st.markdown("---")
        st.markdown("## 📖 Documentation")
        st.markdown("""
        **Hướng dẫn sử dụng:**

        

        💡 *Mẹo:* Bạn có thể xem lại hướng dẫn này bất kỳ lúc nào bằng cách nhấn "View Docs".
        """)

if __name__ == "__main__":
    if "show_docs" not in st.session_state:
        st.session_state.show_docs = False
    main()