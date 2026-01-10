import streamlit as st
import pandas as pd
import time
import json
import os

# ==========================================
# 1. CONFIGURATION
# ==========================================
st.set_page_config(page_title="Luma Command v2.7", layout="wide", page_icon="🛡️")

# [LUMA MEMORY] Hard Sell Logic
HARD_SELL_PERCENT = 0.02 

def calculate_hard_sell(price):
    if price is None or price == 0: return 0.0
    return float(price) * (1 - HARD_SELL_PERCENT)

# ==========================================
# 2. DATA LOADING
# ==========================================
# Matches your Railway/Main.py paths
DATA_DIR = "data"
STATE_FILE = os.path.join(DATA_DIR, "dashboard_state.json")
STATS_FILE = os.path.join(DATA_DIR, "stats.json")

# Fallback for local testing
if not os.path.exists(STATE_FILE): STATE_FILE = "dashboard_state.json"
if not os.path.exists(STATS_FILE): STATS_FILE = "stats.json"

def load_json(filepath):
    if not os.path.exists(filepath): return None
    try:
        with open(filepath, "r") as f: return json.load(f)
    except: return None

def format_signal(signal):
    """
    Maps raw Xenomorph/Predator signals to UI labels.
    """
    s = str(signal).upper()
    
    if "ATTACK" in s:      return "⚔️ ATTACK"
    if "WHALE" in s:       return "🐋 WHALE ALERT"
    if "FAKE" in s:        return "⚠️ FAKE PUMP"
    if "SIGNAL FOUND" in s: return "⚡ SIGNAL FOUND"
    if "BUY" in s:         return "🟢 BUY"
    if "SELL" in s:        return "🔴 SELL"
    if "NEUTRAL" in s:     return "Scanning..."
    if "WAITING" in s:     return "Scanning..."
    
    return s # Return raw signal if no match (e.g. "Scanning...")

# ==========================================
# 3. SIDEBAR (History)
# ==========================================
def render_sidebar():
    st.sidebar.title("🛡️ Luma Guardian")
    st.sidebar.markdown("---")
    
    stats = load_json(STATS_FILE)
    if not stats:
        st.sidebar.info("Initializing Stats...")
        return

    wins = stats.get("wins", 0)
    losses = stats.get("losses", 0)
    total = wins + losses
    win_rate = (wins / total * 100) if total > 0 else 0.0

    c1, c2 = st.sidebar.columns(2)
    c1.metric("Wins", wins)
    c2.metric("Losses", losses)
    st.sidebar.metric("Win Rate", f"{win_rate:.1f}%")
    
    st.sidebar.markdown("### Recent Activity")
    history = stats.get("history", [])
    
    if history:
        for trade in history[:8]:
            color = "🟢" if trade['pnl'] > 0 else "🔴"
            st.sidebar.markdown(
                f"{color} **{trade['coin']}** (${trade['pnl']})",
                unsafe_allow_html=True
            )

# ==========================================
# 4. MAIN DASHBOARD RENDER
# ==========================================
data = load_json(STATE_FILE)
render_sidebar()

# Custom CSS for the Terminal Log
st.markdown("""
<style>
    .terminal-box { 
        font-family: 'Courier New', monospace; 
        font-size: 13px; 
        color: #33ff00; 
        background-color: #0e0e0e; 
        padding: 15px; 
        border-radius: 5px; 
        border: 1px solid #333;
        height: 250px; 
        overflow-y: scroll; 
        white-space: pre-wrap;
    }
</style>
""", unsafe_allow_html=True)

st.title("LUMA SINGULARITY COMMAND")

if data:
    # --- A. METRICS ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Equity", f"${data.get('equity', 0):,.2f}")
    c2.metric("Cash", f"${data.get('cash', 0):,.2f}")
    c3.metric("PnL Season", f"${data.get('pnl', 0):,.2f}")
    c4.metric("Market Mode", data.get('mode', 'STANDARD'))

    st.divider()

    # --- B. VELOCITY SCANNER ---
    st.subheader("📡 Velocity Scanner (Live Feed)")
    
    scan_raw = data.get('scan_results', [])
    if scan_raw:
        df = pd.DataFrame(scan_raw)
        
        # 1. Map Columns
        df['Symbol'] = df['coin']
        
        # 2. Apply Custom Signal Formatter (Whale, Attack, Fake Pump)
        df['Signal'] = df['quality'].apply(format_signal)
        
        df['Price'] = df['price']
        df['Vol (M)'] = df['vol_m']
        df['Hard Sell'] = df['price'].apply(calculate_hard_sell)
        
        # 3. Render Table
        st.dataframe(
            df[['Symbol', 'Signal', 'Price', 'Vol (M)', 'Hard Sell']],
            use_container_width=True,
            column_config={
                "Symbol": st.column_config.TextColumn("Asset", width="small"),
                "Signal": st.column_config.TextColumn("Luma Signal", width="medium"),
                "Price": st.column_config.NumberColumn(format="$%.4f"),
                "Hard Sell": st.column_config.NumberColumn(format="$%.4f", help="-2% Liquid Projection"),
                "Vol (M)": st.column_config.NumberColumn(format="%.2f M"),
            },
            hide_index=True
        )
    else:
        st.info("Scanner initializing... Waiting for first pulse.")

    st.divider()

    # --- C. LIVE POSITIONS ---
    st.subheader("⚡ Active Positions")
    positions = data.get('positions', [])
    if positions:
        pos_df = pd.DataFrame(positions)
        # Calculate ROE approx if not provided
        pos_df['ROE'] = (pos_df['pnl'] / (pos_df['entry'] * pos_df['size'].abs() / 5)) * 100 

        st.dataframe(
            pos_df,
            column_config={
                "coin": "Symbol",
                "size": "Size",
                "entry": st.column_config.NumberColumn("Entry", format="$%.4f"),
                "pnl": st.column_config.NumberColumn("PnL ($)", format="$%.2f"),
                "ROE": st.column_config.NumberColumn("ROE (%)", format="%.2f %%"),
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.write("No active positions.")

    st.divider()

    # --- D. SYSTEM LOGS (TERMINAL) ---
    st.subheader("📟 System Logs")
    logs = data.get('logs', [])
    if logs:
        # Join logs with newlines
        log_content = "\n".join(logs)
        # Render as raw HTML div for styling (The "Terminal" look)
        st.markdown(f'<div class="terminal-box">{log_content}</div>', unsafe_allow_html=True)
    else:
        st.text("Waiting for system logs...")

else:
    st.warning("Connecting to Main Loop... (Check if main.py is running)")

# Auto-Refresh (Matches Pulse Speed)
time.sleep(1) 
st.rerun()
