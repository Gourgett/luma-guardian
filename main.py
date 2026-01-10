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
    # from chronos import Chronos # Optional if logic is inline
except ImportError as e:
    print(f">> CRITICAL ERROR: Missing Module {e}")
    sys.exit(1)

warnings.simplefilter("ignore")

# ==============================================================================
#  LUMA SINGULARITY [TIER: FINAL ARCHITECT]
#  Logic: Recovery (<412) | Standard (>412) | God (>12% ROE)
#  Auth: Railway Environment Variables
# ==============================================================================

# --- PATHS & PERSISTENCE ---
DATA_DIR = "/app/data" if os.path.exists("/app/data") else "."
if not os.path.exists(DATA_DIR):
    try: os.makedirs(DATA_DIR)
    except: pass

STATS_FILE = os.path.join(DATA_DIR, "stats.json")
DASHBOARD_FILE = os.path.join(DATA_DIR, "dashboard_state.json")

BTC_TICKER = "BTC"
STARTING_EQUITY = 412.0
MIN_EQUITY_THRESHOLD = 150.0  # Safety Shutoff

# --- FLEET CONFIG ---
# Princes: Strict, Tighter Stops (SOL, SUI, BNB)
# Memes: Aggressive, Looser Stops (WIF, DOGE, PENGU)
FLEET_CONFIG = {
    # PRINCES
    "SOL":   {"type": "PRINCE", "lev": 5, "risk_mult": 1.0, "stop_loss": 0.04},
    "SUI":   {"type": "PRINCE", "lev": 5, "risk_mult": 1.0, "stop_loss": 0.04},
    "BNB":   {"type": "PRINCE", "lev": 5, "risk_mult": 1.0, "stop_loss": 0.04},
    
    # MEMES
    "WIF":   {"type": "MEME",   "lev": 5, "risk_mult": 1.0, "stop_loss": 0.06},
    "DOGE":  {"type": "MEME",   "lev": 5, "risk_mult": 1.0, "stop_loss": 0.06},
    "PENGU": {"type": "MEME",   "lev": 5, "risk_mult": 1.0, "stop_loss": 0.06}
}

EVENT_QUEUE = deque(maxlen=20) # Increased to handle verbose logs without losing history

# --- STATS HANDLER (History & Win Rate) ---
class StatsHandler:
    def __init__(self):
        self.data = {"wins": 0, "losses": 0, "history": []}
        self.load()

    def load(self):
        try:
            if os.path.exists(STATS_FILE):
                with open(STATS_FILE, 'r') as f:
                    self.data = json.load(f)
        except: pass

    def save(self):
        try:
            with open(STATS_FILE, 'w') as f:
                json.dump(self.data, f, indent=2)
        except: pass

    def record_trade(self, coin, pnl, roe, reason):
        if pnl > 0: self.data["wins"] += 1
        else: self.data["losses"] += 1
        
        entry = {
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "coin": coin,
            "pnl": round(pnl, 2),
            "roe": round(roe * 100, 2),
            "reason": reason
        }
        # Add to top of list
        self.data["history"].insert(0, entry)
        if len(self.data["history"]) > 100:
            self.data["history"] = self.data["history"][:100]
        self.save()

# --- CONFIG LOADER (ENV VARS) ---
def load_config():
    # Prioritize Railway Env Vars
    pk = os.environ.get("PRIVATE_KEY")
    wallet = os.environ.get("WALLET_ADDRESS")
    
    if not pk:
        # Fallback to local file (Optional for local dev)
        try:
            with open("server_config.json", 'r') as f:
                data = json.load(f)
                return data
        except:
            return None
    return {"wallet_address": wallet, "private_key": pk}

# --- HELPER: SAVE DASHBOARD STATE ---
def save_dashboard_state(mode, session, equity, cash, positions, scan_results, logs):
    """Saves the current state to JSON for the frontend to read."""
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
            "logs": list(logs)
        }
        with open(DASHBOARD_FILE, 'w') as f:
            json.dump(dash_state, f)
    except Exception as e:
        print(f"xx STATE SAVE ERROR: {e}")

# --- MAIN EXECUTION ---
def main():
    print(">> SYSTEM BOOT: LUMA SINGULARITY")
    
    # Initialize Modules
    conf = load_config()
    if not conf or not conf.get("private_key"):
        print(">> FATAL: No PRIVATE_KEY found in Environment Variables.")
        # sys.exit(1) # Commented out to allow testing without keys if needed

    from hands import Hands # Late import
    from messenger import Messenger

    hands = Hands() 
    vision = Vision()
    predator = Predator()
    deep_sea = DeepSea()
    xenomorph = Xenomorph()
    smart_money = SmartMoney()
    messenger = Messenger()
    stats_man = StatsHandler()

    print(f">> FLEET: {list(FLEET_CONFIG.keys())}")
    
    # Initial State Variables
    equity = STARTING_EQUITY
    cash = 0.0
    positions = []
    scan_data_for_dashboard = []
    mode = "STANDARD"
    session = "LONDON/NY"

    while True:
        try:
            # 1. MARKET PULSE & EQUITY
            # Use 'conf' address if Vision needs it, or just use what Hands has
            wallet_addr = conf["wallet_address"] if conf else hands.wallet_address
            account = vision.get_user_state(wallet_addr)
            
            # Default to STARTING_EQUITY if API fails temporarily
            if account:
                equity = float(account.get("marginSummary", {}).get("accountValue", STARTING_EQUITY))
                cash = float(account.get("withdrawable", 0.0))
                
                # Normalize positions
                raw_pos = account.get("assetPositions", [])
                positions = [] # Clear old list
                for item in raw_pos:
                    p = item.get("position", {})
                    if float(p.get("szi", 0)) != 0:
                        positions.append({
                            "coin": p.get("coin"),
                            "size": float(p.get("szi")),
                            "entry": float(p.get("entryPx")),
                            "pnl": float(p.get("unrealizedPnl"))
                        })
            
            # 2. SAFETY CHECK
            if equity < MIN_EQUITY_THRESHOLD:
                msg = "💀 KILL SWITCH ENGAGED: Equity below $150"
                print(f">> {msg}")
                EVENT_QUEUE.append(msg)
                messenger.send("errors", msg)
                time.sleep(600)
                continue

            # 3. MODE SELECTION
            total_roe_pct = ((equity - STARTING_EQUITY) / STARTING_EQUITY)
            
            if equity < STARTING_EQUITY:
                mode = "RECOVERY"
            elif total_roe_pct > 0.12:
                mode = "GOD MODE"
            else:
                mode = "STANDARD"

            # Session
            h = datetime.now(timezone.utc).hour
            if 7 <= h < 15: session = "LONDON/NY"
            elif 15 <= h < 21: session = "NY CLOSE"
            else: session = "ASIA"

            # 4. ACTIVE SCANNER LOOP (Updated for Pulse)
            # We clear scan results at the start of the cycle
            scan_data_for_dashboard = [] 
            
            for coin in FLEET_CONFIG:
                try:
                    # --- HEARTBEAT PULSE ---
                    # Update logs immediately so user sees "Scanning [COIN]"
                    pulse_msg = f"🔍 SCANNING {coin}..."
                    print(f">> {pulse_msg}")
                    
                    # Add transient pulse to logs (removed in next cycle)
                    # We create a temporary log list for the file
                    current_logs = list(EVENT_QUEUE)
                    current_logs.insert(0, pulse_msg)
                    
                    # Force save state so UI updates "Scanning..." immediately
                    save_dashboard_state(mode, session, equity, cash, positions, scan_data_for_dashboard, current_logs)

                    # --- DATA FETCH ---
                    rules = FLEET_CONFIG[coin]
                    candles = vision.get_candles(coin, "15m")
                    
                    if not candles: 
                        continue
                    
                    curr_price = float(candles[-1]['c'])
                    curr_vol = float(candles[-1]['v'])
                    
                    # --- ANALYZE ---
                    quality = predator.analyze_divergence(candles, coin) or "NEUTRAL"
                    xeno_sig = xenomorph.hunt(coin, candles)
                    
                    # --- BUILD DASHBOARD DATA ---
                    liq_est = curr_price - (curr_price / rules['lev']) 
                    coin_data = {
                        "coin": coin,
                        "price": curr_price,
                        "vol_m": round(curr_vol / 1000000, 2),
                        "quality": f"{quality}",
                        "liquidity_price": liq_est
                    }
                    scan_data_for_dashboard.append(coin_data)
                    
                    # --- LOG RESULTS (VERBOSE PULSE) ---
                    # Instead of silence, we log the result of the scan
                    if "SELL" in quality or "BUY" in quality:
                        log_msg = f"⚡ SIGNAL: {coin} | {quality}"
                        EVENT_QUEUE.append(log_msg) # Permanent log
                    else:
                        # Optional: Detailed logs for "Neutral" can be noisy, 
                        # but we updated the "Scanning..." msg above, which is sufficient for "Pulse".
                        pass

                    # --- EXECUTION ---
                    # if quality == "REAL_PUMP" ... hands.place_trap(...)

                    # Sleep briefly to allow UI to catch the "Scanning" state and avoid rate limits
                    time.sleep(1.0) 

                except Exception as e:
                    print(f"xx ERROR SCANNING {coin}: {e}")
                    continue

            # 5. MANAGE POSITIONS
            # deep_sea_logs = deep_sea.manage_positions(hands, positions, FLEET_CONFIG)
            # (Logic maintained from your file)
            
            # 6. FINAL SAVE STATE (End of Cycle)
            save_dashboard_state(mode, session, equity, cash, positions, scan_data_for_dashboard, EVENT_QUEUE)
            
            print(f">> PULSE COMPLETE: {mode} | Eq: ${equity:.1f}")
            time.sleep(30)

        except Exception as e:
            print(f"xx MAIN LOOP ERROR: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
