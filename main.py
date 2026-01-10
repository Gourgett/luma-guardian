import time
import json
import sys
import os
import warnings
from collections import deque
from datetime import datetime, timezone

# --- RAILWAY CONFIGURATION ---
# We prioritize Environment Variables (Railway) over local files
def get_env(key, default=None):
    return os.getenv(key, default)

# 1. SETUP PATHS (Critical for Railway Persistence)
# Railway often requires writing to specific temp or data directories
BASE_DIR = os.getcwd()
DATA_DIR = os.path.join(BASE_DIR, "data")

# Create data directory if it doesn't exist
if not os.path.exists(DATA_DIR):
    try:
        os.makedirs(DATA_DIR)
    except OSError:
        # Fallback to tmp if permission denied
        DATA_DIR = "/tmp"

DASHBOARD_FILE = os.path.join(DATA_DIR, "dashboard_state.json")

# 2. FLEET CONFIGURATION (The Blue Princes)
FLEET_CONFIG = {
    "SOL":   {"type": "PRINCE", "lev": 5},
    "SUI":   {"type": "PRINCE", "lev": 5},
    "BNB":   {"type": "PRINCE", "lev": 5},
    "WIF":   {"type": "MEME",   "lev": 5},
    "DOGE":  {"type": "MEME",   "lev": 5},
    "PENGU": {"type": "MEME",   "lev": 5}
}

EVENT_QUEUE = deque(maxlen=20)
warnings.simplefilter("ignore")

def save_dashboard(mode, session, equity, cash, positions, scan_data, logs):
    """Saves the JSON state for app.py to read."""
    try:
        pnl = equity - float(get_env("STARTING_EQUITY", 412.0))
        roe = (pnl / float(get_env("STARTING_EQUITY", 412.0))) * 100

        data = {
            "mode": mode,
            "session": session,
            "equity": round(equity, 2),
            "cash": round(cash, 2),
            "pnl": round(pnl, 2),
            "account_roe": round(roe, 2),
            "positions": positions,
            "scan_results": scan_data,
            "logs": list(logs),
            "updated": time.time()
        }
        
        # Atomic write to prevent file corruption
        temp_file = DASHBOARD_FILE + ".tmp"
        with open(temp_file, 'w') as f:
            json.dump(data, f)
        os.replace(temp_file, DASHBOARD_FILE)
        
    except Exception as e:
        print(f"xx DASHBOARD SAVE ERROR: {e}")

def main():
    print(">> SYSTEM BOOT: LUMA SINGULARITY (RAILWAY PROTOCOL)")
    print(f">> STORAGE PATH: {DASHBOARD_FILE}")

    # 1. LOAD MODULES & INJECT CONFIG
    # We create a config dict from Env Vars to pass to modules
    railway_config = {
        "private_key": get_env("PRIVATE_KEY"),
        "wallet_address": get_env("WALLET_ADDRESS"),
        "rpc_url": get_env("RPC_URL", "https://api.hyperliquid.xyz/info"),
        "discord_webhook": get_env("DISCORD_WEBHOOK")
    }

    try:
        from hands import Hands
        from vision import Vision
        from predator import Predator
        from deep_sea import DeepSea
        from xenomorph import Xenomorph
        from messenger import Messenger
    except ImportError as e:
        print(f">> CRITICAL MISSING MODULE: {e}")
        sys.exit(1)

    # 2. INITIALIZE MODULES (Robust)
    try:
        # Pass the railway config directly to Hands if it accepts it, 
        # otherwise Hands should look for os.getenv internally.
        hands = Hands(config=railway_config)
    except Exception as e:
        print(f">> HANDS INIT ERROR: {e}")
        hands = None

    vision = Vision()
    predator = Predator()
    xenomorph = Xenomorph()
    messenger = Messenger()

    # 3. STATE VARIABLES
    equity = float(get_env("STARTING_EQUITY", 412.0))
    cash = 0.0
    positions = []
    mode = "STANDARD"

    # 4. MAIN LOOP
    while True:
        try:
            # --- A. UPDATE ACCOUNT (If Hands is Alive) ---
            if hands and hasattr(hands, 'wallet_address') and hands.wallet_address:
                try:
                    # Logic assumes Vision can fetch user state using the address
                    # Note: You might need to adjust this depending on your Vision.py logic
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
                except Exception as e:
                    print(f"xx ACCOUNT SYNC ERROR: {e}")
            else:
                # If hands failed, we just log it but KEEP RUNNING the scanner
                if "⚠️ Wallet Disconnected" not in EVENT_QUEUE:
                    EVENT_QUEUE.append("⚠️ Wallet Disconnected - View Only")

            # --- B. DETERMINE SESSION ---
            h = datetime.now(timezone.utc).hour
            if 7 <= h < 15: session = "LONDON/NY"
            elif 15 <= h < 21: session = "NY CLOSE"
            else: session = "ASIA"

            # --- C. SCANNER LOOP ---
            scan_results = []
            
            for coin in FLEET_CONFIG:
                # Log Pulse
                print(f">> Scanning {coin}...")
                
                # Fetch Data
                candles = vision.get_candles(coin, "15m")
                if not candles: continue
                
                curr_price = float(candles[-1]['c'])
                curr_vol = float(candles[-1]['v'])

                # Analyze
                sig = predator.analyze_divergence(candles, coin) or "NEUTRAL"
                
                scan_results.append({
                    "coin": coin,
                    "price": curr_price,
                    "vol_m": round(curr_vol / 1_000_000, 2),
                    "quality": sig
                })
                
                time.sleep(0.5)

            # --- D. SAVE STATE ---
            save_dashboard(mode, session, equity, cash, positions, scan_results, EVENT_QUEUE)
            print(f">> CYCLE COMPLETE. Eq: ${equity:.2f}")
            time.sleep(10)

        except KeyboardInterrupt:
            print("\n>> SHUTDOWN.")
            break
        except Exception as e:
            print(f"xx LOOP ERROR: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
