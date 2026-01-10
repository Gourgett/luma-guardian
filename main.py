import time
import json
import sys
import os
import warnings
from collections import deque
from datetime import datetime, timezone

# IMPORT MODULES
try:
    from vision import Vision
    from predator import Predator
    from deep_sea import DeepSea
    from xenomorph import Xenomorph
    from smart_money import SmartMoney
    from hands import Hands
    from messenger import Messenger
    # from seasonality import Seasonality 
except ImportError as e:
    print(f">> CRITICAL ERROR: Missing Module {e}")
    sys.exit(1)

warnings.simplefilter("ignore")

# ==========================================
# 1. CONFIGURATION
# ==========================================
DATA_DIR = "/app/data" if os.path.exists("/app/data") else "."
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR, exist_ok=True)

DASHBOARD_FILE = os.path.join(DATA_DIR, "dashboard_state.json")
LOG_FILE = os.path.join(DATA_DIR, "system.log") # Permanent Memory
STARTING_EQUITY = 412.0 

# [BLUEPRINT] High-Volatility Fleet
FLEET_CONFIG = {
    "SOL":   {"type": "PRINCE", "lev": 5},
    "SUI":   {"type": "PRINCE", "lev": 5},
    "BNB":   {"type": "PRINCE", "lev": 5},
    "WIF":   {"type": "MEME",   "lev": 5},
    "DOGE":  {"type": "MEME",   "lev": 5},
    "PENGU": {"type": "MEME",   "lev": 5}
}

EVENT_QUEUE = deque(maxlen=50) 

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================
def load_config():
    """Prioritizes Environment Variables (Railway Security)"""
    pk = os.environ.get("PRIVATE_KEY")
    wallet = os.environ.get("WALLET_ADDRESS")
    
    # Fallback to file only if env vars are missing (Backward Compatibility)
    if not pk:
        try:
            if os.path.exists("server_config.json"):
                with open("server_config.json", 'r') as f: return json.load(f)
        except: return None
    return {"wallet_address": wallet, "private_key": pk}

def log_permanent(message):
    """Writes logs to disk for permanent memory."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"[{timestamp}] {message}\n")
    except: pass

def save_dashboard_state(mode, session, equity, cash, positions, scan_results, logs, secured_coins):
    """
    STABILITY PATCH: Includes retry logic to prevent crashes 
    if the Dashboard is reading the file simultaneously.
    """
    try:
        pnl = equity - STARTING_EQUITY
        roe = (pnl / STARTING_EQUITY) * 100
        dash_state = {
            "mode": mode, "session": session,
            "equity": round(equity, 2), "cash": round(cash, 2),
            "pnl": round(pnl, 2), "account_roe": round(roe, 2),
            "positions": positions, "scan_results": scan_results,
            "logs": list(logs), "secured_coins": secured_coins
        }
        
        temp = DASHBOARD_FILE + ".tmp"
        # 1. Write to temp
        with open(temp, 'w') as f: json.dump(dash_state, f)
        
        # 2. Atomic Replace with Retry
        max_retries = 5
        for i in range(max_retries):
            try:
                os.replace(temp, DASHBOARD_FILE)
                break
            except PermissionError:
                time.sleep(0.1)
            except Exception as e:
                print(f"xx SAVE ERROR: {e}")
                break
                
    except Exception as e:
        print(f"xx STATE ERROR: {e}")

# ==========================================
# 3. MAIN LOOP
# ==========================================
def main():
    print(">> SYSTEM BOOT: LUMA SINGULARITY (70/30 ALLOCATION ACTIVE)")
    
    conf = load_config()
    hands = Hands(config=conf)
    vision = Vision()
    predator = Predator()
    deep_sea = DeepSea()
    xenomorph = Xenomorph()
    smart_money = SmartMoney()
    
    # Initialize Messenger (Reads Railway Vars)
    messenger = Messenger() 

    equity = STARTING_EQUITY
    cash = 0.0
    positions = []
    mode = "STANDARD"

    # Initial Log & Discord Alert
    log_permanent("System Booted. 70/30 Allocation Active.")
    messenger.send_info(f"Luma Online. Mode: {mode}. Equity: ${equity}")

    while True:
        try:
            # --- A. UPDATE ACCOUNT ---
            wallet = hands.wallet_address if hands else None
            acct = vision.get_user_state(wallet)
            
            if acct:
                equity = float(acct.get("marginSummary", {}).get("accountValue", equity))
                cash = float(acct.get("withdrawable", 0.0))
                raw_pos = acct.get("assetPositions", [])
                
                positions = []
                for p in raw_pos:
                    pos = p.get("position", {})
                    sz = float(pos.get("szi", 0))
                    if sz != 0:
                        # Direct API Fetch for Margin (No Calculation)
                        margin_used = float(pos.get("marginUsed", 0.0))
                        
                        positions.append({
                            "coin": pos.get("coin"), 
                            "size": sz,
                            "entry": float(pos.get("entryPx", 0)),
                            "pnl": float(pos.get("unrealizedPnl", 0)),
                            "margin": margin_used 
                        })

            # --- B. DETERMINE MODE & LEVERAGE ---
            current_roe = ((equity - STARTING_EQUITY) / STARTING_EQUITY) * 100
            
            if equity < STARTING_EQUITY: 
                mode = "RECOVERY"
            elif current_roe > 12.0 and equity > STARTING_EQUITY: 
                mode = "GOD MODE"
            else: 
                mode = "STANDARD"

            is_god_mode = (mode == "GOD MODE")
            for coin_name, cfg in FLEET_CONFIG.items():
                if cfg['type'] == 'PRINCE':
                    cfg['lev'] = 10 if is_god_mode else 5
                else:
                    cfg['lev'] = 5

            session = "LONDON/NY" 

            # --- C. SCANNER LOOP ---
            scan_data = []
            for coin in FLEET_CONFIG:
                try:
                    # Heartbeat
                    t = datetime.now().strftime("%H:%M:%S")
                    msg = f"[{t}] 🔍 SCANNING {coin}..."
                    print(f">> {msg}")
                    
                    # Update Dashboard State frequently
                    current_logs = list(EVENT_QUEUE)
                    current_logs.insert(0, msg)
                    save_dashboard_state(mode, session, equity, cash, positions, scan_data, current_logs, deep_sea.secured_coins)

                    # Fetch Data
                    candles = vision.get_candles(coin, "15m")
                    if not candles: continue
                    
                    curr_price = float(candles[-1]['c'])
                    c_type = FLEET_CONFIG[coin]['type']

                    # 1. Smart Money Signal
                    sm_sig = smart_money.hunt_turtle(candles, coin_type=c_type)
                    quality = "NEUTRAL"
                    if sm_sig: quality = sm_sig['type'] 

                    # 2. Xenomorph Override
                    xeno_sig = xenomorph.hunt(coin, candles)
                    if xeno_sig == "ATTACK": quality = "⚔️ BREAKOUT"

                    scan_data.append({
                        "coin": coin, "price": curr_price,
                        "vol_m": round(float(candles[-1]['v'])/1000000, 2),
                        "quality": quality
                    })
                    
                    # --- D. EXECUTION LOGIC ---
                    is_buy = "BUY" in str(quality) or "BREAKOUT" in str(quality)
                    is_sell = "SELL" in str(quality)

                    if is_buy or is_sell:
                        # Log to System
                        log_msg = f"[{t}] ⚡ SIGNAL: {coin} | {quality}"
                        EVENT_QUEUE.append(log_msg)
                        log_permanent(log_msg)
                        
                        # DYNAMIC SIZING (70/30 Rule)
                        alloc_size_usd = smart_money.calculate_position_size(equity)
                        
                        # [ACTION] Send Targeted Discord Alert
                        messenger.send_trade(
                            coin=coin, 
                            signal=quality, 
                            price=curr_price, 
                            size=alloc_size_usd
                        )
                        
                        active_coins = [p['coin'] for p in positions]
                        
                        if coin not in active_coins and alloc_size_usd > 5:
                            if hands:
                                side = "BUY" if is_buy else "SELL"
                                print(f">> 🔫 FIRING {side}: {coin} (Size: ${alloc_size_usd})")
                                
                                # Execute Order
                                hands.place_market_order(coin, side, alloc_size_usd)
                                log_permanent(f"Executed {side} on {coin} for ${alloc_size_usd}")
                        else:
                            print(f">> ⚠️ SKIPPING: Active or Low Equity (${alloc_size_usd})")

                    time.sleep(0.5)
                except Exception as e:
                    print(f"xx SCAN ERROR {coin}: {e}")

            # --- E. RISK MANAGEMENT ---
            risk_logs = deep_sea.manage_positions(hands, positions, FLEET_CONFIG, vision)
            if risk_logs:
                for log in risk_logs: 
                    full_log = f"[{t}] {log}"
                    EVENT_QUEUE.append(full_log)
                    log_permanent(full_log)
                    # Notify Discord of Risk Actions (Stops/Secures)
                    messenger.send_info(f"Risk Event: {log}")

            save_dashboard_state(mode, session, equity, cash, positions, scan_data, EVENT_QUEUE, deep_sea.secured_coins)
            
            # Sleep 3s before next full cycle
            time.sleep(3)

        except Exception as e:
            print(f"xx MAIN ERROR: {e}")
            log_permanent(f"CRITICAL MAIN LOOP ERROR: {e}")
            messenger.send_error(f"Main Loop Crash: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
