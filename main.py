import time
import json
import sys
import os
import warnings
from collections import deque
from datetime import datetime, timezone

warnings.simplefilter("ignore")

# ==============================================================================
#  LUMA SINGULARITY [STANDARD OPERATION: PERSISTENT MEMORY]
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
# NEW: Persistent Files
HISTORY_FILE = os.path.join(DATA_DIR, "trade_logs.json")
SCORES_FILE = os.path.join(DATA_DIR, "active_scores.json")
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

# --- SEPARATED LOGGING SYSTEM (PERSISTENT UPGRADE) ---
def load_history():
    """Restores the last 60 logs from disk"""
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                data = json.load(f)
                return deque(data, maxlen=60)
        return deque(maxlen=60)
    except: return deque(maxlen=60)

def save_history(history_deque):
    """Saves logs to disk to prevent dashboard loss"""
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(list(history_deque), f)
    except: pass

TRADE_HISTORY = load_history()
LIVE_ACTIVITY = "System Initializing..."

# --- SCORE PERSISTENCE (For Sizing) ---
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

# --- PERSISTENT VOLUME MEMORY ---
def load_volume():
    """Restores daily stats from disk on restart"""
    default_stats = {
        "wins": 0, 
        "total": 0, 
        "last_reset_day": datetime.now(timezone.utc).day
    }
    try:
        if os.path.exists(VOLUME_FILE):
            with open(VOLUME_FILE, 'r') as f:
                data = json.load(f)
                current_day = datetime.now(timezone.utc).day
                if data.get("last_reset_day") != current_day:
                    return default_stats
                return data
        return default_stats
    except:
        return default_stats

def save_volume():
    """Saves daily stats to disk instantly"""
    global DAILY_STATS
    try:
        with open(VOLUME_FILE, 'w') as f:
            json.dump(DAILY_STATS, f)
            f.flush()
            os.fsync(f.fileno())
    except: pass

DAILY_STATS = load_volume() # <--- LOAD ON STARTUP

def load_anchor(current_equity):
    """Loads the anchor. If missing, sets it to current equity."""
    try:
        if os.path.exists(ANCHOR_FILE):
            with open(ANCHOR_FILE, 'r') as f:
                data = json.load(f)
                return float(data.get("start_equity", current_equity))
        else:
            with open(ANCHOR_FILE, 'w') as f:
                json.dump({"start_equity": current_equity}, f)
            return current_equity
    except:
        return current_equity

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
        save_volume() # <--- SAVE RESET
        return True
    return False

def update_stats(pnl_value):
    global DAILY_STATS
    DAILY_STATS["total"] += 1
    if pnl_value > 0:
        DAILY_STATS["wins"] += 1
    save_volume() # <--- SAVE UPDATE

def normalize_positions(raw_positions):
    clean_pos = []
    if not raw_positions: return []
    for item in raw_positions:
        try:
            p = item['position'] if 'position' in item else item
            coin = p.get('coin') or p.get('symbol') or p.get('asset') or "UNKNOWN"
            if coin == "UNKNOWN": continue
            size = float(p.get('szi') or p.get('size') or p.get('position') or 0)
            entry = float(p.get('entryPx') or p.get('entry_price') or 0)
            pnl = float(p.get('unrealizedPnl') or p.get('unrealized_pnl') or 0)
            if size == 0: continue
            clean_pos.append({"coin": coin, "size": size, "entry": entry, "pnl": pnl})
        except: continue
    return clean_pos

def update_dashboard(equity, cash, status_msg, positions, mode="AGGRESSIVE", secured_list=[], trade_event=None, activity_event=None, session="N/A"):
    global STARTING_EQUITY, TRADE_HISTORY, LIVE_ACTIVITY, DAILY_STATS
    try:
        if STARTING_EQUITY == 0.0 and equity > 0:
            STARTING_EQUITY = load_anchor(equity)
        
        pnl = equity - STARTING_EQUITY if STARTING_EQUITY > 0 else 0.0

        if trade_event:
            # UPDATED: Timestamp with Date
            t_str = time.strftime("[%d-%b %H:%M:%S]")
            if not trade_event.startswith("["):
                final_msg = f"{t_str} {trade_event}"
            else:
                final_msg = trade_event
            TRADE_HISTORY.append(final_msg)
            save_history(TRADE_HISTORY) # <--- SAVE TO DISK
        
        if activity_event:
            LIVE_ACTIVITY = f">> {activity_event}"

        history_str = "||".join(list(TRADE_HISTORY))
        pos_str = "NO_TRADES"
        risk_report = []

        win_rate = 0
        if DAILY_STATS["total"] > 0:
            win_rate = int((DAILY_STATS["wins"] / DAILY_STATS["total"]) * 100)
        daily_stats_str = f"{DAILY_STATS['wins']}/{DAILY_STATS['total']} ({win_rate}%)"

        if positions:
            pos_lines = []
            for p in positions:
                coin = p['coin']
                size = p['size']
                entry = p['entry']
                pnl_val = p['pnl']
                side = "LONG" if size > 0 else "SHORT"

                lev_display = FLEET_CONFIG.get(coin, {}).get('lev', 10)
                if mode == "GOD_MODE" and FLEET_CONFIG.get(coin, {}).get('type') == "MEME":
                    lev_display = 10
                
                margin = (abs(size) * entry) / lev_display
                roe = 0.0
                if margin > 0: roe = (pnl_val / margin) * 100

                is_secured = coin in secured_list
                icon = "🔒" if is_secured else ""

                if side == "LONG": target = entry * (1 + (1/lev_display))
                else: target = entry * (1 - (1/lev_display))

                if target < 1.0: t_str = f"{target:.6f}"
                else: t_str = f"{target:.2f}"

                # Add Logic Score to display
                score_display = f"{int(TRADE_SCORES.get(coin, 50))}%"
                pos_lines.append(f"{coin}|{side}|{pnl_val:.2f}|{roe:.1f}|{icon}|{t_str}|{score_display}")

                status = "SECURED" if is_secured else "RISK ON"
                close_at = entry if is_secured else "Stop Loss"
                risk_report.append(f"{coin}|{side}|{margin:.2f}|{status}|{close_at}")

            pos_str = "::".join(pos_lines)
        
        if not risk_report: risk_report.append("NO_TRADES")

        data = {
            "equity": f"{equity:.2f}",
            "cash": f"{cash:.2f}",
            "pnl": f"{pnl:+.2f}",
            "status": status_msg,
            "session": session,
            "win_rate": daily_stats_str,
            "trade_history": history_str, 
            "live_activity": LIVE_ACTIVITY, 
            "positions": pos_str,
            "risk_report": "::".join(risk_report),
            "mode": mode,
            "updated": time.time()
        }
        temp_dash = "dashboard_state.tmp"
        with open(temp_dash, "w") as f: json.dump(data, f, ensure_ascii=False)
        os.replace(temp_dash, "dashboard_state.json")
    except Exception as e: pass

# --- NEW: LOGIC SCORE ENGINE (Evolution Logic) ---
def calculate_logic_score(coin, candles, session, regime):
    """Calculates 0-100 Confidence Score based on Evolution Data Points"""
    score = 50.0 
    try:
        # 1. Trend Angle (Slope of last 4 candles)
        if len(candles) >= 4:
            closes = [float(c.get('close') or c.get('c')) for c in candles[-4:]]
            if closes[0] == 0: return 50
            slope = (closes[-1] - closes[0]) / closes[0]
            if slope > 0.02: score += 15  # Strong Bull
            elif slope > 0.005: score += 5 
            elif slope < -0.01: score -= 15 # Bear Drag

        # 2. Session ID (Liquidity Preference)
        if "LONDON" in session or "NEW_YORK" in session: score += 10
        elif "ASIA" in session: score -= 5 

        # 3. Regime State
        if regime == "BULLISH": score += 15
        elif regime == "BEARISH": score -= 20 

        # 4. Volatility Expansion (Simple Range Check)
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
    vision = Vision()
    hands = Hands()
    xeno = Xenomorph()
    whale = SmartMoney()
    ratchet = DeepSea()
    msg = Messenger()
    chronos = Chronos()
    history = Historian()
    oracle = Oracle()
    season = Seasonality()
    predator = Predator()
    print(">> SYSTEM INTEGRITY: 100%")
except Exception as e:
    print(f"xx CRITICAL LOAD ERROR: {e}")
    sys.exit()

def main_loop():
    global STARTING_EQUITY
    print("🦅 LUMA SINGULARITY (V2.3: STABLE EVOLUTION)")
    try:
        update_heartbeat("BOOTING")
        
        # --- DASHBOARD FLUSH (FIXES STUCK TEXT) ---
        update_dashboard(0, 0, "SYSTEM BOOTING...", [], "STANDARD", [], activity_event="Connecting to Exchange...")
        
        address = os.environ.get("WALLET_ADDRESS")
        if not address:
            try:
                cfg = json.load(open(CONFIG_FILE))
                address = cfg.get('wallet_address')
            except: pass
        
        if not address:
            print("xx CRITICAL: No WALLET_ADDRESS found.")
            return

        msg.send("info", "🦅 **LUMA ONLINE:** EVOLUTION ACTIVE. LOGS PERSISTENT.")
        last_history_check = 0
        cached_history_data = {'regime': 'NEUTRAL', 'multiplier': 1.0}
        leverage_memory = {}

        while True:
            update_heartbeat("ALIVE")
            session_data = chronos.get_session()
            session_name = session_data['name']
            
            if check_daily_reset():
                update_dashboard(equity, cash, "DAILY RESET", clean_positions, risk_mode, secured, trade_event="--- DAILY STATS RESET ---", session=session_name)

            if time.time() - last_history_check > 14400:
                try:
                    btc_daily = vision.get_candles(BTC_TICKER, "1d")
                    if btc_daily:
                        cached_history_data = history.check_regime(btc_daily)
                        last_history_check = time.time()
                except: pass

            history_data = cached_history_data
            regime = history_data.get('regime', 'NEUTRAL')
            
            equity = 0.0
            cash = 0.0
            clean_positions = []
            open_orders = []

            try:
                user_state = vision.get_user_state(address)
                if user_state:
                    equity = float(user_state.get('marginSummary', {}).get('accountValue', 0))
                    cash = float(user_state.get('withdrawable', 0))
                    clean_positions = normalize_positions(user_state.get('assetPositions', []))
                    open_orders = user_state.get('openOrders', [])
            except: pass

            if STARTING_EQUITY == 0.0 and equity > 0:
                STARTING_EQUITY = load_anchor(equity)
            
            current_pnl = equity - STARTING_EQUITY if STARTING_EQUITY > 0 else 0.0
            start_eq_safe = STARTING_EQUITY if STARTING_EQUITY > 0 else 1.0
            current_roe_pct = (current_pnl / start_eq_safe) * 100

            # --- CIRCUIT BREAKER ---
            if equity < 300.0 and equity > 1.0:
                 print("xx CRITICAL: EQUITY BELOW $300. HALTING TRADING.")
                 msg.send("errors", "CRITICAL: HARD FLOOR BREACHED. SHUTTING DOWN.")
                 time.sleep(3600)
                 continue

            # --- SCALABLE STATE MACHINE ---
            RECOVERY_TARGET = 412.0
            TITAN_THRESHOLD = 12.0
            SHIELD_THRESHOLD = -10.0
            
            risk_mode = "STANDARD"
            titan_active = False
            shield_active = False

            if current_roe_pct >= TITAN_THRESHOLD:
                titan_active = True
                status_msg = f"Mode:{risk_mode} (TITAN ACTIVE) | ROE:+{current_roe_pct:.2f}%"
            elif current_roe_pct <= SHIELD_THRESHOLD:
                shield_active = True
                risk_mode = "RECOVERY" 
                status_msg = f"🛡️ SHIELD ACTIVE (STRICT FILTER) | ROE:{current_roe_pct:.2f}%"
            else:
                status_msg = f"Mode:{risk_mode} (ROE:{current_roe_pct:.2f}%)"

            if not shield_active:
                if equity < RECOVERY_TARGET:
                    risk_mode = "RECOVERY"
                elif current_roe_pct >= 5.0:
                    risk_mode = "GOD_MODE"
                    if titan_active:
                        status_msg = f"Mode:GOD_MODE (TITAN ACTIVE) | ROE:+{current_roe_pct:.2f}%"

            base_margin_usd = equity * 0.11
            max_margin_usd  = equity * 0.165
            secured = ratchet.secured_coins
            
            update_dashboard(equity, cash, status_msg, clean_positions, risk_mode, secured, session=session_name)
            
            print(f">> [{time.strftime('%H:%M:%S')}] {status_msg}", end='\r')

            active_coins = [p['coin'] for p in clean_positions]
            
            # --- MAIN SCANNING LOOP ---
            for coin, rules in FLEET_CONFIG.items():
                update_heartbeat("SCANNING")

                target_leverage = rules['lev']
                if risk_mode == "GOD_MODE" and rules['type'] == "MEME":
                    target_leverage = 10
                if risk_mode == "RECOVERY" or shield_active:
                    target_leverage = 5
                
                target_leverage = int(target_leverage)

                if coin in active_coins:
                    pass
                else:
                    if leverage_memory.get(coin) != target_leverage:
                        try:
                            hands.set_leverage_all([coin], leverage=target_leverage)
                            leverage_memory[coin] = target_leverage
                        except: pass

                if ratchet.check_trauma(hands, coin): continue
                existing = next((p for p in clean_positions if p['coin'] == coin), None)
                if existing: continue

                try: candles = vision.get_candles(coin, "1h")
                except: candles = []
                if not candles: continue
                current_price = float(candles[-1].get('close') or 0)
                if current_price == 0: continue
                
                update_dashboard(equity, cash, status_msg, clean_positions, risk_mode, secured, session=session_name, activity_event=f"Scanning {coin} ({rules['type']})...")

                pending = next((o for o in open_orders if o.get('coin') == coin), None)
                if pending:
                    try:
                        order_price = float(pending.get('limitPx') or 0)
                        gap = abs(current_price - order_price) / order_price
                        if gap > 0.005:
                            msg_txt = f"🏃 CHASING {coin} (Adjusting Trap)"
                            hands.cancel_all_orders(coin)
                            update_dashboard(equity, cash, status_msg, clean_positions, risk_mode, secured, session=session_name, activity_event=msg_txt)
                            continue
                    except: continue

                # --- 2. SIGNAL LOGIC ---
                proposal = None
                trend_status = predator.analyze_divergence(candles, coin)
                season_info = season.get_multiplier(rules['type'])
                season_mult = season_info.get('mult', 1.0)
                
                whale_signal = whale.hunt_turtle(candles) or whale.hunt_ghosts(candles)
                xeno_signal = xeno.hunt(coin, candles)

                if xeno_signal == "ATTACK":
                    if rules['type'] == "OFF": continue
                    is_valid_sniper = False
                    if titan_active or shield_active:
                         if trend_status == "REAL_PUMP": is_valid_sniper = True
                    else:
                         if trend_status == "REAL_PUMP" or trend_status is None: is_valid_sniper = True

                    if is_valid_sniper:
                        proposal = {"source": "SNIPER", "side": "BUY", "price": current_price * 0.999, "reason": "MOMENTUM_CONFIRMED"}

                if whale_signal:
                    if trend_status != "REAL_PUMP":
                        proposal = {"source": whale_signal['type'], "side": whale_signal['side'], "price": whale_signal['price'], "reason": "REVERSAL_CONFIRMED"}

                if proposal:
                    # --- EVOLUTION: CALCULATE LOGIC SCORE ---
                    logic_score = calculate_logic_score(coin, candles, session_name, regime)
                    
                    # Base Sizing (Tier 1)
                    raw_margin = base_margin_usd * season_mult
                    final_margin_usd = min(raw_margin, max_margin_usd)
                    
                    # Feature: RISK SHIELD ONLY (No Boost, only Safety Cuts)
                    if logic_score < 30: final_margin_usd = final_margin_usd * 0.5

                    final_size = round(final_margin_usd * target_leverage, 2)
                    if final_size < 40: final_size = 40

                    if oracle.consult(coin, proposal['source'], proposal['price'], f"Session: {session_name}"):
                        msg_txt = f"OPEN {coin} ({proposal['source']}) ${final_margin_usd:.0f} [Score:{logic_score}]"
                        
                        hands.place_trap(coin, proposal['side'], proposal['price'], final_size)
                        msg.notify_trade(coin, proposal['source'], proposal['price'], final_size)
                        
                        # Save Score for Dashboard display
                        TRADE_SCORES[coin] = logic_score
                        save_scores()
                        
                        update_dashboard(equity, cash, status_msg, clean_positions, risk_mode, secured, trade_event=msg_txt, session=session_name)
            
            # --- RATCHET MANAGEMENT (STRICT 1% LOCK) ---
            # We pass FLEET_CONFIG directly. No dynamic Stop Loss modification.
            ratchet_events = ratchet.manage_positions(hands, clean_positions, FLEET_CONFIG)
            
            if ratchet_events:
                for event in ratchet_events:
                    if any(x in event for x in ["PROFIT", "+", "WIN", "GAIN"]): 
                        update_stats(1)
                    elif any(x in event for x in ["LOSS", "-", "LOSE"]): 
                        update_stats(-1)
                    
                    update_dashboard(equity, cash, status_msg, clean_positions, risk_mode, secured, trade_event=event, session=session_name)
            
            time.sleep(3)

    except Exception as e:
        print(f"xx CRITICAL: {e}")
        msg.send("errors", f"CRASH: {e}")

if __name__ == "__main__":
    try: main_loop()
    except: print("\n🦅 LUMA OFFLINE")
