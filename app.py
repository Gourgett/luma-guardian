import streamlit as st
import pandas as pd
import json
import time
import os

st.set_page_config(page_title="Luma Command", layout="wide", page_icon="🦅")

DATA_DIR = "/app/data"
STATE_FILE = os.path.join(DATA_DIR, "dashboard_state.json")
STATS_FILE = os.path.join(DATA_DIR, "stats.json")

def load_json(path):
    try:
        if os.path.exists(path):
            with open(path, 'r') as f: return json.load(f)
    except: pass
    return None

# --- SIDEBAR ---
with st.sidebar:
    st.header("🦅 System Status")
    if st.button("🔄 Refresh"): st.rerun()
    
    state = load_json(STATE_FILE)
    if state:
        st.success("🟢 ONLINE")
        st.metric("Mode", state.get("mode", "INIT"))
        st.metric("Session", state.get("session", "GLOBAL"))
        
        stats = load_json(STATS_FILE)
        if stats:
            w, l = stats.get("wins", 0), stats.get("losses", 0)
            t = w + l
            wr = (w / t * 100) if t > 0 else 0
            st.metric("Win Rate", f"{wr:.1f}% ({w}/{t})")
    else:
        st.error("🔴 OFFLINE")

# --- MAIN ---
st.title("🦅 Luma Command Center")

if state:
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Equity", f"${state.get('equity', '0.00')}")
    col2.metric("💵 Cash", f"${state.get('cash', '0.00')}")
    col3.metric("📈 Session PnL", f"{state.get('pnl', '0.00')}")

    st.divider()

    st.subheader("🔥 Active Fleet")
    pos_raw = state.get("positions", "NO_TRADES")
    if pos_raw and pos_raw != "NO_TRADES":
        rows = []
        for entry in pos_raw.split("::"):
            p = entry.split("|")
            if len(p) >= 4:
                rows.append({"Asset": p[0], "Side": p[1], "PnL ($)": p[2], "ROE (%)": p[3]})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("No active positions. Scanning...")

    st.divider()

    st.subheader("📜 Neural Log")
    events = state.get("events", "")
    if events:
        for log in reversed(events.split("||")):
            st.code(log, language="text")
    else:
        st.text("No recent events.")
else:
    st.warning("Waiting for Luma heartbeat...")

time.sleep(5)
st.rerun()
