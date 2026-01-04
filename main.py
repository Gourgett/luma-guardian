import time, json, sys, os, warnings
from collections import deque
from datetime import datetime, timezone

warnings.simplefilter("ignore")

# ==============================================================================
#   LUMA SINGULARITY [HYBRID: TERMUX LOGIC + DASHBOARD VAULT]
#   Mode: VOLATILITY SURVIVOR (Railway Final: Fixed Dashboard Header)
# ==============================================================================

# --- DIRECT PATH CONFIGURATION ---
DATA_DIR = "/app/data"
if not os.path.exists(DATA_DIR):
    try:
        os.makedirs(DATA_DIR)
        print(f">> Created persistent directory: {DATA_DIR}")
    except Exception as e:
        print(f"xx FAILED TO CREATE DATA DIR: {e}")

CONFIG_FILE = "server_config.json"
ANCHOR_FILE = os.path.join(DATA_DIR, "equity_anchor.json")
STATS_FILE = os.path.join(DATA_DIR, "stats.json")
BTC_TICKER = "BTC"

# --- CONFIGURATION (VOLATILITY SURVIVOR: 8% STOP + 0.75 SIZE) ---
FLEET_CONFIG = {
    "WIF":    {"type": "MEME",   "lev": 5, "risk_mult": 0.75, "stop_loss": 0.08},
    "DOGE":   {"type": "MEME",   "lev": 5, "risk_mult": 0.75, "stop_loss": 0.08},
    "PENGU":  {"type": "MEME",   "lev": 5, "risk_mult": 0.75, "stop_loss": 0.08},
    "POPCAT": {"type": "MEME",   "lev": 5, "risk_mult": 0.75, "stop_loss": 0.08},
    "BRETT":  {"type": "MEME",   "lev": 5, "risk_mult": 0.75, "stop_loss": 0.08},
    "SPX":    {"type": "MEME",   "lev": 5, "risk_mult": 0.75, "stop_loss": 0.08}
}

# --- FIX 1: HARDCODED ANCHOR TO 412.0 AS REQUESTED ---
STARTING_EQUITY = 412.0
EVENT_QUEUE = deque(maxlen=10)

# --- STATS ENGINE (With Daily Reset) ---
def load_stats():
    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, 'r') as f: 
                data = json.load(f)
        else:
            data = {"last_reset": time.strftime("%Y-%m-%d"), "wins": 0, "losses": 0, "total_pnl": 0.0, "history": []}
    except:
        data = {"last_reset": time.strftime("%Y-%m-%d"), "wins": 0, "losses": 0, "total_pnl": 0.0, "history": []}

    today = time.strftime("%Y-%m-%d")
    last_reset = data.get("last_reset", "")
    
    if last_reset != today:
        data["wins"] = 0
        data["losses"] = 0
        data["total_pnl"] = 0.0
        data["last_reset"] = today
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
    stats["total_pnl"] += pnl
    stats["history"].insert(0, {"date": time.strftime("%Y-%m-%d %H:%M"), "coin": coin, "pnl": pnl, "reason": reason})
    stats["history"] = stats["history"][:100]
    save_stats(stats)
    return stats

def calculate_metric_only(coin, candles, session, regime):
    score = 50.0 
    try:
        if len(candles) >= 4:
            closes = [float(c.get('close') or c.get('c')) for c in candles[-4:]]
            if closes[0] == 0: return 50
            slope = (closes[-1] - closes[0]) / closes[0]
            if slope > 0.02: score += 15  
            elif slope > 0.005: score += 5 
            elif slope < -0.01: score -= 15
        if "LONDON" in session or "NEW_YORK" in session: score += 10
        elif "ASIA" in session: score -= 5 
        if regime == "BULLISH": score += 15
        elif regime == "BEARISH": score -= 20 
    except: pass
    return min(max(int(score), 0), 100)

def load_anchor(current_equity):
    # We ignore the file loading because user requested HARD 412 baseline.
    return 412.0

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
            coin = p.get('coin') or p.get('symbol') or "UNKNOWN"
            if coin == "UNKNOWN": continue
            size = float(p.get('szi') or p.get('size') or 0)
            entry = float(p.get('entryPx') or p.get('entry_price') or 0)
            pnl = float(p.get('unrealizedPnl') or 0)
            if abs(size) < 0.0001: continue
            raw_lev = p.get('leverage', {})
            actual_leverage = raw_lev.get('value', 1) 
            clean_pos.append({"coin": coin, "size": size, "entry": entry, "pnl": pnl, "leverage": actual_leverage})
        except: continue
    return clean_pos

def update_dashboard(equity, cash, status_msg, positions, mode="AGGRESSIVE", secured_list=[], new_event=None):
    global STARTING_EQUITY, EVENT_QUEUE
    try:
        # Use Hardcoded 412.0
        pnl = equity - STARTING_EQUITY

        if new_event:
            t = time.strftime("%H:%M:%S")
            EVENT_QUEUE.append(f"[{t}] {new_event}")

        events_str = "||".join(list(EVENT_QUEUE))
        pos_str = "NO_TRADES"
        risk_report = []
        stats = load_stats()
        total_trades = stats['wins'] + stats['losses']
        win_rate = int((stats['wins'] / total_trades) * 100) if total_trades > 0 else 0

        if positions:
            pos_lines = []
            for p in positions:
                coin = p['coin']
                size = p['size']
                entry = p['entry']
                pnl_val = p['pnl']
                side = "LONG" if size > 0 else "SHORT"
                lev_display = FLEET_CONFIG.get(coin, {}).get('lev', 5)
                margin = (abs(size) * entry) / lev_display if lev_display > 0 else 0
                roe = (pnl_val / margin) * 100 if margin > 0 else 0.0
                is_secured = coin in secured_list
                icon = "🔒" if is_secured else ""
                if side == "LONG": target = entry * (1 + (1/lev_display))
                else: target = entry * (1 - (1/lev_display))
                t_str = f"{target:.6f}" if target < 1.0 else f"{target:.2f}"
                pos_lines.append(f"{coin}|{side}|{pnl_val:.2f}|{roe:.1f}|{icon}|{t_str}")
                status = "SECURED" if is_secured else "RISK ON"
                close_at = entry if is_secured else "Stop Loss"
                risk_report.append(f"{coin}|{side}|{margin:.2f}|{status}|{close_at}")
            pos_str = "::".join(pos_lines)

        if not risk_report: risk_report.append("NO_TRADES")
        data = {
            "equity": f"{equity:.2f}", "cash": f"{cash:.2f}", "pnl": f"{pnl:+.2f}",
            "status": status_msg, "events": events_str, "positions": pos_str,
            "risk_report": "::".join(risk_report), "mode": mode, "updated": time.time(),
            "win_rate": f"{stats['wins']}/{total_trades} ({win_rate}%)"
        }
        
        temp_dash = os.path.join(DATA_DIR, "dashboard_state.tmp")
        with open(temp_dash, "w") as f: json.dump(data, f, ensure_ascii=False)
        os.replace(temp_dash, os.path.join(DATA_DIR, "dashboard_state.json"))
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
    print(">> [2/10] Initializing Organs...")
    vision, hands, xeno, whale, ratchet, msg, chronos, history, oracle, season, predator = Vision(), Hands(), Xenomorph(), SmartMoney(), DeepSea(), Messenger(), Chronos(), Historian(), Oracle(), Seasonality(), Predator()
    print(">> SYSTEM INTEGRITY: 100%")
except Exception as e:
    print(f"xx CRITICAL LOAD ERROR: {e}"); sys.exit()

def main_loop():
    global STARTING_EQUITY
    print("🦅 LUMA SINGULARITY [RESTORED: VOLATILITY SURVIVOR]")
    try:
        update_heartbeat("BOOTING")
        address = os.environ.get("WALLET_ADDRESS")
        if not address:
            try:
                cfg = json.load(open(CONFIG_FILE))
                address = cfg.get('wallet_address')
            except: pass
        if not address: return

        msg.send("info", "🦅 **LUMA ONLINE:** VOLATILITY SURVIVOR (RAILWAY) ACTIVE.")
        last_history_check = 0
        cached_history_data = {'regime': 'NEUTRAL', 'multiplier': 1.0}
        leverage_memory = {}
        score_memory = {}
        last_scan_time = 0
        SCAN_INTERVAL = 10 

        while True:
            update_heartbeat("SCANNING")
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

            # --- FIX 2: FORCE CALCULATION AGAINST 412.0 ---
            current_pnl = equity - STARTING_EQUITY # (Equity - 412)
            current_roe_pct = (current_pnl / STARTING_EQUITY) * 100

            if 1.0 < equity < 10.0:
                 print("xx CRITICAL: EQUITY BELOW $10. HALTING TRADING.")
                 msg.send("errors", "CRITICAL: HARD FLOOR BREACHED.")
                 time.sleep(3600); continue

            # --- MODE SELECTION ---
            risk_mode = "STANDARD"
            if current_roe_pct >= 5.0: risk_mode = "GOD_MODE"
            elif current_roe_pct <= -5.0: risk_mode = "RECOVERY" 
            
            base_margin_usd = equity * 0.11
            max_margin_usd  = equity * 0.165
            
            if risk_mode == "RECOVERY":
                base_margin_usd *= 0.5
                max_margin_usd *= 0.5

            secured = ratchet.secured_coins
            
            # --- FIX 3: RESTORE BLUEPRINT STATUS MESSAGE ---
            # This ensures the dashboard header shows Mode and ROE vs 412, not "Scanning..."
            status_msg = f"Mode:{risk_mode} (ROE:{current_roe_pct:.2f}%) Cap:${max_margin_usd:.0f}"
            
            update_dashboard(equity, cash, status_msg, clean_positions, risk_mode, secured)

            active_coins = [p['coin'] for p in clean_positions]

            if time.time() - last_scan_time > SCAN_INTERVAL:
                last_scan_time = time.time()
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
                            if abs(current_price - order_price) / order_price > 0.005: hands.cancel_all_orders(coin)
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
                            msg_txt = f"OPEN {coin} ({proposal['source']}) ${final_margin_usd:.0f} Lev:{target_leverage}x [Score:{metric_score}]"
                            if hands.place_trap(coin, proposal['side'], proposal['price'], final_size):
                                msg.notify_trade(coin, proposal['source'], proposal['price'], final_size)
                                update_dashboard(equity, cash, status_msg, clean_positions, risk_mode, secured, new_event=msg_txt)

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
                     update_dashboard(equity, cash, status_msg, clean_positions, risk_mode, secured, new_event=event)
            time.sleep(3)
    except Exception as e:
        print(f"xx CRITICAL: {e}")
        msg.send("errors", f"CRASH: {e}")

if __name__ == "__main__":
    try: main_loop()
    except: print("\n🦅 LUMA OFFLINE")
