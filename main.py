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

# --- FLEET CONFIG ---
FLEET_CONFIG = {
    "SOL":   {"type": "PRINCE", "lev": 5},
    "SUI":   {"type": "PRINCE", "lev": 5},
    "BNB":   {"type": "PRINCE", "lev": 5},
    "WIF":   {"type": "MEME",   "lev": 5},
    "DOGE":  {"type": "MEME",   "lev": 5},
    "PENGU": {"type": "MEME",   "lev": 5}
}

# Increased queue size for Verbose Logs
EVENT_QUEUE = deque(maxlen=50)

def load_config():
    # Prioritize Railway Env Vars
    pk = os.environ.get("PRIVATE_KEY")
    wallet = os.environ.get("WALLET_ADDRESS")
    if not pk:
        try:
            with open("server_config.json", 'r') as f: return json.load(f)
        except: return None
    return {"wallet_address": wallet, "private_key": pk}

def save_dashboard_state(mode, session, equity, cash, positions, scan_results, logs):
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
            "logs": list(logs) # Saves the full log history
        }
        # Atomic Write
        temp_file = DASHBOARD_FILE + ".tmp"
        with open(temp_file, 'w') as f:
            json.dump(dash_state, f)
        os.replace(temp_file, DASHBOARD_FILE)
    except Exception as e:
        print(f"xx STATE SAVE ERROR: {e}")

def main():
    print(">> SYSTEM BOOT: LUMA SINGULARITY (VERBOSE MODE)")
    
    conf = load_config()
    # Late import to avoid circular dependency crashes
    try:
        from hands import Hands
        from messenger import Messenger
        hands = Hands(config=conf)
        messenger = Messenger()
    except Exception as e:
        print(f">> WARNING: Hands/Messenger Init Failed: {e}")
        hands = None
        messenger = None

    vision = Vision()
    predator = Predator()
    xenomorph = Xenomorph()
    
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
                # --- VERBOSE LOGGING START ---
                t = datetime.now().strftime("%H:%M:%S")
                log_msg = f"[{t}] 🔍 SCANNING {coin}..."
                print(f">> {log_msg}")
                EVENT_QUEUE.appendleft(log_msg) # Add to Dashboard Log
                
                # Immediate Save so Dashboard updates "Scanning..." in real time
                save_dashboard_state(mode, session, equity, cash, positions, scan_data_for_dashboard, EVENT_QUEUE)
                # -----------------------------

                candles = vision.get_candles(coin, "15m")
                if not candles: 
                    EVENT_QUEUE.appendleft(f"[{t}] ⚠️ {coin}: No Data")
                    continue
                
                curr_price = float(candles[-1]['c'])
                quality = predator.analyze_divergence(candles, coin) or "WAITING"
                
                # Logic: If Xenomorph is active, override
                xeno_sig = xenomorph.hunt(coin, candles)
                if xeno_sig == "ATTACK": quality = "⚔️ BREAKOUT"

                # Append Result to Log
                if quality != "WAITING":
                    EVENT_QUEUE.appendleft(f"[{t}] 🎯 {coin}: {quality}")
                
                scan_data_for_dashboard.append({
                    "coin": coin,
                    "price": curr_price,
                    "vol_m": round(float(candles[-1]['v']) / 1000000, 2),
                    "quality": quality,
                    "liquidity_price": 0.0 
                })

                # --- EXECUTION BLOCK ---
                # This ensures we actually trade if Hands is ready
                if quality == "REAL_PUMP" or xeno_sig == "ATTACK":
                    if hands:
                        print(f">> EXECUTING ON {coin}")
                        # hands.place_trap(coin, "BUY", curr_price, 50.0) # Uncomment to arm
                
                time.sleep(0.5) 

            # 3. SAVE CYCLE END
            save_dashboard_state(mode, session, equity, cash, positions, scan_data_for_dashboard, EVENT_QUEUE)
            
            # 4. SLEEP
            print(f">> CYCLE PAUSE. Eq: ${equity:.2f}")
            time.sleep(5) 

        except Exception as e:
            print(f"xx LOOP ERROR: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
