import json
import os
import time
from config import conf

class DeepSea:
    def __init__(self):
        self.state_file = conf.get_path("ratchet_state.json")
        self.trauma_center = {}  # Stores High-Water Marks (Highest Price Seen)
        self.secured_coins = []  # List of coins that are currently "Locked"
        self.load_state()
        print(">> DeepSea (Shield & Ratchet) Loaded")

    def load_state(self):
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.trauma_center = data.get("trauma", {})
                    self.secured_coins = data.get("secured", [])
        except: pass

    def save_state(self):
        try:
            data = {
                "trauma": self.trauma_center,
                "secured": self.secured_coins
            }
            with open(self.state_file, 'w') as f:
                json.dump(data, f)
        except: pass

    def check_trauma(self, hands, coin):
        # This function updates the "High Water Mark" for trailing stops
        # It's called every loop to update the best price seen
        pass # Logic handled inside manage_positions for efficiency

    def execute_close(self, hands, coin, side, size, reason):
        # The Critical Trigger Function
        print(f">> RATCHET TRIGGER: Closing {coin} ({reason})")
        
        # FIX: Ensure size is positive (Absolute Value)
        final_size = abs(float(size))
        
        # FIX: Determine closing side
        # If we hold a LONG, we must SELL to close.
        # If we hold a SHORT, we must BUY to close.
        close_side = "SELL" if side == "LONG" else "BUY"
        
        # Send the Kill Order
        success = hands.place_market_order(coin, close_side, final_size)
        
        if success:
            # Clean up memory immediately to prevent Zombie Loops
            if coin in self.secured_coins: 
                self.secured_coins.remove(coin)
            if coin in self.trauma_center: 
                del self.trauma_center[coin]
            self.save_state()
            return f"🚫 CLOSED {coin}: {reason}"
        else:
            print(f"xx RATCHET FAILED to close {coin}")
            return None

    def manage_positions(self, hands, positions, fleet_config):
        events = []
        active_coins = [p['coin'] for p in positions]
        
        # 1. Cleanup Old Data (Garbage Collection)
        for coin in list(self.trauma_center.keys()):
            if coin not in active_coins:
                del self.trauma_center[coin]
                if coin in self.secured_coins: self.secured_coins.remove(coin)
        
        self.save_state()

        # 2. Analyze Each Position
        for p in positions:
            coin = p['coin']
            size = float(p['size'])
            entry = float(p['entry'])
            curr_price = float(p['pnl']) / abs(size) + entry if size != 0 else entry 
            # Note: Approximating current price from PnL if not available directly, 
            # or we can pass current price from main.py. 
            # Better approach: main.py passes candles, but for safety we calculate ROE from PnL.
            
            # Determine Side
            side = "LONG" if size > 0 else "SHORT"
            
            # ROI Calculation
            lev = fleet_config.get(coin, {}).get('lev', 10)
            margin = (abs(size) * entry) / lev
            roe_pct = 0.0
            if margin > 0:
                roe_pct = (float(p['pnl']) / margin) * 100

            # --- A. SHIELD (Hard Stop Loss) ---
            # Default hard stop from config (e.g., 0.03 = 3% price move, approx 30% ROE at 10x)
            stop_loss_pct = fleet_config.get(coin, {}).get('stop_loss', 0.03) 
            
            # Calculate Hard Stop Price
            if side == "LONG":
                # If Price drops below Entry * (1 - SL)
                if curr_price < entry * (1 - stop_loss_pct):
                    evt = self.execute_close(hands, coin, side, size, "HARD_STOP_LOSS")
                    if evt: events.append(evt)
                    continue
            else: # SHORT
                # If Price rises above Entry * (1 + SL)
                if curr_price > entry * (1 + stop_loss_pct):
                    evt = self.execute_close(hands, coin, side, size, "HARD_STOP_LOSS")
                    if evt: events.append(evt)
                    continue

            # --- B. RATCHET (Trailing Stop) ---
            # 1. Update High-Water Mark (Best price seen)
            if coin not in self.trauma_center:
                self.trauma_center[coin] = curr_price
            
            if side == "LONG":
                if curr_price > self.trauma_center[coin]:
                    self.trauma_center[coin] = curr_price
            else: # SHORT
                if curr_price < self.trauma_center[coin]:
                    self.trauma_center[coin] = curr_price # Lower is better for shorts

            # 2. Check for "Lock" (Activation)
            # If we are up > 10% ROE (or 5% depending on setting), we LOCK the profit
            if roe_pct > 10.0 and coin not in self.secured_coins:
                self.secured_coins.append(coin)
                events.append(f"🔒 {coin} PROFIT LOCKED (>{roe_pct:.1f}%)")
                self.save_state()

            # 3. Execute Trailing Logic (Only if Locked)
            if coin in self.secured_coins:
                # Dynamic Trail: Tighter trail as we make more money
                trail_pct = 0.01 # 1% drop from peak triggers sell
                if roe_pct > 50: trail_pct = 0.02 # Give more room if huge winner? Or tighter? 
                # Actually, standard ratchet:
                # If ROE > 10%, secure break-even or small profit.
                
                # Logic: If price deviates X% from "Best Seen"
                best_price = self.trauma_center[coin]
                
                if side == "LONG":
                    # If current price < Best Price * (1 - trail)
                    drop_limit = best_price * (1.0 - 0.005) # 0.5% drop from peak
                    # Also ensure we don't sell below entry + small profit (The Floor)
                    floor_price = entry * 1.002 # Break-even + fees
                    
                    trigger_price = max(drop_limit, floor_price)
                    
                    if curr_price < trigger_price:
                        evt = self.execute_close(hands, coin, side, size, f"RATCHET_PROFIT (Peak: {best_price:.4f})")
                        if evt: events.append(evt)

                else: # SHORT
                    # If current price > Best Price * (1 + trail)
                    rise_limit = best_price * (1.0 + 0.005) # 0.5% rise from bottom
                    floor_price = entry * 0.998 # Break-even + fees
                    
                    trigger_price = min(rise_limit, floor_price)
                    
                    if curr_price > trigger_price:
                        evt = self.execute_close(hands, coin, side, size, f"RATCHET_PROFIT (Bottom: {best_price:.4f})")
                        if evt: events.append(evt)

        return events
