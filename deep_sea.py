import json
import os
import time
from datetime import datetime

class DeepSea:
    def __init__(self):
        print(">> DEEP SEA: Smooth Trailing System Loaded")
        self.DATA_DIR = "/app/data" if os.path.exists("/app/data") else "."
        self.STATS_FILE = os.path.join(self.DATA_DIR, "stats.json")
        
        self.secured_coins = []
        self.highest_prices = {} # Tracks highest price seen for trailing
        self.stats = self._load_stats()

    def _load_stats(self):
        if os.path.exists(self.STATS_FILE):
            try: with open(self.STATS_FILE, 'r') as f: return json.load(f)
            except: pass
        return {"wins": 0, "losses": 0, "history": []}

    def _save_stats(self):
        try: with open(self.STATS_FILE, 'w') as f: json.dump(self.stats, f)
        except: pass

    def _record_trade(self, coin, pnl, outcome):
        self.stats['history'].insert(0, {
            "coin": coin, "pnl": round(pnl, 2),
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"), "outcome": outcome
        })
        self.stats['history'] = self.stats['history'][:50]
        if outcome == "WIN": self.stats['wins'] += 1
        else: self.stats['losses'] += 1
        self._save_stats()

    def manage_positions(self, hands, positions, fleet_config, vision_module):
        events = []
        self.secured_coins = [] 

        current_coins = [p['coin'] for p in positions]
        # Clean up old price trackers
        for c in list(self.highest_prices.keys()):
            if c not in current_coins: del self.highest_prices[c]

        for p in positions:
            coin = p['coin']
            size = float(p['size'])
            entry = float(p['entry'])
            pnl = float(p['pnl'])
            
            if size == 0: continue

            # 1. Get Live Price
            curr_price = vision_module.get_price(coin)
            if curr_price == 0: continue

            # 2. Update Highest Price Seen (The "High Water Mark")
            if coin not in self.highest_prices: self.highest_prices[coin] = max(entry, curr_price)
            if curr_price > self.highest_prices[coin]: self.highest_prices[coin] = curr_price
            
            high_water = self.highest_prices[coin]

            # 3. Determine Trail Gap based on Type
            c_type = fleet_config.get(coin, {}).get('type', 'MEME')
            
            # PRINCES: 3% Hard Stop, Trailing 1.5%
            # MEMES:   5% Hard Stop, Trailing 2.0% (Looser)
            if c_type == 'PRINCE':
                trail_percent = 0.015
                hard_stop_pct = 0.03
            else:
                trail_percent = 0.020 
                hard_stop_pct = 0.05

            # 4. Calculate Dynamic Stop Price
            # The stop is "Trail Percent" below the Highest Price Seen
            trailing_stop_price = high_water * (1 - trail_percent)
            
            # 5. Calculate Hard Stop Price (Fixed from Entry)
            hard_stop_price = entry * (1 - hard_stop_pct)

            # The effective stop is whichever is HIGHER (safer)
            # This ensures we respect the hard stop initially, but the trail takes over if price pumps.
            effective_stop = max(hard_stop_price, trailing_stop_price)

            # --- DASHBOARD STATUS ---
            # If our effective stop is above our entry, we are "Secured" (In Profit)
            if effective_stop > entry:
                self.secured_coins.append(coin)

            # --- EXECUTION CHECK ---
            if curr_price < effective_stop:
                tag = "STOP LOSS" if curr_price < entry else "TRAIL SECURED"
                outcome = "LOSS" if curr_price < entry else "WIN"
                
                if hands:
                    print(f">> 📉 CLOSING {coin} @ {curr_price} (Trigger: {effective_stop:.4f})")
                    # Close Full Position
                    size_usd = abs(size) * curr_price
                    hands.place_market_order(coin, "SELL" if size > 0 else "BUY", size_usd)
                    self._record_trade(coin, pnl, outcome)
                
                events.append(f"💰 {tag}: {coin} (${pnl:.2f})")

        return events
