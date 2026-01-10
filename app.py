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

HARD_SELL_PERCENT = 0.02 

def calculate_hard_sell(price):
    if price is None or price == 0: return 0.0
    return float(price) * (1 - HARD_SELL_PERCENT)

# ==========================================
# 2. DATA LOADING
# ==========================================
DATA_DIR = "/app/data" if os.path.exists("/app/data") else "."
STATE_FILE = os.path.join(DATA_DIR, "dashboard_state.json")
STATS_FILE = os.path.join(DATA_DIR, "stats.json")

def load_json(filepath, retries=3):
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
# 3. STATIC LAYOUT (Draws Only Once)
# ==========================================
# This section runs once on load, creating the "Skeleton"
# preventing the page from wiping clean every update.

# Sidebar
sidebar_placeholder = st.sidebar.empty()

# Custom CSS
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

# Title Area
title_placeholder = st.empty()

# A. Metrics Area
metrics_placeholder = st.empty()
st.divider()

# B. Scanner Area
st.subheader("📡 Velocity Scanner (Live Feed)")
scanner_placeholder = st.empty()
st.divider()

# C. Positions Area
st.subheader("⚡ Active Positions")
positions_placeholder = st.empty()
st.divider()

# D. Logs Area
st.subheader("📟 System Logs")
logs_placeholder = st.empty()

# ==========================================
# 4. LIVE UPDATE LOOP
# ==========================================
while True:
    data = load_json(STATE_FILE)
    stats = load_json(STATS_FILE)
    
    # --- UPDATE SIDEBAR ---
    with sidebar_placeholder.container():
        st.title("🛡️ Luma Guardian")
        
        if data:
            st.success(f"⚡ Connected")
            st.caption(f"Reading: {DATA_DIR}")
        else:
            st.error("⚠️ Disconnected")

        st.markdown("---")
        
        if stats:
            wins = stats.get("wins", 0)
            losses = stats.get("losses", 0)
            total = wins + losses
            win_rate = (wins / total * 100) if total > 0 else 0.0

            c1, c2 = st.columns(2)
            c1.metric("Wins", wins)
            c2.metric("Losses", losses)
            st.metric("Win Rate", f"{win_rate:.1f}%")
            
            st.markdown("### Recent Activity")
            history = stats.get("history", [])
            if history:
                for trade in history[:8]:
                    color = "🟢" if trade['pnl'] > 0 else "🔴"
                    st.markdown(
                        f"{color} **{trade['coin']}** (${trade['pnl']})",
                        unsafe_allow_html=True
                    )

    # --- UPDATE MAIN CONTENT ---
    if data:
        # Title
        mode = data.get('mode', 'STANDARD')
        title_placeholder.title(f"LUMA SINGULARITY COMMAND [{mode}]")

        # A. Metrics
        with metrics_placeholder.container():
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Equity", f"${data.get('equity', 0):,.2f}")
            c2.metric("Cash", f"${data.get('cash', 0):,.2f}")
            c3.metric("PnL Season", f"${data.get('pnl', 0):,.2f}")
            roe_val = data.get('account_roe', 0.0)
            c4.metric("Account ROE", f"{roe_val:.2f}%", delta=roe_val)
            c5.metric("Market Session", data.get('session', 'OFFLINE'))

        # B. Scanner
        with scanner_placeholder.container():
            scan_raw = data.get('scan_results', [])
            if scan_raw:
                df = pd.DataFrame(scan_raw)
                df['Symbol'] = df['coin']
                df['Signal'] = df['quality'].apply(format_signal)
                df['Price'] = df['price']
                df['Hard Sell'] = df['price'].apply(calculate_hard_sell)
                
                st.dataframe(
                    df[['Symbol', 'Signal', 'Price', 'Hard Sell']],
                    column_config={
                        "Symbol": st.column_config.TextColumn("Asset", width="small"),
                        "Signal": st.column_config.TextColumn("Luma Signal", width="medium"),
                        "Price": st.column_config.NumberColumn(format="$%.4f"),
                        "Hard Sell": st.column_config.NumberColumn(format="$%.4f", help="-2% Liquid Projection"),
                    },
                    hide_index=True,
                    width="stretch"
                )
            else:
                st.info("Scanner initializing... Waiting for first pulse.")

        # C. Positions
        with positions_placeholder.container():
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
                    width="stretch"
                )
            else:
                st.write("No active positions.")

        # D. Logs
        with logs_placeholder.container():
            logs = data.get('logs', [])
            if logs:
                log_content = "\n".join(logs[:50]) 
                st.markdown(f'<div class="terminal-box">{log_content}</div>', unsafe_allow_html=True)
            else:
                st.text("Waiting for system logs...")

    else:
        # Fallback if file not ready yet
        title_placeholder.title("LUMA SINGULARITY COMMAND [BOOTING]")
        metrics_placeholder.warning("Connecting to Main Loop...")

    # Wait before next update inside the loop
    # This keeps the browser connection open and avoids full page reload
    time.sleep(1)
