import streamlit as st
import pandas as pd
import json
import time
import os

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Luma Singularity",
    layout="wide",
    page_icon="🦅",
    initial_sidebar_state="expanded"
)

# --- PATHS ---
DATA_DIR = "/app/data" if os.path.exists("/app/data") else "."
STATE_FILE = os.path.join(DATA_DIR, "dashboard_state.json")
STATS_FILE = os.path.join(DATA_DIR, "stats.json")

# --- UTILS ---
def load_json(path):
    try:
        if os.path.exists(path):
            with open(path, 'r') as f: return json.load(f)
    except: pass
    return None

def get_mode_color(mode):
    if mode == "GOD MODE": return "🟢"
    if mode == "RECOVERY": return "🔴"
    return "🔵"

# --- SIDEBAR ---
with st.sidebar:
    st.title("🦅 SYSTEM STATUS")
    
    state = load_json(STATE_FILE)
    stats = load_json(STATS_FILE)
    
    if state:
        mode = state.get("mode", "INIT")
        color = get_mode_color(mode)
        st.markdown(f"### {color} {mode}")
        st.caption(f"Session: {state.get('session', 'GLOBAL')}")
        
        # Account ROE
        roe = state.get("account_roe", 0.0)
        roe_color = "green" if roe >= 0 else "red"
        st.markdown(f"**Account ROE:** :{roe_color}[{roe:.2f}%]")

        # Win Rate
        if stats:
            w = stats.get("wins", 0)
            l = stats.get("losses", 0)
            t = w + l
            wr = (w / t * 100) if t > 0 else 0
            st.metric("Daily Win Rate", f"{wr:.1f}%", f"{w}W / {l}L")
        
        if st.button("🔄 FORCE REFRESH"):
            st.rerun()
    else:
        st.error("OFFLINE: No Heartbeat")

# --- MAIN LAYOUT ---
st.title("🦅 Luma Command Center")

if state:
    # 1. HEADER METRICS
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Equity", f"${state.get('equity', '0.00')}")
    c2.metric("💵 Cash", f"${state.get('cash', '0.00')}")
    c3.metric("📈 Session PnL", f"${state.get('pnl', '0.00')}")
    c4.metric("🌍 Market", state.get("session", "UNKNOWN"))

    st.divider()

    # 2. LIVE SCANNER TABLE (Visualizing what the bot sees)
    st.subheader("📡 Live Market Scanner")
    scan_data = state.get("scan_results", [])
    if scan_data:
        df_scan = pd.DataFrame(scan_data)
        # Reorder columns if keys exist
        cols = ["coin", "price", "vol_m", "quality", "liquidity_price"]
        # Filter to ensure columns exist
        valid_cols = [c for c in cols if c in df_scan.columns]
        st.dataframe(
            df_scan[valid_cols], 
            use_container_width=True,
            column_config={
                "coin": "Asset",
                "price": st.column_config.NumberColumn("Price", format="$%.4f"),
                "vol_m": "Vol (M)",
                "quality": "Signal Quality",
                "liquidity_price": st.column_config.NumberColumn("Liq Price", format="$%.4f")
            },
            hide_index=True
        )
    else:
        st.info("Waiting for next scan cycle...")

    # 3. ACTIVE POSITIONS
    st.subheader("⚔️ Active Trades")
    pos_raw = state.get("positions", [])
    if pos_raw and isinstance(pos_raw, list) and len(pos_raw) > 0:
        df_pos = pd.DataFrame(pos_raw)
        st.dataframe(
            df_pos, 
            use_container_width=True,
            hide_index=True
        )
    else:
        st.write("No active trades.")

    # 4. HEARTBEAT / LOGS
    st.subheader("💓 Neural Heartbeat")
    logs = state.get("logs", [])
    if logs:
        st.code("\n".join(logs), language="text")
    else:
        st.caption("No recent events.")

    # 5. HISTORY TAB
    st.divider()
    st.subheader("📜 Trade History")
    if stats and "history" in stats:
        hist_df = pd.DataFrame(stats["history"])
        if not hist_df.empty:
            st.dataframe(hist_df, use_container_width=True, hide_index=True)
        else:
            st.caption("No closed trades yet.")

else:
    st.warning("Waiting for Luma connection...")
    time.sleep(2)
    st.rerun()
