import streamlit as st
from modules.sellerboard import sellerboard_page
from modules.ppc_xnurta import ppc_xnurta_page
from modules.dsp_xnurta import dsp_xnurta_page
from datetime import datetime

# ============================================================
# METRICS INITIALIZATION & CALCULATION FUNCTIONS
# ============================================================

def initialize_metrics():
    """Initialize all metrics in session state"""
    if 'total_uploads' not in st.session_state:
        st.session_state.total_uploads = 0
    if 'successful_uploads' not in st.session_state:
        st.session_state.successful_uploads = 0
    if 'failed_uploads' not in st.session_state:
        st.session_state.failed_uploads = 0
    if 'today_uploads' not in st.session_state:
        st.session_state.today_uploads = 0
    if 'last_upload_date' not in st.session_state:
        st.session_state.last_upload_date = datetime.now().date()
    if 'active_markets' not in st.session_state:
        st.session_state.active_markets = set()
    if 'last_updated' not in st.session_state:
        st.session_state.last_updated = datetime.now()

def get_success_rate():
    """Calculate success rate percentage"""
    if st.session_state.total_uploads == 0:
        return 100.0
    return round((st.session_state.successful_uploads / st.session_state.total_uploads) * 100, 1)

def get_success_rate_delta():
    """Calculate success rate change from previous upload"""
    if st.session_state.total_uploads <= 1:
        return 0
    
    # Calculate previous success rate
    prev_total = st.session_state.total_uploads - 1
    if prev_total == 0:
        return 0
    
    # Determine if last upload was successful
    last_was_success = st.session_state.successful_uploads > 0
    prev_success = st.session_state.successful_uploads - (1 if last_was_success else 0)
    
    prev_rate = round((prev_success / prev_total) * 100, 1) if prev_total > 0 else 0
    current_rate = get_success_rate()
    
    return round(current_rate - prev_rate, 1)

# ============================================================
# MAIN APPLICATION
# ============================================================

def main():
    st.set_page_config(
        page_title="Marketing Data Upload Tool",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # ✅ Initialize metrics FIRST - before any rendering
    initialize_metrics()
    
    # Enhanced Custom CSS
    st.markdown("""
        <style>
        /* Main container styling */
        .main {
            padding-top: 1rem;
        }
        
        /* Button improvements */
        .stButton>button {
            height: 3rem;
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.3s ease;
            border: none;
        }
        
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        /* Radio button styling */
        .stRadio > label {
            font-weight: 500;
            color: #262730;
        }
        
        /* Sidebar improvements */
        [data-testid="stSidebar"] {
            background-color: #F5F5F0;
        }
        
        /* Info/Success/Warning boxes */
        .stAlert {
            border-radius: 8px;
            border-left: 4px solid;
        }
        
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
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin: 1rem 0;
        }
        
        /* Animated loading */
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .loading {
            animation: pulse 2s ease-in-out infinite;
        }
        
        /* Hide default streamlit elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Divider styling */
        hr {
            margin: 2rem 0;
            border: none;
            border-top: 2px solid #f0f2f6;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Header with gradient title
    st.markdown('<h1 class="gradient-title">🚀 Marketing Data Upload Tool</h1>', unsafe_allow_html=True)
    
    # ============================================================
    # REAL-TIME METRICS DASHBOARD
    # ============================================================
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📊 Total Uploads", 
            value=f"{st.session_state.total_uploads}",
            delta=f"+{st.session_state.today_uploads} Today" if st.session_state.today_uploads > 0 else "No uploads today"
        )
    
    with col2:
        success_rate = get_success_rate()
        delta = get_success_rate_delta()
        st.metric(
            label="✅ Success Rate", 
            value=f"{success_rate}%",
            delta=f"{delta:+.1f}%" if delta != 0 else "No change",
            delta_color="normal" if delta >= 0 else "inverse"
        )
    
    with col3:
        markets_list = sorted(list(st.session_state.active_markets))
        markets_str = ", ".join(markets_list) if markets_list else "None"
        st.metric(
            label="⚡ Active Markets", 
            value=f"{len(st.session_state.active_markets)}",
            delta=markets_str if markets_list else "No markets yet"
        )
    
    with col4:
        time_str = st.session_state.last_updated.strftime("%H:%M:%S")
        st.metric(
            label="🕐 Last Updated", 
            value=time_str,
            delta=""
        )
    
    st.markdown("---")
    
    # ============================================================
    # SIDEBAR NAVIGATION
    # ============================================================
    
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
    
    # ============================================================
    # SESSION STATISTICS (DEBUG/ADMIN VIEW)
    # ============================================================
    
    with st.sidebar.expander("📊 Session Stats", expanded=False):
        st.markdown(f"""
        **Current Session:**
        - Total Uploads: {st.session_state.total_uploads}
        - Successful: {st.session_state.successful_uploads}
        - Failed: {st.session_state.failed_uploads}
        - Today: {st.session_state.today_uploads}
        - Markets: {', '.join(sorted(st.session_state.active_markets)) if st.session_state.active_markets else 'None'}
        """)
        
        if st.button("🔄 Reset All Stats", key="reset_stats"):
            st.session_state.total_uploads = 0
            st.session_state.successful_uploads = 0
            st.session_state.failed_uploads = 0
            st.session_state.today_uploads = 0
            st.session_state.active_markets = set()
            st.session_state.last_updated = datetime.now()
            st.rerun()
    
    # ============================================================
    # HELP SECTIONS
    # ============================================================
    
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
    
    # ============================================================
    # PAGE ROUTING
    # ============================================================
    
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
    
    # ============================================================
    # FOOTER
    # ============================================================
    
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Need Help?**")
        st.markdown("Contact: trinh.nguyen@aprime.so")
    
    with col2:
        st.markdown("**Documentation**")
        if st.button("View Docs", key="view_docs"):
            st.session_state.show_docs = not st.session_state.get("show_docs", False)
    
    with col3:
        st.markdown("**Report Issues**")
        st.markdown("[Bug Tracker](#)")
    
    # Docs section
    if st.session_state.get("show_docs", False):
        st.markdown("---")
        st.markdown("## 📖 Documentation")
        st.markdown("""
        **Hướng dẫn sử dụng:**
        Hí, chào cả nhà. Em chưa viết cí này hẹ hẹ. Nhưng mà em sẽ viết sớm thôi ạ.
        Cảm ơn mọi người đã sử dụng công cụ của em! ❤️
        """)

if __name__ == "__main__":
    if "show_docs" not in st.session_state:
        st.session_state.show_docs = False
    main()