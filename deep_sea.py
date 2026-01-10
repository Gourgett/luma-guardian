import json
import os
import time
from datetime import datetime

class DeepSea:
    def __init__(self):
        print(">> DEEP SEA: Stepped Trailing Logic Loaded")
        
        # [PATCH] Align with Railway Directory Logic
        self.DATA_DIR = "/app/data" if os.path.exists("/app/data") else "."
        if not os.path.exists(self.DATA_DIR): os.makedirs(self.DATA_DIR, exist_ok=True)
            
        self.STATS_FILE = os.path.join(self.DATA_DIR, "stats.json")
        
        self.secured_coins = []
        self.highest_rois = {} # Tracks highest ROI % seen (not price)
        self.stats = self._load_stats()

    def _load_stats(self):
        """STABILITY PATCH: Safe Load"""
        if os.path.exists(self.STATS_FILE):
            try: 
                with open(self.STATS_FILE, 'r') as f: return json.load(f)
            except: 
                pass
        return {"wins": 0, "losses": 0, "history": []}

    def _save_stats(self):
        try: 
            with open(self.STATS_FILE, 'w') as f: json.dump(self.stats, f, indent=4)
        except: 
            pass

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
        
        # Clean up old trackers
        for c in list(self.highest_rois.keys()):
            if c not in current_coins: del self.highest_rois[c]

        for p in positions:
            coin = p['coin']
            size = float(p['size'])
            entry = float(p['entry'])
            pnl = float(p['pnl'])
            margin = float(p.get('margin', 1.0))
            if margin == 0: margin = 1.0 # Prevent div/0

            if size == 0: continue
            
            # Calculate Current ROI
            current_roi = (pnl / margin) * 100

            # 1. Update High Water Mark (ROI based)
            if coin not in self.highest_rois: self.highest_rois[coin] = current_roi
            if current_roi > self.highest_rois[coin]: self.highest_rois[coin] = current_roi
            
            high_water_roi = self.highest_rois[coin]

            # 2. Determine Hard Stop based on Type
            c_type = fleet_config.get(coin, {}).get('type', 'MEME')
            
            if c_type == 'PRINCE':
                hard_stop_roi = -6.0
            else:
                hard_stop_roi = -8.0

            # 3. Calculate Dynamic Trail Gap
            # Default Trail: 3%
            trail_gap = 3.0
            
            # Step 1: Above 5% ROI -> Tighten to 1.5%
            if high_water_roi >= 5.0:
                trail_gap = 1.5
            
            # Step 2: Above 12% ROI -> Tighten to 0.5%
            if high_water_roi >= 12.0:
                trail_gap = 0.5

            # 4. Calculate Trigger ROI
            # The trigger is the High Water Mark minus the Gap
            trigger_roi = high_water_roi - trail_gap

            # 5. Breakeven Override
            # If we hit 0.40% ROI, the stop must at least be Break Even (0%)
            # We ensure the trigger never drops below 0 if we passed 0.4%
            if high_water_roi >= 0.40:
                trigger_roi = max(0.0, trigger_roi)
                self.secured_coins.append(coin)

            # --- EXECUTION CHECK ---
            
            # A. Check Hard Stop (Emergency)
            if current_roi <= hard_stop_roi:
                if hands:
                    print(f">> 💀 HARD STOP: {coin} @ {current_roi:.2f}%")
                    hands.place_market_order(coin, "SELL" if size > 0 else "BUY", abs(size), reduce_only=True)
                    self._record_trade(coin, pnl, "LOSS")
                    events.append(f"💀 HARD STOP: {coin} cut at {current_roi:.2f}%")
                continue # Skip trailing check if hard stop hit

            # B. Check Trailing Stop
            # Only trigger if current ROI fell below the calculated trigger AND we are in profit zone (or passed BE)
            # The logic: If High Water is 10%, Gap is 1.5%, Trigger is 8.5%. If Current is 8.4%, SELL.
            if current_roi <= trigger_roi and high_water_roi >= 0.40:
                 if hands:
                    print(f">> 📉 TRAIL HIT: {coin} @ {current_roi:.2f}% (High: {high_water_roi:.2f}% | Gap: {trail_gap}%)")
                    hands.place_market_order(coin, "SELL" if size > 0 else "BUY", abs(size), reduce_only=True)
                    self._record_trade(coin, pnl, "WIN")
                    events.append(f"💰 TRAIL SECURED: {coin} at {current_roi:.2f}% ROI")

        return events
