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
    # from chronos import Chronos 
except ImportError as e:
    print(f">> CRITICAL ERROR: Missing Module {e}")
    sys.exit(1)

warnings.simplefilter("ignore")

# ==============================================================================
#  LUMA SINGULARITY [TIER: FINAL ARCHITECT]
#  Logic: Recovery (<412) | Standard (>412) | God (>12% ROE)
# ==============================================================================

# --- PATHS ---
DATA_DIR = "/app/data" if os.path.exists("/app/data") else "."
if not os.path.exists(DATA_DIR):
    try: os.makedirs(DATA_DIR)
    except: pass

DASHBOARD_FILE = os.path.join(DATA_DIR, "dashboard_state.json")
STATS_FILE = os.path.join(DATA_DIR, "stats.json")

# --- CORE CONFIGURATION ---
BTC_TICKER = "BTC"
# [CRITICAL] HARDCODED BASELINE. DO NOT CHANGE DYNAMICALLY.
STARTING_EQUITY = 412.0 
MIN_EQUITY_THRESHOLD = 150.0

FLEET_CONFIG = {
    "SOL":   {"type": "PRINCE", "lev": 5, "risk_mult": 1.0, "stop_loss": 0.04},
    "SUI":   {"type": "PRINCE", "lev": 5, "risk_mult": 1.0, "stop_loss": 0.04},
    "BNB":   {"type": "PRINCE", "lev": 5, "risk_mult": 1.0, "stop_loss": 0.04},
    "WIF":   {"type": "MEME",   "lev": 5, "risk_mult": 1.0, "stop_loss": 0.06},
    "DOGE":  {"type": "MEME",   "lev": 5, "risk_mult": 1.0, "stop_loss": 0.06},
    "PENGU": {"type": "MEME",   "lev": 5, "risk_mult": 1.0, "stop_loss": 0.06}
}

EVENT_QUEUE = deque(maxlen=50) 

# --- HELPERS ---
def load_config():
    pk = os.environ.get("PRIVATE_KEY")
    wallet = os.environ.get("WALLET_ADDRESS")
    if not pk:
        try:
            with open("server_config.json", 'r') as f: return json.load(f)
        except: return None
    return {"wallet_address": wallet, "private_key": pk}

def save_dashboard_state(mode, session, equity, cash, positions, scan_results, logs, secured_coins):
    """Saves the JSON state for app.py to read."""
    try:
        # Calculate Real PnL against the Hard Baseline
        pnl = equity - STARTING_EQUITY
        roe = (pnl / STARTING_EQUITY) * 100

        dash_state = {
            "mode": mode,
            "session": session,
            "equity": round(equity, 2),
            "cash": round(cash, 2),
            "pnl": round(pnl, 2),
            "account_roe": round(roe, 2),
            "positions": positions,
            "scan_results": scan_results,
            "logs": list(logs),
            "secured_coins": secured_coins
        }
        # Atomic Write
        temp_file = DASHBOARD_FILE + ".tmp"
        with open(temp_file, 'w') as f:
            json.dump(dash_state, f)
        os.replace(temp_file, DASHBOARD_FILE)
    except Exception as e:
        print(f"xx STATE SAVE ERROR: {e}")

# --- MAIN LOOP ---
def main():
    print(">> SYSTEM BOOT: LUMA SINGULARITY (RECOVERY PROTOCOL ENFORCED)")
    
    conf = load_config()
    from hands import Hands
    from messenger import Messenger

    hands = Hands(config=conf)
    vision = Vision()
    predator = Predator()
    deep_sea = DeepSea() # Handles stats.json internally
    xenomorph = Xenomorph()
    smart_money = SmartMoney()
    messenger = Messenger()

    equity = STARTING_EQUITY
    cash = 0.0
    positions = []
    mode = "STANDARD"
    session = "LONDON/NY"

    while True:
        try:
            # 1. UPDATE ACCOUNT
            wallet_addr = conf["wallet_address"] if conf else hands.wallet_address
            acct = vision.get_user_state(wallet_addr)
            
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

            # 2. DETERMINE MODE (STRICT LOGIC)
            pnl_pct = ((equity - STARTING_EQUITY) / STARTING_EQUITY) * 100
            
            if equity < STARTING_EQUITY:
                mode = "RECOVERY"
            elif pnl_pct > 12.0:
                mode = "GOD MODE"
            else:
                mode = "STANDARD"

            # 3. DETERMINE SESSION
            h = datetime.now(timezone.utc).hour
            if 7 <= h < 15: session = "LONDON/NY"
            elif 15 <= h < 21: session = "NY CLOSE"
            else: session = "ASIA"

            # 4. SCANNER LOOP
            scan_data = []
            
            for coin in FLEET_CONFIG:
                try:
                    # Log Pulse
                    t = datetime.now().strftime("%H:%M:%S")
                    pulse_msg = f"[{t}] 🔍 SCANNING {coin}..."
                    print(f">> {pulse_msg}")
                    
                    # Update Dashboard Immediately
                    current_logs = list(EVENT_QUEUE)
                    current_logs.insert(0, pulse_msg)
                    save_dashboard_state(mode, session, equity, cash, positions, scan_data, current_logs, deep_sea.secured_coins)

                    # Analysis
                    candles = vision.get_candles(coin, "15m")
                    if not candles: continue
                    
                    curr_price = float(candles[-1]['c'])
                    vol_m = float(candles[-1]['v']) / 1_000_000
                    
                    quality = predator.analyze_divergence(candles, coin) or "NEUTRAL"
                    xeno_sig = xenomorph.hunt(coin, candles)
                    if xeno_sig == "ATTACK": quality = "⚔️ BREAKOUT"

                    scan_data.append({
                        "coin": coin,
                        "price": curr_price,
                        "vol_m": round(vol_m, 2),
                        "quality": quality
                    })
                    
                    # Signal Log
                    if "BUY" in str(quality) or "SELL" in str(quality) or "BREAKOUT" in str(quality):
                        EVENT_QUEUE.append(f"[{t}] ⚡ SIGNAL: {coin} | {quality}")
                    
                    time.sleep(0.5)

                except Exception as e:
                    print(f"xx SCAN ERROR {coin}: {e}")

            # 5. RISK MANAGEMENT
            risk_logs = deep_sea.manage_positions(hands, positions, FLEET_CONFIG)
            if risk_logs:
                for log in risk_logs: EVENT_QUEUE.append(f"[{t}] {log}")

            # 6. END OF CYCLE SAVE
            save_dashboard_state(mode, session, equity, cash, positions, scan_data, EVENT_QUEUE, deep_sea.secured_coins)
            
            print(f">> CYCLE END: {mode} | ${equity:.2f}")
            time.sleep(5)

        except Exception as e:
            print(f"xx MAIN LOOP ERROR: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
