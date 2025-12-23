import time
from config import conf

class DeepSea:
    def __init__(self):
        # TRAUMA WARD: Stores the state of secured coins
        # Format: {'DOGE': {'high': 0.30, 'stop': 0.05}}
        self.trauma_ward = {}
        
        # --- CASH TRIGGERS (PROFIT LOCK) ---
        self.trigger_meme = 0.25    # Lock if PnL > $0.25
        self.trigger_prince = 0.50  # Lock if PnL > $0.50
        
        # --- HARD STOP LIMITS (DRAWDOWN) ---
        # If ROE drops below this % (Negative), we PANIC SELL.
        self.stop_limit_meme = 25.0   # -25% ROE
        self.stop_limit_prince = 30.0 # -30% ROE
        
        # --- TRAILING SETTINGS ---
        self.initial_guard = 0.05   # Minimum profit to keep ($)
        self.std_trail = 0.80       # Standard: Secure 80% (20% breathing room)
        self.super_trail = 0.99     # Supermax: Secure 99% (1% chokehold)
        self.super_trigger = 10.0   # Activate Supermax at 10% ROE

    def check_trauma(self, hands, coin):
        # We handle trauma inside manage_positions to save API calls
        pass

    def manage_positions(self, hands, positions, fleet_config):
        events = []
        active_coins = [p['coin'] for p in positions]
        
        # 1. CLEANUP
        for coin in list(self.trauma_ward.keys()):
            if coin not in active_coins:
                del self.trauma_ward[coin]

        for p in positions:
            coin = p['coin']
            try:
                pnl = float(p['pnl'])
                size = float(p['size'])
                entry = float(p['entry'])
                
                # --- CONFIG & METRICS ---
                c_data = fleet_config.get(coin, {'type': 'MEME', 'lev': 10})
                
                # Calculate ROE %
                lev = c_data.get('lev', 10)
                margin = (abs(size) * entry) / lev
                roe = (pnl / margin) * 100 if margin > 0 else 0.0

                # Identify Type
                c_type = c_data.get('type', 'MEME')
                trigger_val = self.trigger_meme if c_type == 'MEME' else self.trigger_prince

                # --- 🛑 LAYER 1: HARD STOP LOSS (User Defined) ---
                # MEME = -25%, PRINCE = -30%
                stop_threshold = self.stop_limit_meme if c_type == 'MEME' else self.stop_limit_prince
                
                # Check if we are deeper than the allowed drawdown
                if roe < -(stop_threshold):
                    print(f">> RATCHET: 🚨 HARD STOP hit on {coin} ({roe:.2f}% < -{stop_threshold}%)")
                    side = "SELL" if size > 0 else "BUY"
                    if hands.place_market_order(coin, side, abs(size)):
                        events.append(f"💀 {coin}: STOPPED OUT ({roe:.2f}%)")
                        continue # Trade killed, move to next

                # --- 💰 LAYER 2: PROFIT MANAGEMENT ---
                
                # CASE A: ALREADY SECURED (Trailing Mode)
                if coin in self.trauma_ward:
                    record = self.trauma_ward[coin]
                    
                    # Update High Water Mark
                    if pnl > record['high']:
                        record['high'] = pnl
                        
                        # DYNAMIC RATCHET: 10% ROE -> 1% Deviation
                        current_mult = self.super_trail if roe > self.super_trigger else self.std_trail
                        potential_stop = record['high'] * current_mult
                        
                        # Ratchet only moves UP
                        new_stop = max(self.initial_guard, potential_stop)
                        if new_stop > record['stop']:
                            record['stop'] = new_stop
                            if roe > self.super_trigger:
                                print(f">> RATCHET: {coin} SUPERMAX ({roe:.1f}%) Stop: ${new_stop:.2f}")
                    
                    # Check Trailing Stop
                    if pnl < record['stop']:
                        print(f">> RATCHET: Bank {coin}. PnL ${pnl:.2f} < Stop ${record['stop']:.2f}")
                        side = "SELL" if size > 0 else "BUY"
                        if hands.place_market_order(coin, side, abs(size)):
                            events.append(f"💰 {coin}: BANKED @ ${pnl:.2f}")
                            del self.trauma_ward[coin]

                # CASE B: NOT SECURED YET (Waiting for Cash Trigger)
                else:
                    if pnl >= trigger_val:
                        self.trauma_ward[coin] = {
                            'high': pnl,
                            'stop': self.initial_guard # Starts at $0.05
                        }
                        events.append(f"🔒 {coin}: SECURED (>${trigger_val})")

            except Exception as e:
                print(f"xx RATCHET ERROR {coin}: {e}")
                    
        return events

    @property
    def secured_list(self):
        return list(self.trauma_ward.keys())
