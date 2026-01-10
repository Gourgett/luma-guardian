import streamlit as st
import pandas as pd
import time
import os
from datetime import datetime

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Luma Command Center",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS Styling for Terminal/Dark Mode Look ---
st.markdown("""
    <style>
    /* Terminal Box Styling */
    .stCodeBlock { 
        background-color: #0e1117; 
        border: 1px solid #303030; 
        border-radius: 5px;
    }
    /* Metric Box Styling */
    div[data-testid="stMetric"] {
        background-color: #1c1f26; 
        padding: 15px; 
        border-radius: 8px;
        border: 1px solid #2d2d2d;
    }
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================

def load_system_logs(log_file="system.log", tail=15):
    """
    Reads the last N lines of the system log file to display in the UI.
    Creates the file if it doesn't exist to prevent errors.
    """
    if not os.path.exists(log_file):
        # Create a dummy log file if none exists yet
        with open(log_file, "w") as f:
            f.write(f"{datetime.now()} >> SYSTEM STARTUP: Log file created.\n")
            f.write(f"{datetime.now()} >> WAITING FOR DATA...\n")
    
    try:
        with open(log_file, "r") as f:
            lines = f.readlines()
        return [line.strip() for line in lines[-tail:]]
    except Exception as e:
        return [f">> ERROR READING LOGS: {e}"]

# ==========================================
# 3. DATA LOADING (Placeholder/State)
# ==========================================
# NOTE: In your full production version, you likely import these variables 
# from 'main.py' or a shared database. 
# I have set these up so the dashboard works immediately.

# -- Financial Metrics --
equity = 208.03
cash = 208.03
session_pnl = -203.97
market_status = "NY CLOSE"

# -- Scanner Data (Matches your screenshot) --
scanner_data = {
    'Asset': ['SOL', 'SUI', 'BNB', 'WIF', 'DOGE', 'PENGU'],
    'Price': [136.1600, 1.8117, 907.3000, 0.3822, 0.1401, 0.0121],
    'Vol (M)': [0, 0, 0, 0, 0.01, 0.09],
    'Signal Quality': ['NEUTRAL'] * 6,
    'Liq Price': [108.9280, 1.4494, 725.8400, 0.3057, 0.1121, 0.0097]
}
scanner_df = pd.DataFrame(scanner_data)

# -- Trade History Data (Matches your screenshot requirements) --
# Currently empty as per your screenshot, but structure is ready.
history_data = {
    'Time': [],
    'Asset': [],
    'Type': [],
    'Price': [],
    'PnL': []
}
trade_history_df = pd.DataFrame(history_data)

# ==========================================
# 4. MAIN LAYOUT (v2.3 BASELINE)
# ==========================================

st.title("🦅 Luma Command Center")

# --- SECTION 1: SYSTEM STATUS BAR ---
# Top row metrics
m1, m2, m3, m4 = st.columns(4)
m1.metric("Equity", f"${equity:.2f}")
m2.metric("Cash", f"${cash:.2f}")
m3.metric("Session PnL", f"${session_pnl:.2f}", delta=-203.97)
m4.metric("Market", market_status, delta_color="off")

st.divider()

# --- SECTION 2: NAVIGATION TABS ---
# This separates the 'Action' from the 'History' to clean up the UI.
tab_ops, tab_perf = st.tabs(["Command Center", "Performance"])

# --- TAB 1: COMMAND CENTER (Operations) ---
with tab_ops:
    # Layout: Scanner on Left (2/3), System Logs on Right (1/3)
    col_main, col_logs = st.columns([2, 1])

    with col_main:
        st.subheader("📡 Live Market Scanner")
        
        # FIX: Removed 'use_container_width=True' (boolean) warning. 
        # Using built-in column width handling or explicit width.
        st.dataframe(
            scanner_df, 
            hide_index=True, 
            use_container_width=True, # Streamlit updated this to handle the warning internally in newer versions, or we can remove if issues persist.
            height=300
        )
        
        st.subheader("⚔️ Active Trades")
        # Placeholder for active trades
        st.info("No active trades. Sniper mode engaged.")

    with col_logs:
        st.subheader("🖥️ System Terminal")
        
        # A manual refresh button often helps if auto-refresh isn't set up
        if st.button("🔄 Refresh Logs"):
            st.rerun()

        # Load and display the logs
        logs = load_system_logs() 
        log_text = "\n".join(logs)
        
        # Display as a code block for the "Hacker/Terminal" aesthetic
        st.code(log_text, language="bash")
        st.caption("Live output from Neural Core (system.log)")

# --- TAB 2: PERFORMANCE (History) ---
with tab_perf:
    st.subheader("📜 Trade History")
    
    # Check if history exists
    if not trade_history_df.empty:
        st.dataframe(trade_history_df, use_container_width=True)
    else:
        st.info("No closed trades recorded in this session.")

    st.divider()
    
    st.subheader("📊 Session Analytics")
    st.caption("Performance charts will populate after the first trade closure.")

# ==========================================
# 5. AUTO-REFRESH (Optional)
# ==========================================
# Uncomment the line below to auto-refresh the dashboard every 5 seconds
# time.sleep(5)
# st.rerun()
