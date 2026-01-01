import time
import json
import sys
import os
import warnings
from collections import deque
from datetime import datetime, timezone

warnings.simplefilter("ignore")

# ==============================================================================
#  LUMA SINGULARITY [V2.3 PRODUCTION: PERSISTENCE & FINGERPRINTING]
# ==============================================================================

DATA_DIR = "/app/data"
if not os.path.exists(DATA_DIR):
    try: os.makedirs(DATA_DIR)
    except Exception as e: print(f"xx DATA DIR ERROR: {e}")

CONFIG_FILE = "server_config.json"
ANCHOR_FILE = os.path.join(DATA_DIR, "equity_anchor.json")
VOLUME_FILE = os.path.join(DATA_DIR, "daily_volume.json")
HISTORY_FILE = os.path.join(DATA_DIR, "trade_logs.json")
# NEW: Learning Metadata Storage
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

STARTING_EQUITY = 0.0

# --- PERSISTENT LOGGING & METADATA ---
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

def log_fingerprint(coin, pnl_pct, candles, session):
    """Phase 1: Captures market metadata for successful trades (>= 5%)"""
    if pnl_pct < 0.05: return 
    try:
        c = candles[-1]
        fingerprint = {
            "timestamp": time.strftime("[%d-%b %H:%M:%S]"),
            "coin": coin,
            "pnl": f"{pnl_pct*100:.2f}%",
            "session": session,
            "price": c.get('close', 0),
            "vol_24h": c.get('v', 0),
            # Metadata for future learning
            "type": FLEET_CONFIG.get(coin, {}).get('type', 'MEME')
        }
        logs = []
        if os.path.exists(FINGERPRINT_FILE):
            with open(FINGERPRINT_FILE, 'r') as f: logs = json.load(f)
        logs.append(fingerprint)
        with open(FINGERPRINT_FILE, 'w') as f: json.dump(logs[-100:], f) # Keep last 100 elite samples
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
                return d if d.get("last_reset_day") == datetime.now(timezone.utc).day else default
        return default
    except: return default

def save_volume():
    global DAILY_STATS
    try:
        with open(VOLUME_FILE, 'w') as f: json.dump(DAILY_STATS, f); f.flush(); os.fsync(f.fileno())
    except: pass

DAILY_STATS = load_volume()

def load_anchor(equity):
    try:
        if os.path.exists(ANCHOR_FILE):
            with open(ANCHOR_FILE, 'r') as f: return float(json.load(f).get("start_equity", equity))
        with open(ANCHOR_FILE, 'w') as f: json.dump({"start_equity": equity}, f); return equity
    except: return equity

def update_heartbeat(status="ALIVE"):
    try:
        with open("heartbeat.tmp", "w") as f: json.dump({"last_beat": time.time(), "status": status}, f)
        os.replace("heartbeat.tmp", "heartbeat.json")
    except: pass

def update_dashboard(equity, cash, status_msg, positions, mode="AGGRESSIVE", secured_list=[], trade_event=None, activity_event=None, session="N/A"):
    global STARTING_EQUITY, TRADE_HISTORY, LIVE_ACTIVITY, DAILY_STATS
    try:
        if STARTING_EQUITY == 0.0 and equity > 0: STARTING_EQUITY = load_anchor(equity)
        
        if trade_event:
            t_str = time.strftime("[%d-%b %H:%M:%S]")
            final_msg = f"{t_str} {trade_event}" if not trade_event.startswith("[") else trade_event
            TRADE_HISTORY.append(final_msg); save_history(TRADE_HISTORY)
        
        if activity_event: LIVE_ACTIVITY = f">> {activity_event}"

        pos_str, risk_report = "NO_TRADES", []
        if positions:
            pos_lines = []
            for p in positions:
                coin, size, entry, pnl_val = p['coin'], p['size'], p['entry'], p['pnl']
                side = "LONG" if size > 0 else "SHORT"
                lev = 10 if mode == "GOD_MODE" and FLEET_CONFIG.get(coin, {}).get('type') == "MEME" else FLEET_CONFIG.get(coin, {}).get('lev', 10)
                margin = (abs(size) * entry) / lev
                roe = (pnl_val / margin) * 100 if margin > 0 else 0.0
                target = entry * (1 + (1/lev)) if side == "LONG" else entry * (1 - (1/lev))
                t_px = f"{target:.6f}" if target < 1.0 else f"{target:.2f}"
                pos_lines.append(f"{coin}|{side}|{pnl_val:.2f}|{roe:.1f}|{'🔒' if coin in secured_list else ''}|{t_px}")
                risk_report.append(f"{coin}|{side}|{margin:.2f}|{'SECURED' if coin in secured_list else 'RISK ON'}|{entry if coin in secured_list else 'Stop Loss'}")
            pos_str = "::".join(pos_lines)

        wr = int((DAILY_STATS["wins"] / DAILY_STATS["total"]) * 100) if DAILY_STATS["total"] > 0 else 0
        data = {
            "equity": f"{equity:.2f}", "cash": f"{cash:.2f}", "pnl": f"{(equity - STARTING_EQUITY):+.2f}",
            "status": status_msg, "session": session, "win_rate": f"{DAILY_STATS['wins']}/{DAILY_STATS['total']} ({wr}%)",
            "trade_history": "||".join(list(TRADE_HISTORY)), "live_activity": LIVE_ACTIVITY, 
            "positions": pos_str, "risk_report": "::".join(risk_report if risk_report else ["NO_TRADES"]),
            "mode": mode, "updated": time.time()
        }
        with open("dashboard_state.tmp", "w") as f: json.dump(data, f, ensure_ascii=False)
        os.replace("dashboard_state.tmp", "dashboard_state.json")
    except: pass

# --- CORE MODULE LOAD ---
try:
    from vision import Vision; from hands import Hands; from xenomorph import Xenomorph
    from smart_money import SmartMoney; from deep_sea import DeepSea; from messenger import Messenger
    from chronos import Chronos; from historian import Historian; from oracle import Oracle
    from seasonality import Seasonality; from predator import Predator
    update_heartbeat("STARTING")
    vision, hands, xeno, whale, ratchet, msg, chronos, history, oracle, season, predator = Vision(), Hands(), Xenomorph(), SmartMoney(), DeepSea(), Messenger(), Chronos(), Historian(), Oracle(), Seasonality(), Predator()
    print(">> SYSTEM INTEGRITY: 100%")
except Exception as e: print(f"xx LOAD ERROR: {e}"); sys.exit()

def main_loop():
    global STARTING_EQUITY
    print("🦅 LUMA SINGULARITY V2.3 PRODUCTION")
    try:
        update_heartbeat("BOOTING")
        address = os.environ.get("WALLET_ADDRESS") or json.load(open(CONFIG_FILE)).get('wallet_address')
        msg.send("info", "🦅 **LUMA ONLINE:** V2.3 PRODUCTION ACTIVE.")
        last_history_check = 0; cached_history_data = {'regime': 'NEUTRAL'}; leverage_memory = {}

        while True:
            update_heartbeat("ALIVE"); sess = chronos.get_session(); sess_name = sess['name']
            if datetime.now(timezone.utc).day != DAILY_STATS["last_reset_day"]:
                global DAILY_STATS; DAILY_STATS = {"wins": 0, "total": 0, "last_reset_day": datetime.now(timezone.utc).day}; save_volume()

            if time.time() - last_history_check > 14400:
                try: 
                    btc = vision.get_candles(BTC_TICKER, "1d")
                    if btc: cached_history_data = history.check_regime(btc); last_history_check = time.time()
                except: pass

            eq, csh, pos, ords = 0.0, 0.0, [], []
            try:
                state = vision.get_user_state(address)
                if state:
                    eq = float(state.get('marginSummary', {}).get('accountValue', 0))
                    csh = float(state.get('withdrawable', 0))
                    pos = normalize_positions(state.get('assetPositions', []))
                    ords = state.get('openOrders', [])
            except: pass

            if STARTING_EQUITY == 0.0 and eq > 0: STARTING_EQUITY = load_anchor(eq)
            roe_pct = ((eq - STARTING_EQUITY) / (STARTING_EQUITY if STARTING_EQUITY > 0 else 1.0)) * 100
            
            if 1.0 < eq < 300.0: time.sleep(3600); continue

            risk_mode, shield = "STANDARD", roe_pct <= -10.0
            if shield or eq < 412.0: risk_mode = "RECOVERY"
            elif roe_pct >= 5.0: risk_mode = "GOD_MODE"
            
            status = f"🛡️ SHIELD ACTIVE | ROE:{roe_pct:.2f}%" if shield else f"Mode:{risk_mode} (ROE:{roe_pct:.2f}%)"
            update_dashboard(eq, csh, status, pos, risk_mode, ratchet.secured_coins, session=sess_name)

            active = [p['coin'] for p in pos]
            for coin, rules in FLEET_CONFIG.items():
                update_heartbeat("SCANNING")
                t_lev = 10 if risk_mode == "GOD_MODE" and rules['type'] == "MEME" else (5 if risk_mode == "RECOVERY" or shield else rules['lev'])
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
                    prop = {"source": whale_s['type'], "side": whale_sig['side'], "px": whale_sig['price']}

                if prop and oracle.consult(coin, prop['source'], prop['px'], f"Session: {sess_name}"):
                    final_sz = max(round(min(eq * 0.11 * season.get_multiplier(rules['type']).get('mult', 1.0), eq * 0.165) * t_lev, 2), 40)
                    hands.place_trap(coin, prop['side'], prop['px'], final_sz)
                    msg.notify_trade(coin, prop['source'], prop['px'], final_sz)
                    update_dashboard(eq, csh, status, pos, risk_mode, ratchet.secured_coins, trade_event=f"OPEN {coin} ({prop['source']})", session=sess_name)
            
            r_events = ratchet.manage_positions(hands, pos, FLEET_CONFIG)
            if r_events:
                for ev in r_events:
                    if any(x in ev for x in ["PROFIT", "+", "WIN"]): 
                        DAILY_STATS["total"] += 1; DAILY_STATS["wins"] += 1; save_volume()
                        # Metadata Collection for Elite Wins
                        log_fingerprint(ev.split(":")[1].split("(")[0].strip(), 0.05, candles, sess_name)
                    elif any(x in ev for x in ["LOSS", "-", "LOSE"]): DAILY_STATS["total"] += 1; save_volume()
                    update_dashboard(eq, csh, status, pos, risk_mode, ratchet.secured_coins, trade_event=ev, session=sess_name)
            time.sleep(3)
    except Exception as e: print(f"xx CRITICAL: {e}"); msg.send("errors", f"CRASH: {e}")

if __name__ == "__main__":
    try: main_loop()
    except: print("\n🦅 LUMA OFFLINE")
