import streamlit as st
import pandas as pd
import time
import json
import os
import datetime

# ==========================================
# 1. CONFIGURATION
# ==========================================
st.set_page_config(page_title="Luma Command v3.0", layout="wide", page_icon="🛡️")

# [LUMA MEMORY] Hard Sell Logic
HARD_SELL_PERCENT = 0.02 

def calculate_hard_sell(price):
    if price is None or price == 0: return 0.0
    return float(price) * (1 - HARD_SELL_PERCENT)

# ==========================================
# 2. DATA LOADING (PATCHED)
# ==========================================
# ALIGN DIRECTORY LOGIC WITH BACKEND
DATA_DIR = "/app/data" if os.path.exists("/app/data") else "."
STATE_FILE = os.path.join(DATA_DIR, "dashboard_state.json")
STATS_FILE = os.path.join(DATA_DIR, "stats.json")

def load_json(filepath, retries=3):
    """STABILITY PATCH: Retries loading JSON to handle race conditions."""
    if not os.path.exists(filepath): return None
    for _ in range(retries):
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            time.sleep(0.1)
            continue
        except Exception:
            return None
    return None

def format_signal(signal):
    """Translates System Codes to readable UI Signals."""
    s = str(signal).upper()
    if "ATTACK" in s or "BREAKOUT" in s: return "⚔️ BREAKOUT"
    if "PRINCE" in s:
        if "TREND" in s: return "👑 PRINCE TREND"
        return "👑 SMART MONEY"
    if "MEME" in s:
        if "DUMP" in s: return "⚠️ MEME DUMP"
        return "🚀 MEME PUMP"
    if "WHALE" in s:        return "🐋 WHALE ALERT"
    if "FAKE" in s:         return "⚠️ FAKE PUMP"
    if "FVG" in s:          return "👻 GHOST GAP"
    if "BUY" in s:          return "🟢 BUY SIGNAL"
    if "SELL" in s:         return "🔴 SELL SIGNAL"
    if "NEUTRAL" in s:      return "Scanning..."
    if "WAITING" in s:      return "Scanning..."
    return s

# ==========================================
# 3. SIDEBAR (History)
# ==========================================
def render_sidebar(last_update):
    st.sidebar.title("🛡️ Luma Guardian")
    
    if last_update:
        st.sidebar.success(f"⚡ Connected: {last_update}")
        st.sidebar.caption(f"Reading from: {DATA_DIR}")
    else:
        st.sidebar.error("⚠️ Disconnected")

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

# Get timestamp of file to verify freshness
last_update_time = None
if os.path.exists(STATE_FILE):
    t = os.path.getmtime(STATE_FILE)
    last_update_time = datetime.datetime.fromtimestamp(t).strftime('%H:%M:%S')

render_sidebar(last_update_time)

st.markdown("""
<style>
    .terminal-box { 
        font-family: 'Courier New', monospace; 
        font-size: 13px; 
        color: #33ff00; 
        background-color: #0e0e0e; 
        padding: 15px; 
        border-radius: 5px; 
        height: 250px; 
        overflow-y: scroll; 
        white-space: pre-wrap;
    }
    div[data-testid="stMetricValue"] { font-size: 1.4rem; }
</style>
""", unsafe_allow_html=True)

mode = data.get('mode', 'STANDARD') if data else 'STANDARD'
st.title(f"LUMA SINGULARITY COMMAND [{mode}]")

if data:
    # --- A. METRICS HEADER ---
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Equity", f"${data.get('equity', 0):,.2f}")
    c2.metric("Cash", f"${data.get('cash', 0):,.2f}")
    c3.metric("PnL Season", f"${data.get('pnl', 0):,.2f}")
    roe_val = data.get('account_roe', 0.0)
    c4.metric("Account ROE", f"{roe_val:.2f}%", delta=roe_val)
    c5.metric("Market Session", data.get('session', 'OFFLINE'))

    st.divider()

    # --- B. VELOCITY SCANNER ---
    st.subheader("📡 Velocity Scanner (Live Feed)")
    scan_raw = data.get('scan_results', [])
    
    if scan_raw:
        df = pd.DataFrame(scan_raw)
        df['Symbol'] = df['coin']
        df['Signal'] = df['quality'].apply(format_signal)
        df['Price'] = df['price']
        df['Hard Sell'] = df['price'].apply(calculate_hard_sell)
        
        # [FIX 2] STRICT WIDTH COMPLIANCE FOR NEW STREAMLIT
        st.dataframe(
            df[['Symbol', 'Signal', 'Price', 'Hard Sell']],
            column_config={
                "Symbol": st.column_config.TextColumn("Asset", width="small"),
                "Signal": st.column_config.TextColumn("Luma Signal", width="medium"),
                "Price": st.column_config.NumberColumn(format="$%.4f"),
                "Hard Sell": st.column_config.NumberColumn(format="$%.4f", help="-2% Liquid Projection"),
            },
            hide_index=True,
            width=None  # Removed entirely to force default behavior, preventing crash
        )
    else:
        st.info("Scanner initializing... Waiting for first pulse.")

    st.divider()

    # --- C. LIVE POSITIONS ---
    st.subheader("⚡ Active Positions")
    positions = data.get('positions', [])
    secured_coins = data.get('secured_coins', [])

    if positions:
        pos_df = pd.DataFrame(positions)
        pos_df['Margin'] = (pos_df['entry'] * pos_df['size'].abs()) / 5
        def safe_roe(row):
            if row['Margin'] == 0: return 0.0
            return (row['pnl'] / row['Margin']) * 100

        pos_df['ROE'] = pos_df.apply(safe_roe, axis=1)
        pos_df['Status'] = pos_df['coin'].apply(lambda x: "🔒 SECURED" if x in secured_coins else "🌊 RISK ON")

        st.dataframe(
            pos_df,
            column_config={
                "coin": "Symbol",
                "Status": st.column_config.TextColumn("Risk Status", width="medium"),
                "Margin": st.column_config.NumberColumn("Margin ($)", format="$%.2f"),
                "size": st.column_config.NumberColumn("Size (Coins)", format="%.4f"),
                "entry": st.column_config.NumberColumn("Entry", format="$%.4f"),
                "pnl": st.column_config.NumberColumn("PnL ($)", format="$%.2f"),
                "ROE": st.column_config.NumberColumn("ROE (%)", format="%.2f %%"),
            },
            hide_index=True,
            width=None # Removed entirely to force default behavior
        )
    else:
        st.write("No active positions.")

    st.divider()

    # --- D. SYSTEM LOGS ---
    st.subheader("📟 System Logs")
    logs = data.get('logs', [])
    if logs:
        log_content = "\n".join(logs[:50]) 
        st.markdown(f'<div class="terminal-box">{log_content}</div>', unsafe_allow_html=True)
    else:
        st.text("Waiting for system logs...")
else:
    st.warning(f"Connecting to Main Loop... Looking in: {STATE_FILE}")
    if not os.path.exists(STATE_FILE):
        st.error(f"File NOT found at {STATE_FILE}. Waiting for main.py to create it.")

time.sleep(1) 
st.rerun()
