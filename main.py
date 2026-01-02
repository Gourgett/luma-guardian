import time, json, sys, os, warnings
from collections import deque
from datetime import datetime, timezone

warnings.simplefilter("ignore")

# ==============================================================================
#  LUMA SINGULARITY [V2.3.4: HOTFIX - VISIBILITY RESTORED]
# ==============================================================================

DATA_DIR = "/app/data"
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

CONFIG_FILE = "server_config.json"
ANCHOR_FILE = os.path.join(DATA_DIR, "equity_anchor.json")
VOLUME_FILE = os.path.join(DATA_DIR, "daily_volume.json")
HISTORY_FILE = os.path.join(DATA_DIR, "trade_logs.json")
FINGERPRINT_FILE = os.path.join(DATA_DIR, "fingerprints.json")

FLEET_CONFIG = {
    "WIF": {"type": "MEME", "lev": 5}, "DOGE": {"type": "MEME", "lev": 5},
    "PENGU": {"type": "MEME", "lev": 5}, "POPCAT": {"type": "MEME", "lev": 5},
    "BRETT": {"type": "MEME", "lev": 5}, "SPX": {"type": "MEME", "lev": 5}
}

STARTING_EQUITY = 412.0

def load_history():
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f: return deque(json.load(f), maxlen=60)
        return deque(maxlen=60)
    except: return deque(maxlen=60)

def save_history(history_deque):
    try:
        with open(HISTORY_FILE, 'w') as f: json.dump(list(history_deque), f)
    except: pass

def calculate_logic_score(coin, session):
    try:
        if not os.path.exists(FINGERPRINT_FILE): return 0
        with open(FINGERPRINT_FILE, 'r') as f: fingerprints = json.load(f)
        if len(fingerprints) < 5: return 0 
        matches = [f for f in fingerprints if f['coin'] == coin and f['session'] == session]
        score = min(len(matches) * 15, 95)
        return score if score > 0 else 10
    except: return 0

def log_fingerprint(coin, pnl_pct, session):
    if pnl_pct < 0.05: return 
    try:
        finger = {"timestamp": time.strftime("%d-%b"), "coin": coin, "pnl": f"{pnl_pct*100:.1f}%", "session": session}
        logs = []
        if os.path.exists(FINGERPRINT_FILE):
            with open(FINGERPRINT_FILE, 'r') as f: logs = json.load(f)
        logs.append(finger)
        with open(FINGERPRINT_FILE, 'w') as f: json.dump(logs[-100:], f)
    except: pass

TRADE_HISTORY = load_history()
DAILY_STATS = {"wins": 0, "total": 0, "last_reset_day": datetime.now(timezone.utc).day}
LIVE_ACTIVITY = "Restoring Visuals..." 

# --- HOTFIX: ROBUST NORMALIZATION ---
def normalize_positions(raw_positions):
    """Restored robust check for 'szi' OR 'size' to fix invisible trades"""
    if not raw_positions: return []
    clean = []
    for item in raw_positions:
        try:
            p = item.get('position', item)
            # FIX: Check both keys. If 'szi' is missing, try 'size'.
            sz = float(p.get('szi') or p.get('size') or 0)
            
            # Debug: Print found positions to logs
            if abs(sz) > 0: print(f">> FOUND POS: {p.get('coin')} Size: {sz}")

            if abs(sz) < 0.0001: continue
            
            clean.append({
                "coin": p.get('coin') or p.get('symbol') or 'UNK', 
                "size": sz, 
                "entry": float(p.get('entryPx') or p.get('entry_price') or 0), 
                "pnl": float(p.get('unrealizedPnl') or 0)
            })
        except Exception as e:
            print(f"xx PARSE ERROR: {e}")
            continue
    return clean

def update_dashboard(equity, cash, status, pos, mode, secured_list, trade_event=None, activity_event=None, session="N/A"):
    global TRADE_HISTORY, DAILY_STATS, LIVE_ACTIVITY
    try:
        if trade_event:
            msg = f"[{time.strftime('%d-%b %H:%M:%S')}] {trade_event}"
            TRADE_HISTORY.append(msg); save_history(TRADE_HISTORY)
        
        if activity_event: LIVE_ACTIVITY = f">> {activity_event}"
        
        pos_str = "NO_TRADES"
        if pos:
            lines = []
            for p in pos:
                coin, size = p['coin'], p['size']
                lev = FLEET_CONFIG.get(coin, {}).get('lev', 5)
                margin = (abs(size) * p['entry']) / lev
                roe = (p['pnl'] / margin) * 100 if margin > 0 else 0
                conf = calculate_logic_score(coin, session)
                lines.append(f"{coin}|{'LONG' if size > 0 else 'SHORT'}|{p['pnl']:.2f}|{roe:.1f}|{'🔒' if coin in secured_list else ''}|0|{conf}")
            pos_str = "::".join(lines)

        wr = int((DAILY_STATS['wins']/DAILY_STATS['total'])*100) if DAILY_STATS['total'] > 0 else 0
        data = {
            "equity": f"{equity:.2f}", "cash": f"{cash:.2f}", "pnl": f"{(equity-412.0):+.2f}",
            "status": status, "mode": mode, "win_rate": f"{DAILY_STATS['wins']}/{DAILY_STATS['total']} ({wr}%)",
            "trade_history": "||".join(list(TRADE_HISTORY)), "live_activity": LIVE_ACTIVITY,
            "positions": pos_str, "session": session, "updated": time.time()
        }
        with open(os.path.join(DATA_DIR, "dashboard_state.json"), "w") as f: json.dump(data, f)
    except: pass

from vision import Vision; from hands import Hands; from xenomorph import Xenomorph; from smart_money import SmartMoney
from deep_sea import DeepSea; from messenger import Messenger; from chronos import Chronos; from predator import Predator
v, h, x, w, r, m, c, p = Vision(), Hands(), Xenomorph(), SmartMoney(), DeepSea(), Messenger(), Chronos(), Predator()

def main_loop():
    print("🦅 LUMA SINGULARITY V2.3.4 (HOTFIX ACTIVE)")
    addr = os.environ.get("WALLET_ADDRESS")
    while True:
        sess = c.get_session(); sess_name = sess['name']
        eq, csh, pos = 0.0, 0.0, []
        try:
            state = v.get_user_state(addr)
            if state:
                eq = float(state['marginSummary']['accountValue'])
                csh = float(state['withdrawable'])
                pos = normalize_positions(state.get('assetPositions', []))
        except Exception as e:
            # FIX: Print the exact error if API fails
            print(f"xx API FETCH ERROR: {e}")
            pos = []

        roe = ((eq - 412.0) / 412.0) * 100
        mode = "RECOVERY" if eq < 412.0 else ("GOD_MODE" if roe >= 5.0 else "STANDARD")
        
        update_dashboard(eq, csh, f"Mode:{mode} | ROE:{roe:.2f}%", pos, mode, r.secured_coins, session=sess_name)

        active = [x['coin'] for x in pos]
        for coin, rules in FLEET_CONFIG.items():
            if r.check_trauma(h, coin): continue
            
            if coin in active:
                update_dashboard(eq, csh, f"Mode:{mode}", pos, mode, r.secured_coins, session=sess_name, activity_event=f"Monitoring {coin} (Active)")
                continue

            try: candles = v.get_candles(coin, "1h")
            except: continue
            
            px = float(candles[-1]['close'])
            update_dashboard(eq, csh, f"Mode:{mode}", pos, mode, r.secured_coins, session=sess_name, activity_event=f"Scanning {coin} (Logic: {calculate_logic_score(coin, sess_name)}%)")

            # Logic Engine
            prop, trend = None, p.analyze_divergence(candles, coin)
            whale_s, xeno_s = w.hunt_turtle(candles) or w.hunt_ghosts(candles), x.hunt(coin, candles)
            
            if xeno_s == "ATTACK" and (mode != "RECOVERY" or trend == "REAL_PUMP"):
                prop = {"source": "SNIPER", "side": "BUY", "px": px * 0.999}
            if whale_s and trend != "REAL_PUMP":
                prop = {"source": whale_s['type'], "side": whale_s['side'], "px": whale_s['price']}

            if prop: 
                final_sz = max(round(min(eq * 0.11, eq * 0.165) * 5, 2), 40)
                h.place_trap(coin, prop['side'], prop['px'], final_sz)
                m.notify_trade(coin, prop['source'], prop['px'], final_sz)
                update_dashboard(eq, csh, f"Mode:{mode}", pos, mode, r.secured_coins, trade_event=f"OPEN {coin} ({prop['source']})", session=sess_name)

        events = r.manage_positions(h, pos, FLEET_CONFIG)
        if events:
            for ev in events:
                if "PROFIT" in ev: 
                    DAILY_STATS['wins'] += 1; DAILY_STATS['total'] += 1
                    log_fingerprint(ev.split(":")[1].split("(")[0].strip(), 0.05, sess_name)
                elif "LOSS" in ev: DAILY_STATS['total'] += 1
                update_dashboard(eq, csh, f"Mode:{mode}", pos, mode, r.secured_coins, trade_event=ev, session=sess_name)
        time.sleep(3)

if __name__ == "__main__": main_loop()
