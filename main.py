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
except ImportError as e:
    print(f">> CRITICAL ERROR: Missing Module {e}")
    sys.exit(1)

warnings.simplefilter("ignore")

# ==============================================================================
#  LUMA SINGULARITY [TIER: FINAL ARCHITECT]
#  Logic: Recovery (<412) | Standard (>412) | God (>12% ROE)
# ==============================================================================

DATA_DIR = "/app/data" if os.path.exists("/app/data") else "."
if not os.path.exists(DATA_DIR):
    try: os.makedirs(DATA_DIR)
    except: pass

DASHBOARD_FILE = os.path.join(DATA_DIR, "dashboard_state.json")
STARTING_EQUITY = 412.0
MIN_EQUITY_THRESHOLD = 150.0

FLEET_CONFIG = {
    "SOL":   {"type": "PRINCE", "lev": 5},
    "SUI":   {"type": "PRINCE", "lev": 5},
    "BNB":   {"type": "PRINCE", "lev": 5},
    "WIF":   {"type": "MEME",   "lev": 5},
    "DOGE":  {"type": "MEME",   "lev": 5},
    "PENGU": {"type": "MEME",   "lev": 5}
}

EVENT_QUEUE = deque(maxlen=50)

def load_config():
    pk = os.environ.get("PRIVATE_KEY")
    wallet = os.environ.get("WALLET_ADDRESS")
    if not pk:
        try:
            with open("server_config.json", 'r') as f: return json.load(f)
        except: return None
    return {"wallet_address": wallet, "private_key": pk}

def save_dashboard_state(mode, session, equity, cash, positions, scan_results, logs, secured_coins):
    """
    Updates the dashboard JSON.
    NOW INCLUDES: 'secured_coins' list from Deep Sea.
    """
    try:
        dash_state = {
            "mode": mode,
            "session": session,
            "equity": round(equity, 2),
            "cash": round(cash, 2),
            "pnl": round(equity - STARTING_EQUITY, 2),
            "account_roe": round(((equity - STARTING_EQUITY) / STARTING_EQUITY) * 100, 2),
            "positions": positions,
            "scan_results": scan_results,
            "logs": list(logs),
            "secured_coins": secured_coins # <--- NEW DATA POINT
        }
        temp_file = DASHBOARD_FILE + ".tmp"
        with open(temp_file, 'w') as f:
            json.dump(dash_state, f)
        os.replace(temp_file, DASHBOARD_FILE)
    except Exception as e:
        print(f"xx STATE SAVE ERROR: {e}")

def main():
    print(">> SYSTEM BOOT: LUMA SINGULARITY (DEEP SEA ACTIVE)")
    
    conf = load_config()
    hands = Hands(config=conf)
    messenger = Messenger()
    vision = Vision()
    predator = Predator()
    xenomorph = Xenomorph()
    deep_sea = DeepSea() # Risk Manager
    
    equity = STARTING_EQUITY
    cash = 0.0
    positions = []
    mode = "STANDARD"
    session = "LONDON/NY"

    while True:
        try:
            # 1. MARKET PULSE
            if hands and hands.wallet_address:
                acct = vision.get_user_state(hands.wallet_address)
                if acct:
                    equity = float(acct.get("marginSummary", {}).get("accountValue", equity))
                    cash = float(acct.get("withdrawable", 0.0))
                    
                    raw_pos = acct.get("assetPositions", [])
                    positions = []
                    for p in raw_pos:
                        pos = p.get("position", {})
                        sz = float(pos.get("szi", 0))
                        if sz != 0:
                            positions.append({
                                "coin": pos.get("coin"),
                                "size": sz,
                                "entry": float(pos.get("entryPx", 0)),
                                "pnl": float(pos.get("unrealizedPnl", 0))
                            })

            # 2. SCANNER LOOP
            scan_data_for_dashboard = [] 
            
            for coin in FLEET_CONFIG:
                # Heartbeat Log
                t = datetime.now().strftime("%H:%M:%S")
                pulse_msg = f"[{t}] 🔍 SCANNING {coin}..."
                print(f">> {pulse_msg}")
                
                # Transient Log for Dashboard
                current_logs = list(EVENT_QUEUE)
                current_logs.insert(0, pulse_msg)
                
                # PASS SECURED COINS TO DASHBOARD
                save_dashboard_state(mode, session, equity, cash, positions, scan_data_for_dashboard, current_logs, deep_sea.secured_coins)

                # Fetch & Analyze
                candles = vision.get_candles(coin, "15m")
                if not candles: continue
                
                curr_price = float(candles[-1]['c'])
                quality = predator.analyze_divergence(candles, coin) or "WAITING"
                xeno_sig = xenomorph.hunt(coin, candles)
                
                if xeno_sig == "ATTACK": quality = "⚔️ BREAKOUT"

                scan_data_for_dashboard.append({
                    "coin": coin,
                    "price": curr_price,
                    "vol_m": round(float(candles[-1]['v']) / 1000000, 2),
                    "quality": quality,
                    "liquidity_price": 0.0 
                })

                if quality == "REAL_PUMP" or xeno_sig == "ATTACK":
                    log = f"[{t}] ⚡ SIGNAL: {coin} | {quality}"
                    EVENT_QUEUE.append(log)
                    # hands.place_trap(coin, "BUY", curr_price, 50.0) # ARM THIS WHEN READY

                time.sleep(0.5)

            # 3. DEEP SEA MANAGEMENT (Active)
            # This calculates stops/breakevens and updates the secured_coins list
            risk_logs = deep_sea.manage_positions(hands, positions, FLEET_CONFIG)
            if risk_logs:
                for log in risk_logs:
                    EVENT_QUEUE.append(f"[{datetime.now().strftime('%H:%M:%S')}] {log}")

            # 4. FINAL SAVE
            save_dashboard_state(mode, session, equity, cash, positions, scan_data_for_dashboard, EVENT_QUEUE, deep_sea.secured_coins)
            
            print(f">> CYCLE PAUSE. Eq: ${equity:.2f}")
            time.sleep(5) 

        except Exception as e:
            print(f"xx LOOP ERROR: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
