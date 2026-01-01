import time
import json
import sys
import os
import warnings
from collections import deque
from datetime import datetime, timezone

warnings.simplefilter("ignore")

# ==============================================================================
#  LUMA SINGULARITY [V2.3.1 PRODUCTION: EMERGENCY ANCHOR & GHOST FLUSH]
# ==============================================================================

# --- PATH CONFIGURATION ---
DATA_DIR = "/app/data"
if not os.path.exists(DATA_DIR):
    try:
        os.makedirs(DATA_DIR)
        print(f">> Created persistent directory: {DATA_DIR}")
    except Exception as e:
        print(f"xx FAILED TO CREATE DATA DIR: {e}")

CONFIG_FILE = "server_config.json"
ANCHOR_FILE = os.path.join(DATA_DIR, "equity_anchor.json")
VOLUME_FILE = os.path.join(DATA_DIR, "daily_volume.json")
HISTORY_FILE = os.path.join(DATA_DIR, "trade_logs.json")
FINGERPRINT_FILE = os.path.join(DATA_DIR, "fingerprints.json")
BTC_TICKER = "BTC"

FLEET_CONFIG = {
    "WIF":    {"type": "MEME", "lev": 5, "risk_mult": 1.0, "stop_loss": 0.06},
    "DOGE":   {"type": "MEME", "lev": 5, "risk_mult": 1.0, "stop_loss": 0.06},
    "PENGU":  {"type": "MEME", "lev": 5, "risk_mult": 1.0, "stop_loss": 0.06},
    "POPCAT": {"type": "MEME", "lev": 5, "risk_mult": 1.0, "stop_loss": 0.06},
    "BRETT":  {"type": "MEME", "lev": 5, "risk_mult": 1.0, "stop_loss": 0.06},
    "SPX":    {"type": "MEME", "lev": 5, "risk_mult": 1.0, "stop_loss": 0.06}
}

# --- EMERGENCY ANCHOR: YOUR REAL BASELINE ---
STARTING_EQUITY = 412.0 

# --- PERSISTENT LOGGING & METADATA ---
def load_history():
    """Restores last 60 logs from disk"""
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                return deque(json.load(f), maxlen=60)
        return deque(maxlen=60)
    except: return deque(maxlen=60)

def save_history(history_deque):
    """Saves logs with Date/Time for dashboard persistence"""
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(list(history_deque), f)
    except: pass

def log_fingerprint(coin, pnl_pct, candles, session):
    """Phase 1: Elite Learning (Success Anchor >= 5%)"""
    if pnl_pct < 0.05: return 
    try:
        c = candles[-1]
        fingerprint = {
            "timestamp": time.strftime("[%d-%b %H:%M:%S]"),
            "coin": coin, "pnl": f"{pnl_pct*100:.2f}%", "session": session,
            "px": c.get('close', 0), "v": c.get('v', 0)
        }
        logs = []
        if os.path.exists(FINGERPRINT_FILE):
            with open(FINGERPRINT_FILE, 'r') as f: logs = json.load(f)
        logs.append(fingerprint)
        with open(FINGERPRINT_FILE, 'w') as f: json.dump(logs[-100:], f)
    except: pass

TRADE_HISTORY = load_history()
LIVE_ACTIVITY = "Waiting for signal..."

# --- PERSISTENT VOLUME MEMORY ---
def load_volume():
    default = {"wins": 0, "total": 0, "last_reset_day": datetime.now(timezone.utc).day}
    try:
        if os.path.exists(VOLUME_FILE):
            with open(VOLUME_FILE, 'r') as f:
                d = json.load(f)
                if d.get("last_reset_day") != datetime.now(timezone.utc).day: return default
                return d
        return default
    except: return default

def save_volume():
    global DAILY_STATS
    try:
        with open(VOLUME_FILE, 'w') as f:
            json.dump(DAILY_STATS, f)
            f.flush(); os.fsync(f.fileno())
    except: pass

DAILY_STATS = load_volume()

# --- RECOVERY LOGIC: NO GHOST POSITIONS ---
def normalize_positions(raw_positions):
    """Ensures dashboard only shows current exchange reality"""
    if not raw_positions: return []
    clean_pos = []
    for item in raw_positions:
        try:
            p = item['position'] if 'position' in item else item
            coin = p.get('coin') or p.get('symbol') or "UNKNOWN"
            size = float(p.get('szi') or p.get('size') or 0)
            # Kill dust/ghost positions
            if abs(size) < 0.0001: continue 
            
            entry = float(p.get('entryPx') or p.get('entry_price') or 0)
            pnl = float(p.get('unrealizedPnl') or 0)
            clean_pos.append({"coin": coin, "size": size, "entry": entry, "pnl": pnl})
        except: continue
    return clean_pos

def update_dashboard(equity, cash, status_msg, positions, mode="AGGRESSIVE", secured_list=[], trade_event=None, activity_event=None, session="N/A"):
    global STARTING_EQUITY, TRADE_HISTORY, LIVE_ACTIVITY, DAILY_STATS
    try:
        pnl_val = equity - STARTING_EQUITY
        
        if trade_event:
            t_str = time.strftime("[%d-%b %H:%M:%S]")
            final_msg = f"{t_str} {trade_event}" if not trade_event.startswith("[") else trade_event
            TRADE_HISTORY.append(final_msg); save_history(TRADE_HISTORY)
        
        if activity_event: LIVE_ACTIVITY = f">> {activity_event}"

        pos_str, risk_report = "NO_TRADES", []
        if positions:
            pos_lines = []
            for p in positions:
                coin, size, entry, pnl = p['coin'], p['size'], p['entry'], p['pnl']
                side = "LONG" if size > 0 else "SHORT"
                lev = FLEET_CONFIG.get(coin, {}).get('lev', 5)
                margin = (abs(size) * entry) / lev
                roe = (pnl / margin) * 100 if margin > 0 else 0.0
                target = entry * (1 + (1/lev)) if side == "LONG" else entry * (1 - (1/lev))
                t_px = f"{target:.6f}" if target < 1.0 else f"{target:.2f}"
                pos_lines.append(f"{coin}|{side}|{pnl:.2f}|{roe:.1f}|{'🔒' if coin in secured_list else ''}|{t_px}")
                risk_report.append(f"{coin}|{side}|{margin:.2f}|{'SECURED' if coin in secured_list else 'RISK ON'}|{entry if coin in secured_list else 'Stop Loss'}")
            pos_str = "::".join(pos_lines)

        wr = int((DAILY_STATS["wins"] / DAILY_STATS["total"]) * 100) if DAILY_STATS["total"] > 0 else 0
        data = {
            "equity": f"{equity:.2f}", "cash": f"{cash:.2f}", "pnl": f"{pnl_val:+.2f}",
            "status": status_msg, "session": session, "win_rate": f"{DAILY_STATS['wins']}/{DAILY_STATS['total']} ({wr}%)",
            "trade_history": "||".join(list(TRADE_HISTORY)), "live_activity": LIVE_ACTIVITY, 
            "positions": pos_str, "risk_report": "::".join(risk_report if risk_report else ["NO_TRADES"]),
            "mode": mode, "updated": time.time()
        }
        with open(os.path.join(DATA_DIR, "dashboard_state.json"), "w") as f: json.dump(data, f, ensure_ascii=False)
    except: pass

# --- CORE INITIALIZATION ---
try:
    from vision import Vision; from hands import Hands; from xenomorph import Xenomorph
    from smart_money import SmartMoney; from deep_sea import DeepSea; from messenger import Messenger
    from chronos import Chronos; from historian import Historian; from oracle import Oracle
    from seasonality import Seasonality; from predator import Predator
    
    vision, hands, xeno, whale, ratchet, msg, chronos, history, oracle, season, predator = Vision(), Hands(), Xenomorph(), SmartMoney(), DeepSea(), Messenger(), Chronos(), Historian(), Oracle(), Seasonality(), Predator()
    print(">> SYSTEM INTEGRITY: 100%")
except Exception as e: print(f"xx LOAD ERROR: {e}"); sys.exit()

def main_loop():
    global STARTING_EQUITY
    print("🦅 LUMA SINGULARITY V2.3.1 (STABLE PRODUCTION)")
    try:
        address = os.environ.get("WALLET_ADDRESS") or json.load(open(CONFIG_FILE)).get('wallet_address')
        msg.send("info", "🦅 **LUMA ONLINE:** V2.3.1 EMERGENCY STABILIZATION ACTIVE.")
        last_history_check = 0; cached_history_data = {'regime': 'NEUTRAL'}; leverage_memory = {}

        while True:
            sess = chronos.get_session(); sess_name = sess['name']
            
            # API FETCH
            eq, csh, pos, ords = 0.0, 0.0, [], []
            try:
                state = vision.get_user_state(address)
                if state:
                    eq = float(state.get('marginSummary', {}).get('accountValue', 0))
                    csh = float(state.get('withdrawable', 0))
                    pos = normalize_positions(state.get('assetPositions', []))
                    ords = state.get('openOrders', [])
            except: pos = [] # Force empty on API failure

            roe_pct = ((eq - STARTING_EQUITY) / STARTING_EQUITY) * 100
            
            # MODE RE-CALIBRATION
            risk_mode = "STANDARD"
            if eq < 412.0 or roe_pct <= -10.0: risk_mode = "RECOVERY"
            elif roe_pct >= 5.0: risk_mode = "GOD_MODE"
            
            status = f"Mode:{risk_mode} | ROE:{roe_pct:.2f}%"
            update_dashboard(eq, csh, status, pos, risk_mode, ratchet.secured_coins, session=sess_name)

            # SCANNING LOOP
            active = [p['coin'] for p in pos]
            for coin, rules in FLEET_CONFIG.items():
                t_lev = 10 if risk_mode == "GOD_MODE" and rules['type'] == "MEME" else rules['lev']
                if coin not in active and leverage_memory.get(coin) != int(t_lev):
                    try: hands.set_leverage_all([coin], leverage=int(t_lev)); leverage_memory[coin] = int(t_lev)
                    except: pass
                
                if ratchet.check_trauma(hands, coin) or next((p for p in pos if p['coin'] == coin), None): continue
                try: candles = vision.get_candles(coin, "1h")
                except: candles = []
                if not candles: continue
                
                px = float(candles[-1].get('close', 0))
                update_dashboard(eq, csh, status, pos, risk_mode, ratchet.secured_coins, session=sess_name, activity_event=f"Scanning {coin}...")

                # SIGNAL ENGINE
                prop, trend = None, predator.analyze_divergence(candles, coin)
                whale_s, xeno_s = whale.hunt_turtle(candles) or whale.hunt_ghosts(candles), xeno.hunt(coin, candles)
                
                if xeno_s == "ATTACK" and (risk_mode != "RECOVERY" or trend == "REAL_PUMP"):
                    prop = {"source": "SNIPER", "side": "BUY", "px": px * 0.999}
                if whale_s and trend != "REAL_PUMP":
                    prop = {"source": whale_s['type'], "side": whale_s['side'], "px": whale_s['price']}

                if prop and oracle.consult(coin, prop['source'], prop['px'], f"Session: {sess_name}"):
                    final_sz = max(round(min(eq * 0.11 * season.get_multiplier(rules['type']).get('mult', 1.0), eq * 0.165) * t_lev, 2), 40)
                    hands.place_trap(coin, prop['side'], prop['px'], final_sz)
                    msg.notify_trade(coin, prop['source'], prop['px'], final_sz)
                    update_dashboard(eq, csh, status, pos, risk_mode, ratchet.secured_coins, trade_event=f"OPEN {coin} ({prop['source']})", session=sess_name)
            
            # POSITION MANAGEMENT
            r_events = ratchet.manage_positions(hands, pos, FLEET_CONFIG)
            if r_events:
                for ev in r_events:
                    if any(x in ev for x in ["PROFIT", "+", "WIN"]): 
                        DAILY_STATS["total"] += 1; DAILY_STATS["wins"] += 1; save_volume()
                        log_fingerprint(ev.split(":")[1].split("(")[0].strip(), 0.05, candles, sess_name)
                    elif any(x in ev for x in ["LOSS", "-", "LOSE"]): 
                        DAILY_STATS["total"] += 1; save_volume()
                    update_dashboard(eq, csh, status, pos, risk_mode, ratchet.secured_coins, trade_event=ev, session=sess_name)
            
            time.sleep(3)
    except Exception as e: print(f"xx CRITICAL: {e}"); msg.send("errors", f"CRASH: {e}")

if __name__ == "__main__":
    main_loop()
