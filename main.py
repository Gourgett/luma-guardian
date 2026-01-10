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

EVENT_QUEUE = deque(maxlen=10)

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
    
    if not pk or not wallet:
        # Fallback to local file (Optional for local dev)
        try:
            with open("server_config.json", 'r') as f:
                data = json.load(f)
                return data
        except:
            return None
    return {"wallet_address": wallet, "private_key": pk}

# --- MAIN EXECUTION ---
def main():
    print(">> SYSTEM BOOT: LUMA SINGULARITY")
    
    # Initialize Modules
    conf = load_config()
    if not conf or not conf.get("private_key"):
        print(">> FATAL: No PRIVATE_KEY found in Environment Variables.")
        sys.exit(1)

    from hands import Hands # Late import to avoid config issues
    from messenger import Messenger

    hands = Hands() # Hands will now look for Env Vars too or we pass them if modified
    # NOTE: Your 'hands.py' reads server_config.json. 
    # I am assuming your 'hands.py' works, but ideally it should accept keys or read envs.
    # If your hands.py fails, let me know, I will patch it. 
    # For now, I'll assume it finds the keys via its own logic or the file you might still have.
    # BEST PRACTICE: I will patch Hands initialization here if needed, but 'hands.py' was not requested to change.
    
    vision = Vision()
    predator = Predator()
    deep_sea = DeepSea()
    xenomorph = Xenomorph()
    smart_money = SmartMoney()
    messenger = Messenger() # Will use Env Vars
    stats_man = StatsHandler()

    print(f">> FLEET: {list(FLEET_CONFIG.keys())}")
    
    while True:
        try:
            # 1. MARKET PULSE & EQUITY
            # Use 'conf' address if Vision needs it, or just use what Hands has
            account = vision.get_user_state(conf["wallet_address"])
            
            # Default to STARTING_EQUITY if API fails temporarily
            equity = STARTING_EQUITY
            cash = 0.0
            positions = []
            
            if account:
                equity = float(account.get("marginSummary", {}).get("accountValue", STARTING_EQUITY))
                cash = float(account.get("withdrawable", 0.0))
                # Normalize positions would go here
                # Simplified for this snippet:
                raw_pos = account.get("assetPositions", [])
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
                print(">> 💀 KILL SWITCH ENGAGED: EQUITY BELOW 150")
                EVENT_QUEUE.append("💀 KILL SWITCH ENGAGED")
                messenger.send("errors", "💀 KILL SWITCH ENGAGED: Equity below $150")
                time.sleep(600)
                continue

            # 3. MODE SELECTION
            total_roe_pct = ((equity - STARTING_EQUITY) / STARTING_EQUITY)
            
            if equity < STARTING_EQUITY:
                mode = "RECOVERY"
                global_risk_mult = 0.5
            elif total_roe_pct > 0.12:
                mode = "GOD MODE"
                global_risk_mult = 2.0
            else:
                mode = "STANDARD"
                global_risk_mult = 1.0

            # Session
            h = datetime.now(timezone.utc).hour
            if 7 <= h < 15: session = "LONDON/NY"
            elif 15 <= h < 21: session = "NY CLOSE"
            else: session = "ASIA"

            # 4. SCANNER & TRADING
            scan_data_for_dashboard = []
            
            for coin in FLEET_CONFIG:
                rules = FLEET_CONFIG[coin]
                
                candles = vision.get_candles(coin, "15m")
                if not candles: continue
                
                curr_price = float(candles[-1]['c'])
                curr_vol = float(candles[-1]['v'])
                
                # A. ANALYZE
                quality = predator.analyze_divergence(candles, coin) or "NEUTRAL"
                xeno_sig = xenomorph.hunt(coin, candles)
                
                # B. DASHBOARD DATA
                liq_est = curr_price - (curr_price / rules['lev']) 
                scan_data_for_dashboard.append({
                    "coin": coin,
                    "price": curr_price,
                    "vol_m": round(curr_vol / 1000000, 2),
                    "quality": f"{quality}", # Simplified for display
                    "liquidity_price": liq_est
                })

                # C. EXECUTION (Placeholder for your blueprint logic)
                # If quality == "REAL_PUMP" and not in positions...
                # hands.place_trap(...)
                
            # 5. MANAGE POSITIONS
            # Get fresh positions from Hands if possible, or use Vision data
            # positions = hands.get_positions() 
            deep_sea_logs = deep_sea.manage_positions(hands, positions, FLEET_CONFIG)
            
            if deep_sea_logs:
                for log in deep_sea_logs:
                    EVENT_QUEUE.append(log)
                    messenger.send("trades", log) # Notify Discord
                    if "PROFIT" in log or "STOP LOSS" in log:
                        try:
                            # Parse log: "💰 PROFIT SECURED: WIF (+5.20 | 10.5%)"
                            parts = log.split(":")
                            c_name = parts[1].split("(")[0].strip()
                            val_str = log.split("(")[1].split("|")[0].strip()
                            pnl_val = float(val_str)
                            stats_man.record_trade(c_name, pnl_val, 0, log)
                        except: pass

            # 6. SAVE STATE
            dash_state = {
                "mode": mode,
                "session": session,
                "equity": round(equity, 2),
                "cash": round(cash, 2),
                "pnl": round(equity - STARTING_EQUITY, 2),
                "account_roe": round(total_roe_pct * 100, 2),
                "positions": positions,
                "scan_results": scan_data_for_dashboard,
                "logs": list(EVENT_QUEUE)
            }
            
            with open(DASHBOARD_FILE, 'w') as f:
                json.dump(dash_state, f)
            
            print(f">> PULSE: {mode} | Eq: ${equity:.1f} | Active: {len(positions)}")
            time.sleep(30)

        except Exception as e:
            print(f"xx MAIN LOOP ERROR: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
