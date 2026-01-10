import streamlit as st
import pandas as pd
import time
from datetime import datetime

# ==========================================
# 1. CONFIGURATION & LUMA PROTOCOL
# ==========================================
st.set_page_config(page_title="Server Command Dashboard v2.4", layout="wide", page_icon="🛡️")

# [LUMA MEMORY] Hard Sell Logic Implementation
# Calculates a hypothetical liquidation price for scanner items based on a forced exit rule.
HARD_SELL_PERCENT = 0.02 # 2% Hard Sell Limit

def calculate_hard_sell(price, type='PERP'):
    # Assuming LONGs for scanner context. logic can be expanded.
    return price * (1 - HARD_SELL_PERCENT)

# ==========================================
# 2. MOCK DATA GENERATORS (Replace with your Import Logic)
# ==========================================
# In a real scenario, you would import these from 'vision.py' or 'oracle.py'
def get_metrics():
    return {
        'Equity': 12450.00,
        'Cash': 4500.00,
        'PnL Season': 12.5,
        'ROE': 4.2,
        'Market': "London",
        'Scan Speed': "12ms"
    }

def get_scanner_data():
    # Matches Velocity Validator v5.1 Structure
    data = [
        {"Symbol": "WOTAMALAILE", "Type": "PERP", "Speed (1m)": 20.30, "TPS": 11.2, "Quality": "✅ Real Frenzy", "Price": 0.04139, "Vol (M)": 10.2},
        {"Symbol": "DGRAM", "Type": "PERP", "Speed (1m)": 5.37, "TPS": 4.9, "Quality": "✅ Real Frenzy", "Price": 0.00161, "Vol (M)": 16.8},
        {"Symbol": "WHITEWHALE", "Type": "PERP", "Speed (1m)": 3.76, "TPS": 0.6, "Quality": "❌ Whale Wick", "Price": 0.16155, "Vol (M)": 8.4},
        {"Symbol": "DN", "Type": "PERP", "Speed (1m)": 3.46, "TPS": 1.2, "Quality": "❌ Whale Wick", "Price": 1.20600, "Vol (M)": 0.59},
        {"Symbol": "ELX", "Type": "PERP", "Speed (1m)": 2.60, "TPS": 0.2, "Quality": "❌ Whale Wick", "Price": 0.00312, "Vol (M)": 0.91},
    ]
    df = pd.DataFrame(data)
    # [LUMA LOGIC] Apply Hard Sell Liquidation Calculation
    df['Liquidation*'] = df['Price'].apply(calculate_hard_sell)
    return df

def get_live_trades():
    data = [
        {"Symbol": "BTC", "Type": "PERP", "Open Price": 42000.50, "Quality": "✅ Real Frenzy", "Liq Price": 41160.00, "PnL": 120.50, "ROE": 5.4},
        {"Symbol": "ETH", "Type": "PERP", "Open Price": 2250.00, "Quality": "❌ Whale Wick", "Liq Price": 2100.00, "PnL": -15.20, "ROE": -0.8},
    ]
    return pd.DataFrame(data)

# ==========================================
# 3. DASHBOARD UI LAYOUT (v2.4 Blueprint)
# ==========================================

# --- SECTION A: GLOBAL HEADER ---
metrics = get_metrics()

# Custom CSS for metrics to match the Dark/Gaming aesthetic
st.markdown("""
<style>
    div[data-testid="stMetricValue"] { font-size: 1.2rem; }
    div[data-testid="stMarkdownContainer"] p { font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

# 6-Column Header Layout
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Equity", f"${metrics['Equity']:,.2f}")
c2.metric("Cash", f"${metrics['Cash']:,.2f}")
c3.metric("PnL Season", f"{metrics['PnL Season']}%", delta=metrics['PnL Season'])
c4.metric("ROE", f"{metrics['ROE']}%", delta=metrics['ROE'])
c5.metric("Market", metrics['Market'])
c6.metric("Scan Speed", metrics['Scan Speed'])

st.divider()

# --- SECTION B: MARKET SCANNER (Velocity Validator Style) ---
st.subheader("📡 Velocity Scanner (Futures)")
st.caption("Live Feed • 1m Burst Speed • Hard Sell Liquidation Projections")

scanner_df = get_scanner_data()

st.dataframe(
    scanner_df,
    column_config={
        "Symbol": st.column_config.TextColumn("Symbol", width="medium"),
        "Speed (1m)": st.column_config.ProgressColumn(
            "Speed (1m)",
            format="%.2f %%",
            min_value=0,
            max_value=25, # Adjusted max for visual scaling
        ),
        "TPS": st.column_config.NumberColumn("TPS", format="%.1f"),
        "Price": st.column_config.NumberColumn("Price", format="$%.5f"),
        "Vol (M)": st.column_config.NumberColumn("Vol (M)", format="%.2f M"),
        "Liquidation*": st.column_config.NumberColumn(
            "Liquidation (Hard Sell)", 
            format="$%.5f",
            help="Calculated based on 2% Hard Sell limit from current price"
        ),
    },
    use_container_width=True,
    hide_index=True
)

st.divider()

# --- SECTION C: LIVE POSITIONS ---
st.subheader("⚡ Live Positions")
st.caption("Active Executions • Real-time PnL")

live_df = get_live_trades()

st.dataframe(
    live_df,
    column_config={
        "Open Price": st.column_config.NumberColumn("Entry", format="$%.5f"),
        "Liq Price": st.column_config.NumberColumn("Liq Price", format="$%.5f"),
        "PnL": st.column_config.NumberColumn("PnL ($)", format="$%.2f"),
        "ROE": st.column_config.NumberColumn("ROE (%)", format="%.2f %%"),
    },
    use_container_width=True,
    hide_index=True
)

# --- AUTO REFRESH LOGIC (Optional) ---
# Uncomment below if you want auto-refresh every 5 seconds
# time.sleep(5)
# st.rerun()
