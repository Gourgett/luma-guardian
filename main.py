import time
import json
import sys
import os
import warnings
from collections import deque

warnings.simplefilter("ignore")

# ==============================================================================
#  LUMA SINGULARITY [TIER: OFF HIERARCHY + MEME PRESERVATION]
# ==============================================================================

CONFIG_FILE = "server_config.json"
ANCHOR_FILE = "equity_anchor.json"
BTC_TICKER = "BTC"

FLEET_CONFIG = {
    # --- THE VETERANS ---
    "WIF":    {"type": "MEME", "lev": 5, "risk_mult": 1.0, "stop_loss": 0.06},
    "DOGE":   {"type": "MEME", "lev": 5, "risk_mult": 1.0, "stop_loss": 0.06},
    "PENGU":  {"type": "MEME", "lev": 5, "risk_mult": 1.0, "stop_loss": 0.06},

    # --- THE REINFORCEMENTS (Structural Beta) ---
    "POPCAT": {"type": "MEME", "lev": 5, "risk_mult": 1.0, "stop_loss": 0.06},
    "BRETT":  {"type": "MEME", "lev": 5, "risk_mult": 1.0, "stop_loss": 0.06},
    "SPX":    {"type": "MEME", "lev": 5, "risk_mult": 1.0, "stop_loss": 0.06}
}

STARTING_EQUITY = 0.0
# UPDATE: Increased memory to 60 events
EVENT_QUEUE = deque(maxlen=60)

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
    except:
        return current_equity

def update_heartbeat(status="ALIVE"):
    try:
        temp_file = "heartbeat.tmp"
        with open(temp_file, "w") as f:
            json.dump({"last_beat": time.time(), "status": status}, f)
        os.replace(temp_file, "heartbeat.json")
    except: pass

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

# UPDATE: Added 'session' parameter to this function
def update_dashboard(equity, cash, status_msg, positions, mode="AGGRESSIVE", secured_list=[], new_event=None, session="N/A"):
    global STARTING_EQUITY, EVENT_QUEUE
    try:
        if STARTING_EQUITY == 0.0 and equity > 0:
            STARTING_EQUITY = load_anchor(equity)
        
        pnl = equity - STARTING_EQUITY if STARTING_EQUITY > 0 else 0.0

        if new_event:
            t = time.strftime("%H:%M:%S")
            EVENT_QUEUE.append(f"[{t}] {new_event}")
        
        events_str = "||".join(list(EVENT_QUEUE))
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

                pos_lines.append(f"{coin}|{side}|{pnl_val:.2f}|{roe:.1f}|{icon}|{t_str}")

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
            "session": session,  # New Field
            "events": events_str,
            "positions": pos_str,
            "risk_report": "::".join(risk_report),
            "mode": mode,
            "updated": time.time()
        }
        temp_dash = "dashboard_state.tmp"
        with open(temp_dash, "w") as f: json.dump(data, f, ensure_ascii=False)
        os.replace(temp_dash, "dashboard_state.json")
    except Exception as e: pass

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
    print("🦅 LUMA SINGULARITY (OFF FILTER ACTIVE)")
    try:
        update_heartbeat("BOOTING")
        
        address = os.environ.get("WALLET_ADDRESS")
        if not address:
            try:
                cfg = json.load(open(CONFIG_FILE))
                address = cfg.get('wallet_address')
            except: pass
        
        if not address:
            print("xx CRITICAL: No WALLET_ADDRESS found.")
            return

        msg.send("info", "🦅 **LUMA UPDATE:** MEME FLEET (6-PACK) + RECOVERY LOCK ($412).")
        last_history_check = 0
        cached_history_data = {'regime': 'NEUTRAL', 'multiplier': 1.0}
        leverage_memory = {}

        while True:
            update_heartbeat("ALIVE")
            session_data = chronos.get_session()
            session_name = session_data['name'] # Extract Session Name

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

            # --- CIRCUIT BREAKER ---
            if equity < 300.0 and equity > 1.0:
                 print("xx CRITICAL: EQUITY BELOW $300. HALTING TRADING.")
                 msg.send("errors", "CRITICAL: HARD FLOOR BREACHED. SHUTTING DOWN.")
                 time.sleep(3600)
                 continue

            # --- SCALABLE STATE MACHINE (RECOVERY LOCK) ---
            RECOVERY_TARGET = 412.0
            risk_mode = "STANDARD"
            
            if equity < RECOVERY_TARGET:
                risk_mode = "RECOVERY"
            elif current_roe_pct >= 5.0:
                risk_mode = "GOD_MODE"
            
            base_margin_usd = equity * 0.11
            max_margin_usd  = equity * 0.165

            secured = ratchet.secured_coins

            status_msg = f"Mode:{risk_mode} (ROE:{current_roe_pct:.2f}%) Cap:${max_margin_usd:.0f}"
            
            # UPDATE: Pass session_name to dashboard
            update_dashboard(equity, cash, status_msg, clean_positions, risk_mode, secured, session=session_name)
            
            print(f">> [{time.strftime('%H:%M:%S')}] {status_msg}", end='\r')

            active_coins = [p['coin'] for p in clean_positions]
            for coin, rules in FLEET_CONFIG.items():
                update_heartbeat("SCANNING")

                # --- 1. SMART LEVERAGE MANAGEMENT ---
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
                context_str = f"Session: {session_data['name']}, Season: {season_info['note']}"
                
                whale_signal = whale.hunt_turtle(candles) or whale.hunt_ghosts(candles)
                xeno_signal = xeno.hunt(coin, candles)

                # --- A. SNIPER (MOMENTUM) ---
                if xeno_signal == "ATTACK":
                    if rules['type'] == "OFF":
                        continue
                    else:
                        if trend_status == "REAL_PUMP" or trend_status is None:
                            proposal = {
                                "source": "SNIPER",
                                "side": "BUY",
                                "price": current_price * 0.999,
                                "reason": "MOMENTUM_CONFIRMED"
                            }

                # --- B. WHALE (SMART MONEY) ---
                if whale_signal:
                    if trend_status != "REAL_PUMP":
                        proposal = {
                            "source": whale_signal['type'],
                            "side": whale_signal['side'],
                            "price": whale_signal['price'],
                            "reason": "REVERSAL_CONFIRMED"
                        }

                if proposal:
                    raw_margin = base_margin_usd * season_mult
                    final_margin_usd = min(raw_margin, max_margin_usd)
                    final_size = round(final_margin_usd * target_leverage, 2)

                    if final_size < 40: final_size = 40

                    if oracle.consult(coin, proposal['source'], proposal['price'], context_str):
                        lev_tag = f"{target_leverage}x"
                        log = f"{coin}: {proposal['source']} ({proposal['reason']}) [${final_margin_usd:.0f} Margin | {lev_tag}]"
                        print(f"\n>> {log}")
                        hands.place_trap(coin, proposal['side'], proposal['price'], final_size)
                        msg.notify_trade(coin, proposal['source'], proposal['price'], final_size)
            
            ratchet_events = ratchet.manage_positions(hands, clean_positions, FLEET_CONFIG)
            if ratchet_events:
                for event in ratchet_events:
                    update_dashboard(equity, cash, status_msg, clean_positions, risk_mode, secured, new_event=event)
            
            time.sleep(3)

    except Exception as e:
        print(f"xx CRITICAL: {e}")
        msg.send("errors", f"CRASH: {e}")

if __name__ == "__main__":
    try: main_loop()
    except: print("\n🦅 LUMA OFFLINE")
