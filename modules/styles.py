global_css = """
<style>
    /* Global Font & Colors */
    html, body, [class*="css"] {
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Dark Mode Adjustments (Streamlit handles dark mode automatically, but we can refine) */
    
    /* Card-like containers for metrics */
    .stMetric {
        background-color: #262730;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Custom Buttons */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
    }
    
    /* Tables */
    .dataframe {
        font-size: 14px !important;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #1E1E1E;
    }
</style>
"""
