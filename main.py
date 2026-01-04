import time, json, sys, os, warnings
from collections import deque
from datetime import datetime, timezone

warnings.simplefilter("ignore")

# ==============================================================================
#   LUMA SINGULARITY [HYBRID: RAILWAY MASTER]
#   Mode: VOLATILITY SURVIVOR (Final: True Heartbeat)
# ==============================================================================

DATA_DIR = "/app/data"
if not os.path.exists(DATA_DIR):
    try: os.makedirs(DATA_DIR)
    except: pass

CONFIG_FILE = "server_config.json"
ANCHOR_FILE = os.path.join(DATA_DIR, "equity_anchor.json")
STATS_FILE = os.path.join(DATA_DIR, "stats.json")
BTC_TICKER = "BTC"

FLEET_CONFIG = {
    "WIF":    {"type": "MEME",   "lev": 5, "risk_mult": 0.75, "stop_loss": 0.08},
    "DOGE":   {"type": "MEME",   "lev": 5, "risk_mult": 0.75, "stop_loss": 0.08},
    "PENGU":  {"type": "MEME",   "lev": 5, "risk_mult": 0.75, "stop_loss": 0.08},
    "POPCAT": {"type": "MEME",   "lev": 5, "risk_mult": 0.75, "stop_loss": 0.08},
    "BRETT":  {"type": "MEME",   "lev": 5, "risk_mult": 0.75, "stop_loss": 0.08},
    "SPX":    {"type": "MEME",   "lev": 5, "risk_mult": 0.75, "stop_loss": 0.08}
}

STARTING_EQUITY = 412.0
# LIMIT LOGS TO 6 LINES AS REQUESTED
EVENT_QUEUE = deque(maxlen=6) 

# --- GLOBAL STATE ---
DASH_STATE = {
    "equity": 0.0, "cash": 0.0, "pnl": 0.0,
    "positions": [], "secured": [], 
    "financial_header": "Initializing...",
    "activity_header": ">> Starting System..."
}

def load_stats():
    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, 'r') as f: data = json.load(f)
        else: data = {"last_reset": time.strftime("%Y-%m-%d"), "wins": 0, "losses": 0}
    except: data = {"last_reset": time.strftime("%Y-%m-%d"), "wins": 0, "losses": 0}
    
    today = time.strftime("%Y-%m-%d")
    if data.get("last_reset") != today:
        data = {"last_reset": today, "wins": 0, "losses": 0, "total_pnl": 0.0, "history": data.get("history", [])}
        save_stats(data)
    return data

def save_stats(stats):
    try:
        with open(STATS_FILE, 'w') as f: json.dump(stats, f, indent=2)
    except: pass

def update_stats(pnl, coin, reason):
    stats = load_stats()
    if pnl > 0: stats["wins"] += 1
    else: stats["losses"] += 1
    stats["total_pnl"] = stats.get("total_pnl", 0.0) + pnl
    stats["history"].insert(0, {"date": time.strftime("%Y-%m-%d %H:%M"), "coin": coin, "pnl": pnl, "reason": reason})
    stats["history"] = stats["history"][:100]
    save_stats(stats)
    return stats

def calculate_metric_only(coin, candles, session, regime):
    score = 50.0 
    try:
        closes = [float(c.get('close') or c.get('c')) for c in candles[-4:]]
        slope = (closes[-1] - closes[0]) / closes[0]
        if slope > 0.02: score += 15  
        elif slope > 0.005: score += 5 
        elif slope < -0.01: score -= 15
        if "LONDON" in session or "NEW_YORK" in session: score += 10
        elif regime == "BULLISH": score += 15
        elif regime == "BEARISH": score -= 20 
    except: pass
    return min(max(int(score), 0), 100)

def update_heartbeat(status="ALIVE"):
    try:
        temp_file = os.path.join(DATA_DIR, "heartbeat.tmp")
        with open(temp_file, "w") as f: json.dump({"last_beat": time.time(), "status": status}, f)
        os.replace(temp_file, os.path.join(DATA_DIR, "heartbeat.json"))
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

# --- LOGGING ENGINE (THE LOUD BRAIN) ---
def log(text):
    global EVENT_QUEUE
    # 1. Print to Railway Console
    print(f">> {text}")
    # 2. Push to Dashboard Ticker
    t = time.strftime("%H:%M:%S")
    EVENT_QUEUE.append(f"[{t}] {text}")
    # 3. Trigger Sync
    sync_dashboard()

def sync_dashboard():
    global DASH_STATE, EVENT_QUEUE, FLEET_CONFIG
    try:
        pos_str = "NO_TRADES"
        risk_report = []
        if DASH_STATE["positions"]:
            pos_lines = []
            for p in DASH_STATE["positions"]:
                coin = p['coin']
                size = p['size']
                entry = p['entry']
                pnl_val = p['pnl']
                side = "LONG" if size > 0 else "SHORT"
                lev_display = FLEET_CONFIG.get(coin, {}).get('lev', 5)
                margin = (abs(size) * entry) / lev_display if lev_display > 0 else 0
                roe = (pnl_val / margin) * 100 if margin > 0 else 0.0
                is_secured = coin in DASH_STATE["secured"]
                icon = "🔒" if is_secured else ""
                
                if side == "LONG": target = entry * (1 + (1/lev_display))
                else: target = entry * (1 - (1/lev_display))
                t_str = f"{target:.6f}" if target < 1.0 else f"{target:.2f}"
                
                pos_lines.append(f"{coin}|{side}|{pnl_val:.2f}|{roe:.1f}|{icon}|{t_str}")
                status_txt = "SECURED" if is_secured else "RISK ON"
                close_at = entry if is_secured else "Stop Loss"
                risk_report.append(f"{coin}|{side}|{margin:.2f}|{status_txt}|{close_at}")
            pos_str = "::".join(pos_lines)

        if not risk_report: risk_report.append("NO_TRADES")
        stats = load_stats()
        total = stats.get('wins', 0) + stats.get('losses', 0)
        wr = int((stats.get('wins', 0) / total) * 100) if total > 0 else 0

        data = {
            "equity": f"{DASH_STATE['equity']:.2f}",
            "cash": f"{DASH_STATE['cash']:.2f}",
            "pnl": f"{DASH_STATE['pnl']:+.2f}",
            "financial_header": DASH_STATE['financial_header'], 
            "activity_header": DASH_STATE['activity_header'],
            "events": "||".join(list(EVENT_QUEUE)), 
            "positions": pos_str,
            "risk_report": "::".join(risk_report),
            "updated": time.time(),
            "win_rate": f"{stats.get('wins', 0)}/{total} ({wr}%)"
        }

        temp_dash = os.path.join(DATA_DIR, "dashboard_state.tmp")
        with open(temp_dash, "w") as f: json.dump(data, f, ensure_ascii=False)
        os.replace(temp_dash, os.path.join(DATA_DIR, "dashboard_state.json"))
    except Exception as e:
        print(f"xx SYNC ERROR: {e}")

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
    
    # Initialize Log with "System Ready" so the box isn't empty
    log("System Initialized. Waiting for market data...")
    
    vision, hands, xeno, whale, ratchet, msg, chronos, history, oracle, season, predator = Vision(), Hands(), Xenomorph(), SmartMoney(), DeepSea(), Messenger(), Chronos(), Historian(), Oracle(), Seasonality(), Predator()
except Exception as e:
    print(f"xx CRITICAL LOAD ERROR: {e}"); sys.exit()

def main_loop():
    global STARTING_EQUITY, DASH_STATE
    log("🦅 LUMA ONLINE: VOLATILITY SURVIVOR")
    
    address = os.environ.get("WALLET_ADDRESS")
    if not address:
        try:
            cfg = json.load(open(CONFIG_FILE))
            address = cfg.get('wallet_address')
        except: pass
    if not address: return

    last_history_check = 0
    cached_history_data = {'regime': 'NEUTRAL', 'multiplier': 1.0}
    leverage_memory = {}
    score_memory = {}
    last_scan_time = 0
    SCAN_INTERVAL = 15 # Check every 15s to allow logs to be read

    while True:
        update_heartbeat("ALIVE")
        session_data = chronos.get_session()

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

        current_pnl = equity - STARTING_EQUITY 
        current_roe_pct = (current_pnl / STARTING_EQUITY) * 100

        if 1.0 < equity < 10.0:
             log("CRITICAL: HARD FLOOR BREACHED. HALTING.")
             time.sleep(3600); continue

        # --- MODE LOGIC ---
        risk_mode = "STANDARD"
        if current_roe_pct >= 5.0: risk_mode = "GOD_MODE"
        elif current_roe_pct < 0.0: risk_mode = "RECOVERY"
        
        base_margin_usd = equity * 0.11
        max_margin_usd  = equity * 0.165
        if risk_mode == "RECOVERY":
            base_margin_usd *= 0.5
            max_margin_usd *= 0.5
        
        # --- UPDATE STATE ---
        DASH_STATE["equity"] = equity
        DASH_STATE["cash"] = cash
        DASH_STATE["pnl"] = current_pnl
        DASH_STATE["positions"] = clean_positions
        DASH_STATE["secured"] = ratchet.secured_coins
        
        # TOP HEADER: Financials
        DASH_STATE["financial_header"] = f"MODE: {risk_mode} | ROE: {current_roe_pct:.2f}% | CAP: ${max_margin_usd:.0f}"
        
        # CYAN HEADER: Activity + Session (RESTORED)
        session_name = session_data.get('name', 'GLOBAL')
        DASH_STATE["activity_header"] = f">> Scanning Markets... ({session_name})"

        active_coins = [p['coin'] for p in clean_positions]

        # --- SCANNING LOOP ---
        if time.time() - last_scan_time > SCAN_INTERVAL:
            last_scan_time = time.time()
            
            # Broadcast "Thinking" log so the ticker isn't dead
            log(f"Scanning Fleet... ({len(FLEET_CONFIG)} Coins)")

            for coin, rules in FLEET_CONFIG.items():
                target_leverage = rules['lev']
                if risk_mode == "GOD_MODE" and rules['type'] == "MEME": target_leverage = 10

                if coin not in active_coins:
                     if leverage_memory.get(coin) != target_leverage:
                         try: 
                             hands.set_leverage_all([coin], leverage=int(target_leverage))
                             leverage_memory[coin] = int(target_leverage)
                         except: pass

                if ratchet.check_trauma(hands, coin): continue
                if next((p for p in clean_positions if p['coin'] == coin), None): continue

                try: candles = vision.get_candles(coin, "1h")
                except: candles = []
                if not candles: continue
                current_price = float(candles[-1].get('close') or 0)
                if current_price == 0: continue

                regime = cached_history_data.get('regime', 'NEUTRAL')
                metric_score = calculate_metric_only(coin, candles, session_data['name'], regime)

                pending = next((o for o in open_orders if o.get('coin') == coin), None)
                if pending:
                    try:
                        order_price = float(pending.get('limitPx') or 0)
                        if abs(current_price - order_price) / order_price > 0.005: 
                            log(f"🧹 SWEEPING: {coin} moved out of range")
                            hands.cancel_all_orders(coin)
                    except: pass
                    continue

                proposal = None
                trend_status = predator.analyze_divergence(candles, coin)
                season_info = season.get_multiplier(rules['type'])
                season_mult = season_info.get('mult', 1.0)
                context_str = f"Session: {session_data.get('name')}, Season: {season_info.get('note')}"

                whale_signal = whale.hunt_turtle(candles) or whale.hunt_ghosts(candles)
                xeno_signal = xeno.hunt(coin, candles)

                if xeno_signal == "ATTACK":
                    if rules['type'] == "OFF": continue
                    if trend_status == "REAL_PUMP" or trend_status is None:
                         proposal = {"source": "SNIPER", "side": "BUY", "price": current_price * 0.999, "reason": "MOMENTUM_CONFIRMED"}

                if whale_signal and not proposal:
                    if trend_status != "REAL_PUMP":
                         proposal = {"source": whale_signal['type'], "side": whale_signal['side'], "price": whale_signal['price'], "reason": "REVERSAL_CONFIRMED"}

                if proposal:
                    raw_margin = base_margin_usd * season_mult * rules.get('risk_mult', 1.0)
                    final_margin_usd = min(raw_margin, max_margin_usd)
                    final_size = round(final_margin_usd * target_leverage, 2)
                    if final_size < 10: final_size = 10 

                    if oracle.consult(coin, proposal['source'], proposal['price'], context_str):
                        score_memory[coin] = metric_score
                        log(f"🪤 TRAP: {coin} @ ${proposal['price']:.4f} (Size:{final_size})")
                        if hands.place_trap(coin, proposal['side'], proposal['price'], final_size):
                            msg.notify_trade(coin, proposal['source'], proposal['price'], final_size)

        # --- RATCHET & LOGGING ---
        ratchet_events = ratchet.manage_positions(hands, clean_positions, FLEET_CONFIG)
        if ratchet_events:
            for event in ratchet_events:
                 try:
                     parts = event.split(":") 
                     if len(parts) > 1:
                         coin_name = parts[1].strip().split("(")[0].strip()
                         score = score_memory.get(coin_name, "N/A")
                         event = f"{event[:-1]} | {score}% conf)" 
                 except: pass
                 
                 # PARSE PNL FOR VAULT
                 if "STOP LOSS" in event or "PROFIT" in event:
                     try:
                         clean_event = event.replace("💰 ", "")
                         parts = clean_event.split(":") 
                         data_part = parts[1].strip() 
                         coin_name = data_part.split("(")[0].strip() 
                         numbers = data_part.split("(")[1] 
                         pnl_val = float(numbers.split("|")[0].strip()) 
                         update_stats(pnl_val, coin_name, clean_event)
                     except: pass
                 
                 # PUSH TO TICKER
                 log(event)
        
        # Always sync state at end of loop
        sync_dashboard()
        time.sleep(3)

if __name__ == "__main__":
    try: main_loop()
    except: print("\n🦅 LUMA OFFLINE")
