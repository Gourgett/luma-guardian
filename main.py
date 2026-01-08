import time, json, sys, os, warnings
from collections import deque

warnings.simplefilter("ignore")

# ==============================================================================
#  LUMA SINGULARITY [RAILWAY SAFE MODE]
#  Logic: k-Tickers | Risk 0.75 | Stop 4% | Asia Sniper
# ==============================================================================

DATA_DIR = "/app/data"
if not os.path.exists(DATA_DIR):
    try: os.makedirs(DATA_DIR)
    except: pass

CONFIG_FILE = "server_config.json"
ANCHOR_FILE = os.path.join(DATA_DIR, "equity_anchor.json")
STATS_FILE = os.path.join(DATA_DIR, "stats.json")
BTC_TICKER = "BTC"

# --- FLEET CONFIG (Safe Structure) ---
FLEET_CONFIG = {
    "WIF":    {"type": "MEME",   "lev": 5, "risk_mult": 0.75, "stop_loss": 0.04},
    "DOGE":   {"type": "MEME",   "lev": 5, "risk_mult": 0.75, "stop_loss": 0.04},
    "PENGU":  {"type": "MEME",   "lev": 5, "risk_mult": 0.75, "stop_loss": 0.04},
    "BRETT":  {"type": "MEME",   "lev": 5, "risk_mult": 0.75, "stop_loss": 0.04},
    "kBONK":  {"type": "MEME",   "lev": 5, "risk_mult": 0.75, "stop_loss": 0.04},
    "kFLOKI": {"type": "MEME",   "lev": 5, "risk_mult": 0.75, "stop_loss": 0.04}
}

STARTING_EQUITY = 0.0
EVENT_QUEUE = deque(maxlen=10)

# --- GLOBAL STATE ---
DASH_STATE = {
    "equity": 0.0, "cash": 0.0, "pnl": 0.0,
    "positions": [], "secured": [], 
    "mode": "INIT", "session": "GLOBAL"
}

def load_stats():
    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, 'r') as f: data = json.load(f)
        else: data = {"last_reset": time.strftime("%Y-%m-%d"), "wins": 0, "losses": 0}
    except: data = {"last_reset": time.strftime("%Y-%m-%d"), "wins": 0, "losses": 0}
    return data

def save_stats(stats):
    try: with open(STATS_FILE, 'w') as f: json.dump(stats, f, indent=2)
    except: pass

def update_stats(pnl, coin, reason):
    stats = load_stats()
    if pnl > 0: stats["wins"] += 1
    else: stats["losses"] += 1
    stats["total_pnl"] = stats.get("total_pnl", 0.0) + pnl
    if "history" not in stats: stats["history"] = []
    stats["history"].insert(0, {"date": time.strftime("%Y-%m-%d %H:%M"), "coin": coin, "pnl": pnl, "reason": reason})
    stats["history"] = stats["history"][:50]
    save_stats(stats)

def load_anchor(current_equity):
    try:
        if os.path.exists(ANCHOR_FILE):
            with open(ANCHOR_FILE, 'r') as f:
                data = json.load(f)
                return float(data.get("start_equity", current_equity))
        else:
            with open(ANCHOR_FILE, 'w') as f: json.dump({"start_equity": current_equity}, f)
            return current_equity
    except: return current_equity

def update_heartbeat(status="ALIVE"):
    try:
        with open(os.path.join(DATA_DIR, "heartbeat.tmp"), "w") as f:
            json.dump({"last_beat": time.time(), "status": status}, f)
        os.replace(os.path.join(DATA_DIR, "heartbeat.tmp"), os.path.join(DATA_DIR, "heartbeat.json"))
    except: pass

def normalize_positions(raw_positions):
    clean_pos = []
    if not raw_positions: return []
    for item in raw_positions:
        try:
            p = item['position'] if 'position' in item else item
            coin = p.get('coin') or "UNKNOWN"
            if coin == "UNKNOWN": continue
            size = float(p.get('szi') or 0)
            entry = float(p.get('entryPx') or 0)
            pnl = float(p.get('unrealizedPnl') or 0)
            if abs(size) < 0.0001: continue
            clean_pos.append({"coin": coin, "size": size, "entry": entry, "pnl": pnl})
        except: continue
    return clean_pos

def sync_dashboard():
    global DASH_STATE, EVENT_QUEUE
    try:
        pos_str = "NO_TRADES"
        if DASH_STATE["positions"]:
            lines = []
            for p in DASH_STATE["positions"]:
                c, s, e, pnl = p['coin'], p['size'], p['entry'], p['pnl']
                side = "LONG" if s > 0 else "SHORT"
                lev = FLEET_CONFIG.get(c, {}).get('lev', 5)
                margin = (abs(s) * e) / lev if lev > 0 else 0
                roe = (pnl / margin * 100) if margin > 0 else 0
                lines.append(f"{c}|{side}|{pnl:.2f}|{roe:.1f}|OPEN|0.00")
            pos_str = "::".join(lines)
            
        data = {
            "equity": f"{DASH_STATE['equity']:.2f}",
            "cash": f"{DASH_STATE['cash']:.2f}",
            "pnl": f"{DASH_STATE['pnl']:+.2f}",
            "mode": DASH_STATE['mode'],
            "session": DASH_STATE['session'],
            "positions": pos_str,
            "events": "||".join(list(EVENT_QUEUE)),
            "updated": time.time()
        }
        temp = os.path.join(DATA_DIR, "dashboard_state.tmp")
        with open(temp, "w") as f: json.dump(data, f, ensure_ascii=False)
        os.replace(temp, os.path.join(DATA_DIR, "dashboard_state.json"))
    except: pass

try:
    print(">> [1/10] Loading Modules...")
    from vision import Vision
    from hands import Hands
    from xenomorph import Xenomorph
    from smart_money import SmartMoney
    from deep_sea import DeepSea
    from messenger import Messenger
    from chronos import Chronos
    from historian import Historian
    from oracle import Oracle
    from seasonality import Seasonality
    from predator import Predator

    update_heartbeat("STARTING")
    vision, hands, xeno, whale, ratchet, msg, chronos, history, oracle, season, predator = Vision(), Hands(), Xenomorph(), SmartMoney(), DeepSea(), Messenger(), Chronos(), Historian(), Oracle(), Seasonality(), Predator()
except Exception as e:
    print(f"xx CRITICAL LOAD ERROR: {e}"); sys.exit()

def main_loop():
    global STARTING_EQUITY, DASH_STATE
    print("🦅 LUMA SINGULARITY (RAILWAY SAFE MODE)")
    
    cfg = json.load(open(CONFIG_FILE))
    address = cfg.get('wallet_address')
    msg.send("info", "🦅 **LUMA REBOOT:** SAFE STRUCTURE + ASIA SNIPER ACTIVE.")

    last_history_check = 0
    cached_history_data = {'regime': 'NEUTRAL', 'multiplier': 1.0}
    leverage_memory = {}

    while True:
        update_heartbeat("ALIVE")
        session_data = chronos.get_session()
        sess_name = session_data.get('name', 'GLOBAL')

        if time.time() - last_history_check > 14400:
            try:
                btc_daily = vision.get_candles(BTC_TICKER, "1d")
                if btc_daily: cached_history_data = history.check_regime(btc_daily)
                last_history_check = time.time()
            except: pass
        
        equity, cash, clean_positions, open_orders = 0.0, 0.0, [], []
        try:
            user_state = vision.get_user_state(address)
            if user_state:
                equity = float(user_state.get('marginSummary', {}).get('accountValue', 0))
                cash = float(user_state.get('withdrawable', 0))
                clean_positions = normalize_positions(user_state.get('assetPositions', []))
                open_orders = user_state.get('openOrders', [])
        except: pass

        if STARTING_EQUITY == 0.0 and equity > 0: STARTING_EQUITY = load_anchor(equity)
        current_pnl = equity - STARTING_EQUITY if STARTING_EQUITY > 0 else 0.0
        current_roe_pct = (current_pnl / STARTING_EQUITY * 100) if STARTING_EQUITY > 0 else 0.0

        if 1.0 < equity < 200.0:
             msg.send("errors", "CRITICAL: HARD FLOOR BREACHED. SHUTTING DOWN.")
             time.sleep(3600); continue

        risk_mode = "STANDARD"
        if current_roe_pct >= 5.0: risk_mode = "GOD_MODE"
        
        base_margin_usd = equity * 0.11
        max_margin_usd  = equity * 0.165
        
        # SYNC DASHBOARD
        DASH_STATE.update({"equity": equity, "cash": cash, "pnl": current_pnl, "positions": clean_positions, "mode": risk_mode, "session": sess_name})
        sync_dashboard()
        
        active_coins = [p['coin'] for p in clean_positions]

        for coin, rules in FLEET_CONFIG.items():
            update_heartbeat("SCANNING")
            target_lev = 10 if (risk_mode == "GOD_MODE" and rules['type'] == "MEME") else rules['lev']
            
            if coin not in active_coins:
                if leverage_memory.get(coin) != target_lev:
                    try: hands.set_leverage_all([coin], leverage=target_lev); leverage_memory[coin] = target_lev
                    except: pass

            if ratchet.check_trauma(hands, coin): continue
            if next((p for p in clean_positions if p['coin'] == coin), None): continue
            
            try: candles = vision.get_candles(coin, "1h")
            except: candles = []
            if not candles: continue
            current_price = float(candles[-1].get('close') or 0)
            if current_price == 0: continue

            pending = next((o for o in open_orders if o.get('coin') == coin), None)
            if pending:
                try:
                    op = float(pending.get('limitPx') or 0)
                    if abs(current_price - op) / op > 0.005: hands.cancel_all_orders(coin)
                except: pass
                continue

            proposal = None
            trend_status = predator.analyze_divergence(candles, coin)
            season_info = season.get_multiplier(rules['type'])
            context_str = f"Session: {sess_name}, Season: {season_info['note']}"

            whale_signal = whale.hunt_turtle(candles) or whale.hunt_ghosts(candles)
            xeno_signal = xeno.hunt(coin, candles)

            if xeno_signal == "ATTACK":
                if trend_status == "REAL_PUMP" or trend_status is None:
                    proposal = {"source": "SNIPER", "side": "BUY", "price": current_price * 0.999, "reason": "MOMENTUM_CONFIRMED"}

            # ASIA FILTER (The Critical Fix)
            if sess_name == "ASIA": whale_signal = None
            
            if whale_signal and trend_status != "REAL_PUMP":
                proposal = {"source": whale_signal['type'], "side": whale_signal['side'], "price": whale_signal['price'], "reason": "REVERSAL_CONFIRMED"}

            if proposal:
                # RISK FIX (0.75)
                raw_margin = base_margin_usd * season_info.get('mult', 1.0) * rules.get('risk_mult', 1.0)
                final_margin = min(raw_margin, max_margin_usd)
                final_size = round(final_margin * target_lev, 2)
                if final_size < 40: final_size = 40

                if oracle.consult(coin, proposal['source'], proposal['price'], context_str):
                    log_msg = f"{coin}: {proposal['source']} ({proposal['reason']}) [${final_margin:.0f}]"
                    print(f">> {log_msg}")
                    EVENT_QUEUE.append(f"[{time.strftime('%H:%M:%S')}] {log_msg}")
                    hands.place_trap(coin, proposal['side'], proposal['price'], final_size)
                    msg.notify_trade(coin, proposal['source'], proposal['price'], final_size)

        ratchet_events = ratchet.manage_positions(hands, clean_positions, FLEET_CONFIG)
        if ratchet_events:
            for event in ratchet_events:
                 EVENT_QUEUE.append(f"[{time.strftime('%H:%M:%S')}] {event}")
                 if "STOP LOSS" in event or "PROFIT" in event:
                     try:
                         parts = event.split(":") 
                         c_name = parts[1].split("(")[0].strip()
                         val = float(event.split("(")[1].split("|")[0].strip())
                         update_stats(val, c_name, event)
                     except: pass
        
        time.sleep(3)

if __name__ == "__main__":
    try: main_loop()
    except: print("\n🦅 LUMA OFFLINE")
