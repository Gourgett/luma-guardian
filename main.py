import time
import json
import sys
import os
import warnings
from collections import deque
from config import conf

warnings.simplefilter("ignore")

# TIER: RAILWAY CLOUD COMMANDER (DIAGNOSTIC MODE)
ANCHOR_FILE = conf.get_path("equity_anchor.json")
BTC_TICKER = "BTC"
SESSION_START_TIME = time.time()

FLEET_CONFIG = {
    "SOL":   {"type": "PRINCE", "lev": 10, "risk_mult": 1.0, "stop_loss": 0.03},
    "SUI":   {"type": "PRINCE", "lev": 10, "risk_mult": 1.0, "stop_loss": 0.03},
    "ETH":   {"type": "PRINCE", "lev": 10, "risk_mult": 1.0, "stop_loss": 0.03},
    "WIF":   {"type": "MEME",   "lev": 5,  "risk_mult": 1.0, "stop_loss": 0.05},
    "kPEPE": {"type": "MEME",   "lev": 5,  "risk_mult": 1.0, "stop_loss": 0.05},
    "DOGE":  {"type": "MEME",   "lev": 5,  "risk_mult": 1.0, "stop_loss": 0.05}
}

STARTING_EQUITY = 0.0
EVENT_QUEUE = deque(maxlen=4)
RADAR_CACHE = {} 

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

def calculate_projection(current_pnl):
    elapsed_hours = (time.time() - SESSION_START_TIME) / 3600
    if elapsed_hours < 0.1: return 0.0 
    hourly_rate = current_pnl / elapsed_hours
    return hourly_rate * 24 * 30

def update_dashboard(equity, cash, status_msg, positions, mode="AGGRESSIVE", session_name="--", secured_list=[], new_event=None):
    global STARTING_EQUITY, EVENT_QUEUE, RADAR_CACHE
    try:
        if STARTING_EQUITY == 0.0 and equity > 0: 
            STARTING_EQUITY = load_anchor(equity)
            
        pnl = equity - STARTING_EQUITY if STARTING_EQUITY > 0 else 0.0
        proj_30d = calculate_projection(pnl)
        
        if new_event:
            t = time.strftime("%H:%M:%S")
            EVENT_QUEUE.append(f"[{t}] {new_event}")
        events_str = "||".join(list(EVENT_QUEUE))

        pos_str = "NO_TRADES"
        if positions:
            pos_lines = []
            for p in positions:
                coin = p['coin']
                size = p['size']
                entry = p['entry']
                pnl_val = p['pnl']
                side = "LONG" if size > 0 else "SHORT"
                
                lev = FLEET_CONFIG.get(coin, {}).get('lev', 10)
                margin = (abs(size) * entry) / lev
                roe = 0.0
                if margin > 0: roe = (pnl_val / margin) * 100
                
                is_secured = coin in secured_list
                icon = "🔒" if is_secured else "" 
                pos_lines.append(f"{coin}|{side}|{pnl_val:.2f}|{roe:.1f}|{icon}")
            pos_str = "::".join(pos_lines)

        radar_lines = []
        for coin, data in RADAR_CACHE.items():
            radar_lines.append(f"{coin}|{data['price']}|{data['status']}|{data['color']}")
        radar_str = "::".join(radar_lines)
        
        data = {
            "equity": f"{equity:.2f}",
            "cash": f"{cash:.2f}",
            "pnl": f"{pnl:+.2f}",
            "proj": f"{proj_30d:+.2f}",
            "status": status_msg,
            "events": events_str,
            "positions": pos_str,
            "radar": radar_str,
            "mode": mode,
            "session": session_name,
            "updated": time.time()
        }
        
        with open(conf.get_path("dashboard_state.json"), "w") as f: 
            json.dump(data, f, ensure_ascii=False)
            
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
    global STARTING_EQUITY, RADAR_CACHE
    
    print("🦅 LUMA CLOUD COMMANDER ONLINE")
    try:
        address = conf.wallet_address
        msg.send("info", "🦅 **LUMA CLOUD:** Diagnostics Active.")
        
        for coin, rules in FLEET_CONFIG.items():
            try:
                hands.set_leverage_all([coin], leverage=rules['lev'])
                time.sleep(0.2) 
            except: pass

        last_history_check = 0
        cached_history_data = {'regime': 'NEUTRAL', 'multiplier': 1.0}
        last_finance_report = 0 
        
        while True:
            session_data = chronos.get_session()
            session_name = session_data['name']
            
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
            
            risk_mode = "AGGRESSIVE"
            investable_pct = 0.60 
            if current_pnl > 5.00:
                risk_mode = "GOD_MODE"
                investable_pct = 0.70 
            
            total_investable_cash = equity * investable_pct
            prince_margin_target = total_investable_cash * 0.25
            meme_margin_target = total_investable_cash * 0.1666
            
            # Use property name 'secured_coins' to prevent crash
            secured = ratchet.secured_coins

            status_msg = f"Scanning... Mode:{risk_mode}"
            update_dashboard(equity, cash, status_msg, clean_positions, risk_mode, session_name, secured)
            print(f">> [{time.strftime('%H:%M:%S')}] Pulse Check: OK", end='\r')

            if time.time() - last_finance_report > 3600:
                try:
                    msg.notify_financial(equity, current_pnl, len(clean_positions), risk_mode)
                    last_finance_report = time.time()
                except: pass

            for coin, rules in FLEET_CONFIG.items():
                ratchet.check_trauma(hands, coin)
                
                existing = next((p for p in clean_positions if p['coin'] == coin), None)
                pending = next((o for o in open_orders if o.get('coin') == coin), None)
                
                try: candles = vision.get_candles(coin, "1h") 
                except: candles = []
                
                if candles:
                    curr_p = float(candles[-1]['c'])
                    formatted_p = f"${curr_p:.4f}"
                    
                    if existing:
                        RADAR_CACHE[coin] = {"price": formatted_p, "status": "ACTIVE TRADE", "color": "blue"}
                    elif pending:
                        limit_px = pending.get('limitPx', '---')
                        RADAR_CACHE[coin] = {"price": formatted_p, "status": f"🛡️ TRAP @ {limit_px}", "color": "cyan"}
                    else:
                        RADAR_CACHE[coin] = {"price": formatted_p, "status": "👀 SCANNING", "color": "gray"}
                else:
                    continue

                if existing or pending: continue 

                micro_season = season.get_multiplier(rules['type'])
                macro_mult = session_data['aggression'] * history_data['multiplier']
                total_mult = macro_mult * micro_season['mult']
                if total_mult < 1.0: total_mult = 1.0
                if total_mult > 1.0: total_mult = 1.0 
                
                if rules['type'] == "PRINCE": target_margin_usd = prince_margin_target
                else: target_margin_usd = meme_margin_target
                
                leverage = rules['lev']
                final_size = target_margin_usd * leverage
                if final_size < 60.0: final_size = 60.0
                final_size = round(final_size, 2)
                
                context_str = f"Session: {session_data['name']}, Season: {micro_season['note']}"
                predator_signal = predator.analyze_divergence(candles)
                sm_signal = whale.hunt_turtle(candles) or whale.hunt_ghosts(candles)
                
                if sm_signal:
                    if predator_signal != "EXHAUSTION_SELL" or sm_signal['side'] == "SELL":
                         if oracle.consult(coin, sm_signal['type'], sm_signal['price'], context_str):
                            side = sm_signal['side']
                            if hands.place_trap(coin, side, sm_signal['price'], final_size):
                                log = f"{coin}: {sm_signal['type']} ({risk_mode})"
                                update_dashboard(equity, cash, status_msg, clean_positions, risk_mode, session_name, secured, new_event=log)
                                msg.notify_trade(coin, f"TRAP_{side}", sm_signal['price'], final_size)
                            else:
                                update_dashboard(equity, cash, status_msg, clean_positions, risk_mode, session_name, secured, new_event=f"❌ {coin}: TRAP FAILED")
                
                elif xeno.hunt(coin, candles) == "ATTACK":
                    if predator_signal == "REAL_PUMP" or predator_signal is None:
                        if rules['type'] == "MEME" and session_data['name'] == "ASIA": pass 
                        else:
                            if oracle.consult(coin, "BREAKOUT_BUY", "Market", context_str):
                                coin_size = final_size / float(candles[-1]['c'])
                                
                                # --- MARKET BUY EXECUTION & DIAGNOSTICS ---
                                # result is True OR an error string
                                result = hands.place_market_order(coin, "BUY", coin_size)
                                
                                if result is True:
                                    log = f"{coin}: MARKET BUY ({risk_mode})"
                                    update_dashboard(equity, cash, status_msg, clean_positions, risk_mode, session_name, secured, new_event=log)
                                    msg.notify_trade(coin, "MARKET_BUY", "Market", final_size)
                                else:
                                    # PARSE ERROR FOR DISPLAY
                                    err_msg = str(result)
                                    if "Insufficient Margin" in err_msg: short_err = "NO MARGIN"
                                    elif "Invalid Size" in err_msg: short_err = "BAD SIZE"
                                    else: short_err = "REJECTED" # Will verify in logs
                                    
                                    err_log = f"❌ {coin}: {short_err}"
                                    update_dashboard(equity, cash, status_msg, clean_positions, risk_mode, session_name, secured, new_event=err_log)

            ratchet_events = ratchet.manage_positions(hands, clean_positions, FLEET_CONFIG)
            if ratchet_events:
                for event in ratchet_events:
                     update_dashboard(equity, cash, status_msg, clean_positions, risk_mode, session_name, secured, new_event=event)
            
            time.sleep(3) 
            
    except Exception as e:
        print(f"xx CRITICAL: {e}")
        msg.send("errors", f"CRASH: {e}")

if __name__ == "__main__":
    try: main_loop()
    except: print("\n🦅 LUMA OFFLINE")
