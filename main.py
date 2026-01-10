import time
import json
import sys
import os
import warnings
from collections import deque
from datetime import datetime, timezone

# --- CONFIGURATION ---
BTC_TICKER = "BTC"
STARTING_EQUITY = 412.0
MIN_EQUITY_THRESHOLD = 150.0 
DATA_DIR = "/app/data" if os.path.exists("/app/data") else "."
DASHBOARD_FILE = os.path.join(DATA_DIR, "dashboard_state.json")

# BLUE PRINCE + MEME FLEET
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
    """Saves the exact JSON structure required by the dashboard."""
    try:
        # Calculate Account ROE
        pnl = equity - STARTING_EQUITY
        roe = (pnl / STARTING_EQUITY) * 100 if STARTING_EQUITY > 0 else 0

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
        with open(DASHBOARD_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"xx DASHBOARD SAVE ERROR: {e}")

def main():
    print(">> SYSTEM BOOT: LUMA SINGULARITY (BLUE PRINCE RESTORED)")
    
    # 1. LOAD MODULES
    try:
        from hands import Hands
        from vision import Vision
        from predator import Predator
        from deep_sea import DeepSea
        from xenomorph import Xenomorph
        from messenger import Messenger
    except ImportError as e:
        print(f">> CRITICAL MISSING MODULE: {e}")
        print(">> RUN: pip install hyperliquid-python-sdk eth-account requests")
        sys.exit(1)

    # 2. INITIALIZE
    hands = Hands() # Connects to Hyperliquid
    vision = Vision()
    predator = Predator()
    xenomorph = Xenomorph()
    messenger = Messenger()
    
    # Verify Wallet Connection
    if not hands.wallet_address:
        print(">> WARNING: Hands not connected. Dashboard will be Read-Only.")

    equity = STARTING_EQUITY
    cash = 0.0
    positions = []
    mode = "STANDARD"

    while True:
        try:
            # --- A. UPDATE ACCOUNT INFO ---
            # We use the address from Hands to query the state
            addr = hands.wallet_address
            if addr:
                acct = vision.get_user_state(addr)
                if acct:
                    equity = float(acct.get("marginSummary", {}).get("accountValue", equity))
                    cash = float(acct.get("withdrawable", 0.0))
                    
                    # Format Positions for Dashboard
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

            # --- B. DETERMINE SESSION ---
            h = datetime.now(timezone.utc).hour
            if 7 <= h < 15: session = "LONDON/NY"
            elif 15 <= h < 21: session = "NY CLOSE"
            else: session = "ASIA"

            # --- C. SCANNER LOOP ---
            scan_results = []
            
            for coin in FLEET_CONFIG:
                # 1. Pulse Log
                log_msg = f"🔍 SCANNING {coin}..."
                print(f">> {log_msg}")
                
                # 2. Immediate Dashboard Update (So UI shows 'Scanning')
                temp_logs = list(EVENT_QUEUE)
                temp_logs.insert(0, log_msg)
                save_dashboard(mode, session, equity, cash, positions, scan_results, temp_logs)

                # 3. Fetch Data
                candles = vision.get_candles(coin, "15m")
                if not candles: continue
                
                curr_price = float(candles[-1]['c'])
                curr_vol = float(candles[-1]['v'])

                # 4. Analyze
                sig = predator.analyze_divergence(candles, coin) or "NEUTRAL"
                xeno = xenomorph.hunt(coin, candles)
                
                # 5. Add to Results
                scan_results.append({
                    "coin": coin,
                    "price": curr_price,
                    "vol_m": round(curr_vol / 1_000_000, 2), # Volume in Millions
                    "quality": sig,
                    "liquidity_price": 0.0 # Placeholder
                })
                
                # 6. Execution (Optional Hook)
                if xeno == "ATTACK":
                    EVENT_QUEUE.append(f"⚡ SIGNAL: {coin} BREAKOUT")
                
                time.sleep(1) # Rate limit safety

            # --- D. SAVE FINAL STATE ---
            save_dashboard(mode, session, equity, cash, positions, scan_results, EVENT_QUEUE)
            
            print(f">> CYCLE COMPLETE. Eq: ${equity:.2f}")
            time.sleep(15)

        except KeyboardInterrupt:
            print("\n>> SHUTDOWN.")
            break
        except Exception as e:
            print(f"xx LOOP ERROR: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
