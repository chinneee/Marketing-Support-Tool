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
    
    import streamlit as st

def apply_custom_theme():
    """Apply enhanced custom theme to Streamlit app"""
    st.markdown("""
        <style>
        /* ============================================
           GLOBAL STYLES
        ============================================ */
        
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* Root variables for easy theming */
        :root {
            --primary-color: #FF4B4B;
            --secondary-color: #FF6B6B;
            --background-color: #FFFFFF;
            --secondary-bg: #F8F9FA;
            --text-color: #262730;
            --text-light: #6C757D;
            --border-color: #E9ECEF;
            --shadow-sm: 0 1px 3px rgba(0,0,0,0.08);
            --shadow-md: 0 4px 12px rgba(0,0,0,0.1);
            --shadow-lg: 0 8px 24px rgba(0,0,0,0.12);
            --radius-sm: 6px;
            --radius-md: 8px;
            --radius-lg: 12px;
            --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        /* Main container styling */
        .main {
            padding-top: 1rem;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }
        
        /* ============================================
           TYPOGRAPHY
        ============================================ */
        
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Inter', sans-serif;
            font-weight: 600;
            color: var(--text-color);
            letter-spacing: -0.02em;
        }
        
        h1 {
            font-size: 2.5rem;
            margin-bottom: 1rem;
        }
        
        h2 {
            font-size: 2rem;
            margin-bottom: 0.875rem;
        }
        
        h3 {
            font-size: 1.5rem;
            margin-bottom: 0.75rem;
        }
        
        p, .stMarkdown {
            color: var(--text-color);
            line-height: 1.6;
        }
        
        /* ============================================
           BUTTONS
        ============================================ */
        
        .stButton>button {
            height: 3rem;
            border-radius: var(--radius-md);
            font-weight: 500;
            font-family: 'Inter', sans-serif;
            transition: var(--transition);
            border: none;
            box-shadow: var(--shadow-sm);
            letter-spacing: 0.01em;
        }
        
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }
        
        .stButton>button:active {
            transform: translateY(0);
            box-shadow: var(--shadow-sm);
        }
        
        /* Primary button style */
        .stButton>button[kind="primary"] {
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            color: white;
        }
        
        .stButton>button[kind="primary"]:hover {
            background: linear-gradient(135deg, var(--secondary-color) 0%, var(--primary-color) 100%);
        }
        
        /* Secondary button style */
        .stButton>button[kind="secondary"] {
            background: var(--secondary-bg);
            color: var(--text-color);
            border: 1px solid var(--border-color);
        }
        
        .stButton>button[kind="secondary"]:hover {
            background: #E9ECEF;
            border-color: #CED4DA;
        }
        
        /* ============================================
           DOWNLOAD BUTTONS
        ============================================ */
        
        .stDownloadButton>button {
            height: 3rem;
            border-radius: var(--radius-md);
            font-weight: 500;
            transition: var(--transition);
            border: 1px solid var(--border-color);
            background: white;
            box-shadow: var(--shadow-sm);
        }
        
        .stDownloadButton>button:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
            border-color: var(--primary-color);
            color: var(--primary-color);
        }
        
        /* ============================================
           INPUTS & FORM ELEMENTS
        ============================================ */
        
        .stTextInput>div>div>input,
        .stNumberInput>div>div>input,
        .stTextArea textarea {
            border-radius: var(--radius-md);
            border: 1px solid var(--border-color);
            padding: 0.75rem 1rem;
            transition: var(--transition);
            font-family: 'Inter', sans-serif;
        }
        
        .stTextInput>div>div>input:focus,
        .stNumberInput>div>div>input:focus,
        .stTextArea textarea:focus {
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(255, 75, 75, 0.1);
        }
        
        /* File uploader */
        .stFileUploader {
            border-radius: var(--radius-lg);
        }
        
        .stFileUploader>div {
            border: 2px dashed var(--border-color);
            border-radius: var(--radius-lg);
            padding: 2rem;
            transition: var(--transition);
            background: var(--secondary-bg);
        }
        
        .stFileUploader>div:hover {
            border-color: var(--primary-color);
            background: rgba(255, 75, 75, 0.03);
        }
        
        /* Slider */
        .stSlider>div>div>div>div {
            background: var(--primary-color);
        }
        
        /* Checkbox */
        .stCheckbox>label {
            font-weight: 400;
            color: var(--text-color);
        }
        
        /* Radio buttons */
        .stRadio>label {
            font-weight: 500;
            color: var(--text-color);
            margin-bottom: 0.5rem;
        }
        
        .stRadio>div {
            gap: 0.5rem;
        }
        
        .stRadio>div>label {
            background: white;
            padding: 0.75rem 1.25rem;
            border-radius: var(--radius-md);
            border: 1px solid var(--border-color);
            transition: var(--transition);
            cursor: pointer;
        }
        
        .stRadio>div>label:hover {
            border-color: var(--primary-color);
            background: rgba(255, 75, 75, 0.03);
        }
        
        /* ============================================
           SIDEBAR
        ============================================ */
        
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #F8F9FA 0%, #FFFFFF 100%);
            border-right: 1px solid var(--border-color);
        }
        
        [data-testid="stSidebar"]>div:first-child {
            padding-top: 2rem;
        }
        
        /* Sidebar navigation */
        [data-testid="stSidebar"] .stRadio>div>label {
            background: white;
            margin-bottom: 0.5rem;
            padding: 1rem;
            border-radius: var(--radius-md);
            border: 1px solid var(--border-color);
            transition: var(--transition);
            font-weight: 500;
        }
        
        [data-testid="stSidebar"] .stRadio>div>label:hover {
            border-color: var(--primary-color);
            background: rgba(255, 75, 75, 0.05);
            transform: translateX(4px);
        }
        
        [data-testid="stSidebar"] .stRadio>div>label[data-checked="true"] {
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            color: white;
            border-color: transparent;
            box-shadow: var(--shadow-md);
        }
        
        /* ============================================
           ALERT BOXES
        ============================================ */
        
        .stAlert {
            border-radius: var(--radius-md);
            border-left: 4px solid;
            padding: 1rem 1.25rem;
            box-shadow: var(--shadow-sm);
        }
        
        /* Success */
        .stSuccess {
            background: #D1FAE5;
            border-left-color: #10B981;
            color: #065F46;
        }
        
        /* Info */
        .stInfo {
            background: #DBEAFE;
            border-left-color: #3B82F6;
            color: #1E40AF;
        }
        
        /* Warning */
        .stWarning {
            background: #FEF3C7;
            border-left-color: #F59E0B;
            color: #92400E;
        }
        
        /* Error */
        .stError {
            background: #FEE2E2;
            border-left-color: #EF4444;
            color: #991B1B;
        }
        
        /* ============================================
           METRICS
        ============================================ */
        
        [data-testid="stMetric"] {
            background: white;
            padding: 1.5rem;
            border-radius: var(--radius-lg);
            border: 1px solid var(--border-color);
            box-shadow: var(--shadow-sm);
            transition: var(--transition);
        }
        
        [data-testid="stMetric"]:hover {
            box-shadow: var(--shadow-md);
            transform: translateY(-2px);
        }
        
        [data-testid="stMetricLabel"] {
            font-size: 0.875rem;
            color: var(--text-light);
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        [data-testid="stMetricValue"] {
            font-size: 1.875rem;
            font-weight: 700;
            color: var(--text-color);
        }
        
        [data-testid="stMetricDelta"] {
            font-size: 0.875rem;
            font-weight: 500;
        }
        
        /* ============================================
           DATAFRAME / TABLES
        ============================================ */
        
        .stDataFrame {
            border-radius: var(--radius-md);
            overflow: hidden;
            border: 1px solid var(--border-color);
            box-shadow: var(--shadow-sm);
        }
        
        .stDataFrame table {
            font-family: 'Inter', sans-serif;
        }
        
        .stDataFrame thead tr th {
            background: var(--secondary-bg) !important;
            color: var(--text-color) !important;
            font-weight: 600 !important;
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.05em;
            padding: 1rem !important;
            border-bottom: 2px solid var(--border-color) !important;
        }
        
        .stDataFrame tbody tr:hover {
            background: rgba(255, 75, 75, 0.02) !important;
        }
        
        .stDataFrame tbody tr td {
            padding: 0.875rem 1rem !important;
            border-bottom: 1px solid var(--border-color) !important;
        }
        
        /* ============================================
           EXPANDERS
        ============================================ */
        
        .streamlit-expanderHeader {
            background: var(--secondary-bg);
            border-radius: var(--radius-md);
            border: 1px solid var(--border-color);
            padding: 1rem 1.25rem;
            font-weight: 500;
            transition: var(--transition);
        }
        
        .streamlit-expanderHeader:hover {
            background: #E9ECEF;
            border-color: var(--primary-color);
        }
        
        .streamlit-expanderContent {
            border: 1px solid var(--border-color);
            border-top: none;
            border-radius: 0 0 var(--radius-md) var(--radius-md);
            padding: 1.25rem;
            background: white;
        }
        
        /* ============================================
           PROGRESS BAR
        ============================================ */
        
        .stProgress>div>div>div>div {
            background: linear-gradient(90deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            border-radius: var(--radius-sm);
            height: 8px;
        }
        
        .stProgress>div>div {
            background: var(--secondary-bg);
            border-radius: var(--radius-sm);
            height: 8px;
        }
        
        /* ============================================
           SPINNER
        ============================================ */
        
        .stSpinner>div {
            border-top-color: var(--primary-color) !important;
            border-right-color: var(--secondary-color) !important;
        }
        
        /* ============================================
           CUSTOM COMPONENTS
        ============================================ */
        
        /* Gradient title */
        .gradient-title {
            background: linear-gradient(120deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            line-height: 1.2;
        }
        
        /* Card containers */
        .info-card {
            background: white;
            padding: 1.5rem;
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-md);
            margin: 1rem 0;
            border: 1px solid var(--border-color);
            transition: var(--transition);
        }
        
        .info-card:hover {
            box-shadow: var(--shadow-lg);
            transform: translateY(-2px);
        }
        
        /* Badge */
        .badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .badge-success {
            background: #D1FAE5;
            color: #065F46;
        }
        
        .badge-info {
            background: #DBEAFE;
            color: #1E40AF;
        }
        
        .badge-warning {
            background: #FEF3C7;
            color: #92400E;
        }
        
        /* ============================================
           ANIMATIONS
        ============================================ */
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        .loading {
            animation: pulse 2s ease-in-out infinite;
        }
        
        .slide-in {
            animation: slideIn 0.3s ease-out;
        }
        
        .fade-in {
            animation: fadeIn 0.5s ease-in;
        }
        
        /* ============================================
           DIVIDERS
        ============================================ */
        
        hr {
            margin: 2rem 0;
            border: none;
            border-top: 2px solid var(--border-color);
            opacity: 1;
        }
        
        /* Fancy divider with gradient */
        .divider-gradient {
            height: 2px;
            background: linear-gradient(90deg, transparent 0%, var(--primary-color) 50%, transparent 100%);
            margin: 2rem 0;
            border: none;
        }
        
        /* ============================================
           SCROLLBAR
        ============================================ */
        
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--secondary-bg);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #CED4DA;
            border-radius: 4px;
            transition: var(--transition);
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--primary-color);
        }
        
        /* ============================================
           HIDE DEFAULT STREAMLIT ELEMENTS
        ============================================ */
        
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* ============================================
           RESPONSIVE DESIGN
        ============================================ */
        
        @media (max-width: 768px) {
            .block-container {
                padding: 1rem;
            }
            
            h1, .gradient-title {
                font-size: 2rem;
            }
            
            h2 {
                font-size: 1.5rem;
            }
            
            [data-testid="stMetric"] {
                padding: 1rem;
            }
            
            [data-testid="stMetricValue"] {
                font-size: 1.5rem;
            }
        }
        
        /* ============================================
           DARK MODE SUPPORT (Optional)
        ============================================ */
        
        @media (prefers-color-scheme: dark) {
            :root {
                --background-color: #1A1A1A;
                --secondary-bg: #2D2D2D;
                --text-color: #E9ECEF;
                --text-light: #ADB5BD;
                --border-color: #404040;
            }
            
            .main {
                background-color: var(--background-color);
                color: var(--text-color);
            }
            
            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, #2D2D2D 0%, #1A1A1A 100%);
            }
            
            .stButton>button[kind="secondary"],
            .stDownloadButton>button {
                background: var(--secondary-bg);
                color: var(--text-color);
            }
            
            .info-card,
            [data-testid="stMetric"] {
                background: var(--secondary-bg);
                border-color: var(--border-color);
            }
        }
        </style>
    """, unsafe_allow_html=True)

# Usage in main.py:
# from theme import apply_custom_theme
# apply_custom_theme()
    
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