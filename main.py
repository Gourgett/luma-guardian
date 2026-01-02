import time, json, sys, os, warnings
from collections import deque
from datetime import datetime, timezone

warnings.simplefilter("ignore")

# ==============================================================================
#  LUMA SINGULARITY [ORDER RETENTION FIX]
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
SCORES_FILE = os.path.join(DATA_DIR, "active_scores.json")
BTC_TICKER = "BTC"

# --- CONFIGURATION (Standard) ---
FLEET_CONFIG = {
    "WIF":    {"type": "MEME", "lev": 5, "risk_mult": 1.0, "stop_loss": 0.04},
    "DOGE":   {"type": "MEME", "lev": 5, "risk_mult": 1.0, "stop_loss": 0.04},
    "PENGU":  {"type": "MEME", "lev": 5, "risk_mult": 1.0, "stop_loss": 0.04},
    "POPCAT": {"type": "MEME", "lev": 5, "risk_mult": 1.0, "stop_loss": 0.04},
    "BRETT":  {"type": "MEME", "lev": 5, "risk_mult": 1.0, "stop_loss": 0.04},
    "SPX":    {"type": "MEME", "lev": 5, "risk_mult": 1.0, "stop_loss": 0.04}
}

STARTING_EQUITY = 0.0

# --- HISTORY FIX (Prevents Data Deletion) ---
def load_history():
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return deque(data, maxlen=60)
        return deque(maxlen=60)
    except: return deque(maxlen=60)

def save_history(new_event=None):
    try:
        current_data = []
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                try: current_data = json.load(f)
                except: current_data = []
        
        if not isinstance(current_data, list): current_data = []
        
        if new_event:
            current_data.append(new_event)
            
        if len(current_data) > 60:
            current_data = current_data[-60:]
            
        with open(HISTORY_FILE, 'w') as f:
            json.dump(current_data, f)
            f.flush(); os.fsync(f.fileno())
            
        return deque(current_data, maxlen=60)
    except Exception as e: 
        print(f"xx HISTORY SAVE FAILED: {e}")
        return deque(maxlen=60)

TRADE_HISTORY = load_history()
LIVE_ACTIVITY = "System Initializing..."

# --- SCORE PERSISTENCE ---
TRADE_SCORES = {}
def load_scores():
    global TRADE_SCORES
    try:
        if os.path.exists(SCORES_FILE):
            with open(SCORES_FILE, 'r') as f:
                TRADE_SCORES = json.load(f)
    except: TRADE_SCORES = {}

def save_scores():
    try:
        with open(SCORES_FILE, 'w') as f:
            json.dump(TRADE_SCORES, f)
    except: pass

load_scores()

# --- VOLUME MEMORY ---
def load_volume():
    default_stats = {"wins": 0, "total": 0, "last_reset_day": datetime.now(timezone.utc).day}
    try:
        if os.path.exists(VOLUME_FILE):
            with open(VOLUME_FILE, 'r') as f:
                data = json.load(f)
                if data.get("last_reset_day") != datetime.now(timezone.utc).day:
                    return default_stats
                return data
        return default_stats
    except: return default_stats

def save_volume():
    global DAILY_STATS
    try:
        with open(VOLUME_FILE, 'w') as f:
            json.dump(DAILY_STATS, f)
            f.flush(); os.fsync(f.fileno())
    except: pass

DAILY_STATS = load_volume()

def load_anchor(current_equity):
    try:
        if os.path.exists(ANCHOR_FILE):
            with open(ANCHOR_FILE, 'r') as f:
                data = json.load(f)
                return float(data.get("start_equity", current_equity))
        else:
            with open(ANCHOR_FILE, 'w') as f:
                json.dump({"start_equity": current_equity}, f)
            return current_equity
    except: return current_equity

def update_heartbeat(status="ALIVE"):
    try:
        temp_file = "heartbeat.tmp"
        with open(temp_file, "w") as f:
            json.dump({"last_beat": time.time(), "status": status}, f)
        os.replace(temp_file, "heartbeat.json")
    except: pass

def check_daily_reset():
    global DAILY_STATS
    current_day = datetime.now(timezone.utc).day
    if current_day != DAILY_STATS["last_reset_day"]:
        DAILY_STATS = {"wins": 0, "total": 0, "last_reset_day": current_day}
        save_volume(); return True
    return False

def update_stats(pnl_value):
    global DAILY_STATS
    DAILY_STATS["total"] += 1
    if pnl_value > 0: DAILY_STATS["wins"] += 1
    save_volume()

def normalize_positions(raw_positions):
    clean_pos = []
    if not raw_positions: return []
    for item in raw_positions:
        try:
            p = item['position'] if 'position' in item else item
            coin = p.get('coin') or p.get('symbol') or "UNKNOWN"
            if coin == "UNKNOWN": continue
            
            size = float(p.get('szi') or p.get('size') or 0)
            if abs(size) < 0.0001: continue 

            entry = float(p.get('entryPx') or p.get('entry_price') or 0)
            pnl = float(p.get('unrealizedPnl') or 0)
            
            clean_pos.append({"coin": coin, "size": size, "entry": entry, "pnl": pnl})
        except: continue
    return clean_pos

def update_dashboard(equity, cash, status_msg, positions, mode="AGGRESSIVE", secured_list=[], trade_event=None, activity_event=None, session="N/A"):
    global STARTING_EQUITY, TRADE_HISTORY, LIVE_ACTIVITY, DAILY_STATS
    try:
        if STARTING_EQUITY == 0.0 and equity > 0: STARTING_EQUITY = load_anchor(equity)
        pnl = equity - STARTING_EQUITY if STARTING_EQUITY > 0 else 0.0

        if trade_event:
            t_str = time.strftime("[%d-%b %H:%M:%S]")
            final_msg = f"{t_str} {trade_event}" if not trade_event.startswith("[") else trade_event
            save_history(final_msg)
        
        # DASHBOARD FIX: Read from Disk to prevent vanishing logs
        DISPLAY_HISTORY = load_history()

        if activity_event: LIVE_ACTIVITY = f">> {activity_event}"

        history_str = "||".join(list(DISPLAY_HISTORY))
        pos_str = "NO_TRADES"
        risk_report = []

        win_rate = int((DAILY_STATS["wins"] / DAILY_STATS["total"]) * 100) if DAILY_STATS["total"] > 0 else 0
        daily_stats_str = f"{DAILY_STATS['wins']}/{DAILY_STATS['total']} ({win_rate}%)"

        if positions:
            pos_lines = []
            for p in positions:
                coin, size, entry, pnl_val = p['coin'], p['size'], p['entry'], p['pnl']
                side = "LONG" if size > 0 else "SHORT"
                lev_display = FLEET_CONFIG.get(coin, {}).get('lev', 10)
                if mode == "GOD_MODE" and FLEET_CONFIG.get(coin, {}).get('type') == "MEME": lev_display = 10
                
                margin = (abs(size) * entry) / lev_display
                roe = (pnl_val / margin) * 100 if margin > 0 else 0.0
                icon = "🔒" if coin in secured_list else ""
                target = entry * (1 + (1/lev_display)) if side == "LONG" else entry * (1 - (1/lev_display))
                t_str_px = f"{target:.6f}" if target < 1.0 else f"{target:.2f}"
                
                score_display = f"{int(TRADE_SCORES.get(coin, 50))}%"
                pos_lines.append(f"{coin}|{side}|{pnl_val:.2f}|{roe:.1f}|{icon}|{t_str_px}|{score_display}")
                
                risk_report.append(f"{coin}|{side}|{margin:.2f}|{'SECURED' if coin in secured_list else 'RISK ON'}|{entry if coin in secured_list else 'Stop Loss'}")
            pos_str = "::".join(pos_lines)

        if not risk_report: risk_report.append("NO_TRADES")

        data = {
            "equity": f"{equity:.2f}", "cash": f"{cash:.2f}", "pnl": f"{pnl:+.2f}",
            "status": status_msg, "session": session, "win_rate": daily_stats_str,
            "trade_history": history_str, "live_activity": LIVE_ACTIVITY,
            "positions": pos_str, "risk_report": "::".join(risk_report),
            "mode": mode, "updated": time.time()
        }
        temp_dash = "dashboard_state.tmp"
        with open(temp_dash, "w") as f: json.dump(data, f, ensure_ascii=False)
        os.replace(temp_dash, "dashboard_state.json")
    except: pass

# --- LOGIC SCORE ENGINE ---
def calculate_logic_score(coin, candles, session, regime):
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

        if len(candles) >= 2:
            curr_rng = float(candles[-1]['high']) - float(candles[-1]['low'])
            prev_rng = float(candles[-2]['high']) - float(candles[-2]['low'])
            if prev_rng > 0 and curr_rng > prev_rng * 1.5: score += 5
            
    except: pass
    return min(max(int(score), 0), 100)

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
    print("🦅 LUMA SINGULARITY [RESTORED]")
    try:
        update_heartbeat("BOOTING")
        update_dashboard(0, 0, "SYSTEM BOOTING...", [], "STANDARD", [], activity_event="Connecting...")
        
        address = os.environ.get("WALLET_ADDRESS")
        if not address:
            try:
                cfg = json.load(open(CONFIG_FILE))
                address = cfg.get('wallet_address')
            except: pass
        
        if not address: return

        msg.send("info", "🦅 **LUMA ONLINE:** SYSTEM RESTORED.")
        last_history_check = 0; cached_history_data = {'regime': 'NEUTRAL', 'multiplier': 1.0}; leverage_memory = {}
        
        known_positions = {}
        # Simple throttle memory to prevent machine-gunning
        last_action_time = {}

        while True:
            update_heartbeat("ALIVE")
            session_data = chronos.get_session(); session_name = session_data['name']
            if check_daily_reset():
                update_dashboard(0, 0, "DAILY RESET", [], "STANDARD", [], trade_event="--- DAILY STATS RESET ---", session=session_name)

            if time.time() - last_history_check > 14400:
                try:
                    btc_daily = vision.get_candles(BTC_TICKER, "1d")
                    if btc_daily: cached_history_data = history.check_regime(btc_daily); last_history_check = time.time()
                except: pass
            
            regime = cached_history_data.get('regime', 'NEUTRAL')

            equity, cash, clean_positions, open_orders = 0.0, 0.0, [], []
            api_success = False
            try:
                user_state = vision.get_user_state(address)
                if user_state:
                    equity = float(user_state.get('marginSummary', {}).get('accountValue', 0))
                    cash = float(user_state.get('withdrawable', 0))
                    clean_positions = normalize_positions(user_state.get('assetPositions', []))
                    open_orders = user_state.get('openOrders', [])
                    api_success = True
            except: pass
            
            # --- DASHBOARD FIX: No API = No Update (Prevents vanishing) ---
            if not api_success:
                 time.sleep(1); continue

            if STARTING_EQUITY == 0.0 and equity > 0: STARTING_EQUITY = load_anchor(equity)
            current_roe_pct = ((equity - STARTING_EQUITY) / (STARTING_EQUITY if STARTING_EQUITY > 0 else 1.0)) * 100

            if 1.0 < equity < 300.0:
                msg.send("errors", "CRITICAL: EQUITY < $300."); time.sleep(3600); continue

            risk_mode, titan_active, shield_active = "STANDARD", current_roe_pct >= 12.0, current_roe_pct <= -10.0
            status_msg = f"🛡️ SHIELD ACTIVE | ROE:{current_roe_pct:.2f}%" if shield_active else f"Mode:STANDARD (ROE:{current_roe_pct:.2f}%)"
            if shield_active: risk_mode = "RECOVERY"
            elif not shield_active:
                if equity < 412.0: risk_mode = "RECOVERY"
                elif current_roe_pct >= 5.0: risk_mode = "GOD_MODE"

            current_coins = [p['coin'] for p in clean_positions]
            
            # --- MANUAL CLOSE DETECTION FIX ---
            manual_close_event = None
            for k_coin in list(known_positions.keys()):
                if k_coin not in current_coins:
                    manual_close_event = f"🕵️ DETECTED CLOSE: {k_coin}"
            known_positions = {p['coin']: p for p in clean_positions}

            update_dashboard(equity, cash, status_msg, clean_positions, risk_mode, ratchet.secured_coins, trade_event=manual_close_event, session=session_name)
            
            print(f">> [{time.strftime('%H:%M:%S')}] {status_msg}", end='\r')

            active_coins = [p['coin'] for p in clean_positions]
            
            # --- WALLET EDGING CAP (70% / 6) ---
            wallet_edging_cap = (equity * 0.70) / 6

            for coin, rules in FLEET_CONFIG.items():
                update_heartbeat("SCANNING")
                target_lev = 10 if risk_mode == "GOD_MODE" and rules['type'] == "MEME" else (5 if risk_mode == "RECOVERY" or shield_active else rules['lev'])

                if coin not in active_coins and leverage_memory.get(coin) != int(target_lev):
                    try: hands.set_leverage_all([coin], leverage=int(target_lev)); leverage_memory[coin] = int(target_lev)
                    except: pass

                if ratchet.check_trauma(hands, coin) or next((p for p in clean_positions if p['coin'] == coin), None): continue
                
                # --- ANTI-STACKING (SIMPLE THROTTLE) ---
                if time.time() - last_action_time.get(coin, 0) < 30:
                    continue

                try: candles = vision.get_candles(coin, "1h")
                except: candles = []
                if not candles: continue
                current_price = float(candles[-1].get('close') or 0)
                update_dashboard(equity, cash, status_msg, clean_positions, risk_mode, ratchet.secured_coins, session=session_name, activity_event=f"Scanning {coin}...")

                # --- 🛑 THE FIX: ORDER RETENTION CHECK 🛑 ---
                pending = next((o for o in open_orders if o.get('coin') == coin), None)
                if pending:
                    try:
                        order_price = float(pending.get('limitPx') or 0)
                        # IF ORDER IS BAD (MOVED): Cancel & Continue loop (to replace)
                        if abs(current_price - order_price) / order_price > 0.005:
                            hands.cancel_all_orders(coin)
                            # Let it fall through to place new order
                        else:
                            # IF ORDER IS GOOD: STOP HERE! DO NOT PLACE A NEW ONE.
                            # This 'continue' was missing, causing the bot to delete good orders.
                            update_dashboard(equity, cash, status_msg, clean_positions, risk_mode, ratchet.secured_coins, session=session_name, activity_event=f"Holding Trap {coin}...")
                            continue 
                    except: continue

                proposal, trend = None, predator.analyze_divergence(candles, coin)
                whale_sig, xeno_sig = whale.hunt_turtle(candles) or whale.hunt_ghosts(candles), xeno.hunt(coin, candles)

                if xeno_sig == "ATTACK" and (not (titan_active or shield_active) or trend == "REAL_PUMP"):
                    proposal = {"source": "SNIPER", "side": "BUY", "price": current_price * 0.999}
                if whale_sig and trend != "REAL_PUMP":
                    proposal = {"source": whale_sig['type'], "side": whale_sig['side'], "price": whale_sig['price']}

                if proposal:
                    logic_score = calculate_logic_score(coin, candles, session_name, regime)
                    
                    # --- EXECUTION LOGIC (SIMPLE) ---
                    base_size = equity * 0.11 * season.get_multiplier(rules['type']).get('mult', 1.0)
                    final_margin_usd = min(base_size, wallet_edging_cap)
                    final_margin_usd = max(final_margin_usd, 10.0)
                    
                    final_sz_notional = final_margin_usd * target_lev
                    final_sz = round(final_sz_notional, 2)

                    if oracle.consult(coin, proposal['source'], proposal['price'], f"Session: {session_name}"):
                        msg_txt = f"OPEN {coin} ({proposal['source']}) Margin:${final_margin_usd:.0f} [Score:{logic_score}]"
                        
                        hands.place_trap(coin, proposal['side'], proposal['price'], final_sz)
                        
                        last_action_time[coin] = time.time()
                        
                        msg.notify_trade(coin, proposal['source'], proposal['price'], final_sz)
                        TRADE_SCORES[coin] = logic_score
                        save_scores()
                        update_dashboard(equity, cash, status_msg, clean_positions, risk_mode, ratchet.secured_coins, trade_event=msg_txt, session=session_name)
            
            ratchet_events = ratchet.manage_positions(hands, clean_positions, FLEET_CONFIG)
            
            if ratchet_events:
                for event in ratchet_events:
                    if any(x in event for x in ["PROFIT", "+", "WIN", "GAIN"]): update_stats(1)
                    elif any(x in event for x in ["LOSS", "-", "LOSE"]): update_stats(-1)
                    update_dashboard(equity, cash, status_msg, clean_positions, risk_mode, ratchet.secured_coins, trade_event=event, session=session_name)
            
            time.sleep(3)

    except Exception as e:
        print(f"xx CRITICAL: {e}")
        msg.send("errors", f"CRASH: {e}")

if __name__ == "__main__":
    try: main_loop()
    except: print("\n🦅 LUMA OFFLINE")
