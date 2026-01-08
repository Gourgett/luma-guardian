import time
import json
import sys
import os
import warnings
from collections import deque

warnings.simplefilter("ignore")

# ==============================================================================
#  LUMA SINGULARITY [RAILWAY EDITION: SAFE STRUCTURE]
#  Logic: k-Tickers Active | Risk 0.75 | Stop 4% | Asia Sniper
# ==============================================================================

DATA_DIR = "/app/data"
if not os.path.exists(DATA_DIR):
    try: os.makedirs(DATA_DIR)
    except: pass

CONFIG_FILE = "server_config.json"
ANCHOR_FILE = os.path.join(DATA_DIR, "equity_anchor.json")
STATS_FILE = os.path.join(DATA_DIR, "stats.json")
BTC_TICKER = "BTC"

# --- FLEET CONFIG ---
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
    "financial_header": "Initializing...",
    "activity_header": ">> Starting System..."
}

def load_stats():
    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, 'r') as f: data = json.load(f)
        else: data = {"last_reset": time.strftime("%Y-%m-%d"), "wins": 0, "losses": 0}
    except: data = {"last_reset": time.strftime("%Y-%m-%d"), "wins": 0, "losses": 0}
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
    # Save history
    history_entry = {"date": time.strftime("%Y-%m-%d %H:%M"), "coin": coin, "pnl": pnl, "reason": reason}
    if "history" not in stats: stats["history"] = []
    stats["history"].insert(0, history_entry)
    stats["history"] = stats["history"][:50] # Keep last 50
    save_stats(stats)
    return stats

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

def sync_dashboard_state(equity, cash, pnl, positions, mode, events, session_name):
    # This creates the JSON file that App.py will read
    try:
        pos_str = "NO_TRADES"
        risk_report = []
        
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
                
                # Format for Streamlit: COIN|SIDE|PNL|ROE|STATUS|TARGET
                pos_lines.append(f"{coin}|{side}|{pnl_val:.2f}|{roe:.1f}|OPEN|0.00")
                risk_report.append(f"{coin}|{side}|{margin:.2f}|RISK ON|Stop Loss")
            pos_str = "::".join(pos_lines)
            
        data = {
            "equity": f"{equity:.2f}",
            "cash": f"{cash:.2f}",
            "pnl": f"{pnl:+.2f}",
            "mode": mode,
            "session": session_name,
            "positions": pos_str,
            "events": "||".join(list(events)),
            "updated": time.time()
        }
        
        temp_dash = os.path.join(DATA_DIR, "dashboard_state.tmp")
        with open(temp_dash, "w") as f: json.dump(data, f, ensure_ascii=False)
        os.replace(temp_dash, os.path.join(DATA_DIR, "dashboard_state.json"))
    except Exception as e:
        print(f"xx DASHBOARD SYNC ERROR: {e}")

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
    print("🦅 LUMA SINGULARITY (RAILWAY SAFE MODE)")
    try:
        update_heartbeat("BOOTING")
        try:
            cfg = json.load(open(CONFIG_FILE))
            address = cfg.get('wallet_address')
        except: return
        
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
                    if btc_daily:
                        cached_history_data = history.check_regime(btc_daily)
                        last_history_check = time.time()
                except: pass
            
            history_data = cached_history_data
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

            # --- CIRCUIT BREAKER (Restored to 200) ---
            if equity < 200.0 and equity > 1.0:
                 print("xx CRITICAL: EQUITY BELOW $200. HALTING TRADING.")
                 msg.send("errors", "CRITICAL: HARD FLOOR BREACHED. SHUTTING DOWN.")
                 time.sleep(3600)
                 continue

            # --- SCALABLE STATE MACHINE ---
            risk_mode = "STANDARD"
            if current_roe_pct >= 5.0:
                risk_mode = "GOD_MODE"
            
            base_margin_usd = equity * 0.11
            max_margin_usd  = equity * 0.165
            
            # DASHBOARD SYNC
            sync_dashboard_state(equity, cash, current_pnl, clean_positions, risk_mode, EVENT_QUEUE, sess_name)
            status_msg = f"Mode:{risk_mode} [{sess_name}] (ROE:{current_roe_pct:.2f}%)"
            print(f">> [{time.strftime('%H:%M:%S')}] {status_msg}", end='\r')

            active_coins = [p['coin'] for p in clean_positions]

            for coin, rules in FLEET_CONFIG.items():
                update_heartbeat("SCANNING")
                
                target_leverage = rules['lev']
                if risk_mode == "GOD_MODE" and rules['type'] == "MEME":
                    target_leverage = 10
                
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
                current_price = float(candles[-1].get('close') or candles[-1].get('c') or 0)
                if current_price == 0: continue

                pending = next((o for o in open_orders if o.get('coin') == coin), None)
                if pending:
                    try:
                        order_price = float(pending.get('limitPx') or pending.get('price') or 0)
                        gap = abs(current_price - order_price) / order_price
                        if gap > 0.005:
                            print(f">> 🏃 CHASING: {coin} moved away ({gap*100:.1f}%). Adjusting trap...")
                            hands.cancel_all_orders(coin)
                            continue
                    except: continue

                # --- 2. THE SIGNAL HIERARCHY ---
                proposal = None
                trend_status = predator.analyze_divergence(candles, coin)
                season_info = season.get_multiplier(rules['type'])
                season_mult = season_info.get('mult', 1.0)
                context_str = f"Session: {sess_name}, Season: {season_info['note']}"

                whale_signal = whale.hunt_turtle(candles) or whale.hunt_ghosts(candles)
                xeno_signal = xeno.hunt(coin, candles)

                # --- A. SNIPER (MOMENTUM) ---
                if xeno_signal == "ATTACK":
                    if rules['type'] == "OFF": continue
                    else:
                        if trend_status == "REAL_PUMP" or trend_status is None:
                            proposal = {"source": "SNIPER", "side": "BUY", "price": current_price * 0.999, "reason": "MOMENTUM_CONFIRMED"}

                # --- B. WHALE (SMART MONEY) ---
                # ASIA FILTER: IGNORE Reversals during Asia
                if sess_name == "ASIA":
                     whale_signal = None
                
                if whale_signal:
                    if trend_status != "REAL_PUMP":
                        proposal = {"source": whale_signal['type'], "side": whale_signal['side'], "price": whale_signal['price'], "reason": "REVERSAL_CONFIRMED"}

                if proposal:
                    # FIX: Correct Risk Math
                    raw_margin = base_margin_usd * season_mult * rules.get('risk_mult', 1.0)

                    final_margin_usd = min(raw_margin, max_margin_usd)
                    final_size = round(final_margin_usd * target_leverage, 2)
                    if final_size < 40: final_size = 40

                    if oracle.consult(coin, proposal['source'], proposal['price'], context_str):
                        lev_tag = f"{target_leverage}x"
                        log_msg = f"{coin}: {proposal['source']} ({proposal['reason']}) [${final_margin_usd:.0f} Margin | {lev_tag}]"
                        print(f"\n>> {log_msg}")
                        
                        # Add to Event Queue for Dashboard
                        t_now = time.strftime("%H:%M:%S")
                        EVENT_QUEUE.append(f"[{t_now}] {log_msg}")
                        
                        hands.place_trap(coin, proposal['side'], proposal['price'], final_size)
                        msg.notify_trade(coin, proposal['source'], proposal['price'], final_size)

            ratchet_events = ratchet.manage_positions(hands, clean_positions, FLEET_CONFIG)
            if ratchet_events:
                for event in ratchet_events:
                     # Log events to dashboard queue
                     t_now = time.strftime("%H:%M:%S")
                     EVENT_QUEUE.append(f"[{t_now}] {event}")
                     
                     # Update stats logic
                     if "STOP LOSS" in event or "PROFIT" in event:
                         try:
                             parts = event.split(":") 
                             coin_name = parts[1].split("(")[0].strip()
                             clean_event = event.replace("💰 ", "")
                             pnl_val = float(event.split("(")[1].split("|")[0].strip())
                             update_stats(pnl_val, coin_name, clean_event)
                         except: pass

            time.sleep(3)

    except Exception as e:
        print(f"xx CRITICAL: {e}")
        msg.send("errors", f"CRASH: {e}")

if __name__ == "__main__":
    try: main_loop()
    except: print("\n🦅 LUMA OFFLINE")
