import json
import os
import time
from datetime import datetime

class DeepSea:
    def __init__(self):
        print(">> DEEP SEA: Ratchet System Loaded (Mode: VOLATILITY SURVIVOR)")
        
        # PATHS (Matches your Railway/Main setup)
        self.DATA_DIR = "/app/data" if os.path.exists("/app/data") else "."
        self.STATS_FILE = os.path.join(self.DATA_DIR, "stats.json")
        
        # STATE VARIABLES
        self.secured_coins = []
        self.peak_roe = {}
        self.trauma_record = {}
        
        # Load History for Dashboard Sidebar
        self.stats = self._load_stats()

    def _load_stats(self):
        """Loads trade history for the Dashboard sidebar."""
        if os.path.exists(self.STATS_FILE):
            try:
                with open(self.STATS_FILE, 'r') as f: return json.load(f)
            except: pass
        return {"wins": 0, "losses": 0, "history": []}

    def _save_stats(self):
        """Saves trade history so sidebar persists after restart."""
        try:
            with open(self.STATS_FILE, 'w') as f: json.dump(self.stats, f)
        except Exception as e:
            print(f"xx STATS SAVE ERROR: {e}")

    def _record_trade(self, coin, pnl, outcome):
        """Updates the Wins/Losses counter."""
        self.stats['history'].insert(0, {
            "coin": coin,
            "pnl": round(pnl, 2),
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "outcome": outcome
        })
        # Keep history trimmed to last 50 trades
        self.stats['history'] = self.stats['history'][:50]
        
        if outcome == "WIN": self.stats['wins'] += 1
        else: self.stats['losses'] += 1
        
        self._save_stats()

    def check_trauma(self, hands, coin):
        # 5-Minute Cooldown for LOSSES only.
        last_loss = self.trauma_record.get(coin, 0)
        if time.time() - last_loss < 300:
            return True # BLOCK TRADES
        return False

    def manage_positions(self, hands, positions, fleet_config):
        events = []
        self.secured_coins = [] # Reset for this cycle to re-verify

        # Cleanup peaks for closed positions
        current_coins = [p['coin'] for p in positions]
        for c in list(self.peak_roe.keys()):
            if c not in current_coins: del self.peak_roe[c]

        for p in positions:
            coin = p['coin']
            size = float(p['size'])
            entry = float(p['entry'])
            pnl = float(p['pnl'])
            
            if size == 0: continue

            # CONFIG & ROE CALCULATION
            rules = fleet_config.get(coin, {})
            # Default to 5x if not found, avoids crash
            leverage = float(rules.get('lev', 5)) 
            
            margin = (abs(size) * entry) / leverage if leverage > 0 else 1
            if margin == 0: continue
            roe = pnl / margin

            # TRACK PEAK ROE
            if coin not in self.peak_roe: self.peak_roe[coin] = roe
            else:
                if roe > self.peak_roe[coin]: self.peak_roe[coin] = roe
            
            peak = self.peak_roe[coin]

            # --- VOLATILITY SURVIVOR STRATEGY ---

            # 1. HARD STOP LOSS
            stop_loss_val = rules.get('stop_loss', 0.08)
            current_floor = -(stop_loss_val)

            # 2. EARLY BREAKEVEN (Trigger at 1.5% ROE)
            if peak >= 0.015:
                current_floor = 0.002 # Lock small profit

            # 3. THE "RUNNER" TRAIL (Trigger at 4.0% ROE)
            if peak >= 0.04:
                current_floor = peak - 0.02

            # --- STATUS CHECK FOR DASHBOARD ---
            # If current floor is positive, we are "Secured"
            if current_floor > 0:
                self.secured_coins.append(coin)

            # --- EXECUTION CHECK ---
            if roe < current_floor:
                tag = "STOP LOSS" if current_floor < 0 else "PROFIT SECURED"
                outcome = "LOSS" if current_floor < 0 else "WIN"
                
                # Trauma Record (Only on losses)
                if outcome == "LOSS":
                    self.trauma_record[coin] = time.time()

                if hands:
                    print(f">> 📉 CLOSING {coin} ({tag})")
                    hands.place_market_order(coin, "SELL" if size > 0 else "BUY", abs(size))
                    
                    # RECORD STATS FOR SIDEBAR
                    self._record_trade(coin, pnl, outcome)

                pnl_str = f"{pnl:+.2f}"
                events.append(f"💰 {tag}: {coin} ({pnl_str} | {roe*100:.1f}%)")

            # EMERGENCY HARD STOP (-50%)
            elif roe < -0.50:
                if hands:
                    hands.place_market_order(coin, "SELL" if size > 0 else "BUY", abs(size))
                    self._record_trade(coin, pnl, "LOSS")
                
                self.trauma_record[coin] = time.time()
                events.append(f"xx EMERGENCY CUT: {coin}")

        return events
