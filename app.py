import streamlit as st
import pandas as pd
import time
import json
import os
from datetime import datetime

# ==========================================
# 1. CONFIGURATION
# ==========================================
st.set_page_config(page_title="Luma Command v2.5", layout="wide", page_icon="🛡️")

# [LUMA MEMORY] Hard Sell Logic
HARD_SELL_PERCENT = 0.02 

def calculate_hard_sell(price):
    if price is None or price == 0: return 0.0
    return float(price) * (1 - HARD_SELL_PERCENT)

# ==========================================
# 2. DATA FETCHING (State + Stats)
# ==========================================
# Paths match your Railway 'main.py' configuration
DATA_DIR = "data"
STATE_FILE = os.path.join(DATA_DIR, "dashboard_state.json")
STATS_FILE = os.path.join(DATA_DIR, "stats.json")

# Fallback for local testing if folder doesn't exist
if not os.path.exists(STATE_FILE): STATE_FILE = "dashboard_state.json"
if not os.path.exists(STATS_FILE): STATS_FILE = "stats.json"

def load_json(filepath):
    if not os.path.exists(filepath): return None
    try:
        with open(filepath, "r") as f: return json.load(f)
    except: return None

def get_metrics(data):
    if not data:
        return {'Equity': 0, 'Cash': 0, 'PnL': 0, 'ROE': 0, 'Market': "OFFLINE"}
    return {
        'Equity': data.get('equity', 0.0),
        'Cash': data.get('cash', 0.0),
        'PnL': data.get('pnl', 0.0),
        'ROE': data.get('account_roe', 0.0),
        'Market': data.get('session', "Unknown"),
    }

# ==========================================
# 3. UI SECTIONS
# ==========================================

# --- SIDEBAR: PERFORMANCE HISTORY ---
def render_sidebar():
    st.sidebar.title("🛡️ Luma Guardian")
    st.sidebar.markdown("---")
    
    stats = load_json(STATS_FILE)
    if not stats:
        st.sidebar.warning("No Trade History Yet")
        return

    # Win/Loss Metrics
    wins = stats.get("wins", 0)
    losses = stats.get("losses", 0)
    total = wins + losses
    win_rate = (wins / total * 100) if total > 0 else 0

    c1, c2 = st.sidebar.columns(2)
    c1.metric("Wins", wins)
    c2.metric("Losses", losses)
    st.sidebar.metric("Win Rate", f"{win_rate:.1f}%")
    
    st.sidebar.markdown("### Recent Closes")
    history = stats.get("history", [])
    
    if not history:
        st.sidebar.text("Waiting for closes...")
    else:
        for trade in history[:10]: # Show last 10
            color = "🟢" if trade['pnl'] > 0 else "🔴"
            st.sidebar.markdown(
                f"**{color} {trade['coin']}** "
                f"(${trade['pnl']}) "
                f"<span style='color:grey; font-size:0.8em'>{trade['time'].split(' ')[1]}</span>", 
                unsafe_allow_html=True
            )

# --- MAIN DASHBOARD ---
state_data = load_json(STATE_FILE)
metrics = get_metrics(state_data)
render_sidebar()

# CSS Styling
st.markdown("""
<style>
    div[data-testid="stMetricValue"] { font-size: 1.2rem; }
    div[data-testid="stMarkdownContainer"] p { font-size: 0.9rem; }
    .log-box { font-family: 'Courier New'; font-size: 12px; color: #00FF00; background-color: #000; padding: 10px; border-radius: 5px; height: 200px; overflow-y: scroll; }
</style>
""", unsafe_allow_html=True)

# 1. HEADER METRICS
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Equity", f"${metrics['Equity']:,.2f}")
c2.metric("Cash", f"${metrics['Cash']:,.2f}")
c3.metric("PnL Season", f"${metrics['PnL']:,.2f}", delta=f"{metrics['PnL']}")
c4.metric("ROE", f"{metrics['ROE']}%", delta=f"{metrics['ROE']}")
c5.metric("Market", metrics['Market'])

st.divider()

# 2. SCANNER (Cleaned Up)
st.subheader("📡 Velocity Scanner")
if state_data and 'scan_results' in state_data:
    df = pd.DataFrame(state_data['scan_results'])
    if not df.empty:
        # Map & Filter Columns
        df['Symbol'] = df['coin']
        df['Type'] = "PERP"
        df['Quality'] = df['quality'].apply(lambda x: "✅ FRENSZY" if "BUY" in str(x) else ("❄️ COOL" if "SELL" in str(x) else "Waiting..."))
        df['Price'] = df['price']
        df['Vol (M)'] = df['vol_m']
        df['Hard Sell'] = df['price'].apply(calculate_hard_sell)

        st.dataframe(
            df[['Symbol', 'Type', 'Quality', 'Price', 'Vol (M)', 'Hard Sell']],
            column_config={
                "Price": st.column_config.NumberColumn(format="$%.4f"),
                "Hard Sell": st.column_config.NumberColumn(format="$%.4f", help="-2% Hard Stop Projection"),
                "Vol (M)": st.column_config.NumberColumn(format="%.2f M"),
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Scanner Active - Waiting for next candle close...")
else:
    st.warning("Connecting to Main Loop...")

st.divider()

# 3. LIVE POSITIONS
st.subheader("⚡ Live Positions")
if state_data and 'positions' in state_data and state_data['positions']:
    pos_df = pd.DataFrame(state_data['positions'])
    pos_df['ROE %'] = (pos_df['pnl'] / (pos_df['entry'] * pos_df['size'].abs() / 5)) * 100 # Approx 5x lev
    
    st.dataframe(
        pos_df,
        column_config={
            "coin": "Symbol",
            "size": "Size",
            "entry": st.column_config.NumberColumn("Entry", format="$%.4f"),
            "pnl": st.column_config.NumberColumn("PnL ($)", format="$%.2f"),
            "ROE %": st.column_config.NumberColumn("ROE", format="%.2f %%"),
        },
        use_container_width=True,
        hide_index=True
    )
else:
    st.write("No active positions.")

st.divider()

# 4. SYSTEM LOGS (Live Bot Confirmation)
st.subheader("📟 System Logs")
if state_data and 'logs' in state_data:
    # Reverse logs to show newest first
    logs = state_data['logs']
    log_text = "\n".join(logs) if logs else "System initializing..."
    st.text_area("Live Terminal Output", value=log_text, height=200, disabled=True)
else:
    st.text("Waiting for logs...")

# Auto-Refresh
time.sleep(2)
st.rerun()
