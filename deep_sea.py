import json
import os
from config import conf

class DeepSea:
    def __init__(self):
        self.state_file = conf.get_path("ratchet_state.json")
        self.trauma_center = {} 
        self.secured_coins = []
        self.load_state()

    def load_state(self):
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    d = json.load(f)
                    self.trauma_center = d.get("trauma", {})
                    self.secured_coins = d.get("secured", [])
        except: pass

    def save_state(self):
        try:
            with open(self.state_file, 'w') as f:
                json.dump({"trauma": self.trauma_center, "secured": self.secured_coins}, f)
        except: pass

    def check_trauma(self, hands, coin):
        pass

    def execute_close(self, hands, coin, side, size, reason):
        print(f">> RATCHET: Closing {coin} ({reason})")
        # FIX: FORCE POSITIVE SIZE
        final_size = abs(float(size))
        close_side = "SELL" if side == "LONG" else "BUY"
        
        if hands.place_market_order(coin, close_side, final_size):
            if coin in self.secured_coins: self.secured_coins.remove(coin)
            if coin in self.trauma_center: del self.trauma_center[coin]
            self.save_state()
            return f"🚫 CLOSED {coin}: {reason}"
        return None

    def manage_positions(self, hands, positions, fleet_config):
        events = []
        active = [p['coin'] for p in positions]
        
        # Cleanup
        for k in list(self.trauma_center.keys()):
            if k not in active: 
                del self.trauma_center[k]
                if k in self.secured_coins: self.secured_coins.remove(k)
        self.save_state()

        for p in positions:
            coin = p['coin']
            size = float(p['size'])
            entry = float(p['entry'])
            side = "LONG" if size > 0 else "SHORT"
            
            # Calculate Price & ROE
            lev = fleet_config.get(coin, {}).get('lev', 10)
            margin = (abs(size) * entry) / lev
            roe = (float(p['pnl']) / margin * 100) if margin > 0 else 0
            curr_price = (float(p['pnl']) / abs(size)) + entry

            # 1. HARD STOP
            sl = fleet_config.get(coin, {}).get('stop_loss', 0.03)
            if side == "LONG" and curr_price < entry * (1 - sl):
                e = self.execute_close(hands, coin, side, size, "HARD_STOP")
                if e: events.append(e)
                continue
            elif side == "SHORT" and curr_price > entry * (1 + sl):
                e = self.execute_close(hands, coin, side, size, "HARD_STOP")
                if e: events.append(e)
                continue

            # 2. RATCHET
            if coin not in self.trauma_center: self.trauma_center[coin] = curr_price
            best = self.trauma_center[coin]
            
            if side == "LONG":
                if curr_price > best: self.trauma_center[coin] = curr_price
                best = self.trauma_center[coin] # Re-read updated best
                
                if roe > 10 and coin not in self.secured_coins:
                    self.secured_coins.append(coin)
                    events.append(f"🔒 {coin} LOCKED")
                
                if coin in self.secured_coins:
                    drop_limit = best * 0.995 # 0.5% drop
                    floor = entry * 1.002
                    if curr_price < max(drop_limit, floor):
                        e = self.execute_close(hands, coin, side, size, "RATCHET_PROFIT")
                        if e: events.append(e)

            else: # SHORT
                if curr_price < best: self.trauma_center[coin] = curr_price
                best = self.trauma_center[coin]

                if roe > 10 and coin not in self.secured_coins:
                    self.secured_coins.append(coin)
                    events.append(f"🔒 {coin} LOCKED")
                
                if coin in self.secured_coins:
                    rise_limit = best * 1.005 # 0.5% rise
                    floor = entry * 0.998
                    if curr_price > min(rise_limit, floor):
                        e = self.execute_close(hands, coin, side, size, "RATCHET_PROFIT")
                        if e: events.append(e)

        return events
