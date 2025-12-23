import time
from config import conf

class DeepSea:
    def __init__(self):
        # TRAUMA WARD: Stores the state of secured coins
        # Format: {'DOGE': {'high': 0.30, 'stop': 0.05}}
        self.trauma_ward = {}
        
        # --- CASH TRIGGERS ---
        self.trigger_meme = 0.25    # Lock if PnL > $0.25
        self.trigger_prince = 0.50  # Lock if PnL > $0.50
        
        # --- TRAILING SETTINGS ---
        self.initial_guard = 0.05   # Minimum profit to keep ($)
        self.std_trail = 0.80       # Standard: Secure 80% (20% breathing room)
        self.super_trail = 0.99     # Supermax: Secure 99% (1% chokehold)
        self.super_trigger = 10.0   # Activate Supermax at 10% ROE

    def check_trauma(self, hands, coin):
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
                
                # --- CALCULATE ROE (For the 10% Logic) ---
                # We need to estimate margin to know percentage
                c_data = fleet_config.get(coin, {'type': 'MEME', 'lev': 10})
                lev = c_data.get('lev', 10)
                margin = (abs(size) * entry) / lev
                roe = (pnl / margin) * 100 if margin > 0 else 0.0

                # --- IDENTIFY TYPE (For the $0.25/$0.50 Logic) ---
                c_type = c_data.get('type', 'MEME')
                trigger_val = self.trigger_meme if c_type == 'MEME' else self.trigger_prince

                # --- LOGIC BRANCH ---
                
                # CASE A: ALREADY SECURED (Trailing Mode)
                if coin in self.trauma_ward:
                    record = self.trauma_ward[coin]
                    
                    # 1. UPDATE HIGH WATER MARK
                    if pnl > record['high']:
                        record['high'] = pnl
                        
                        # DYNAMIC RATCHET LOGIC
                        # If ROE > 10%, we choke the stop to 1% deviation (0.99)
                        # Otherwise, we give it 20% deviation (0.80)
                        current_mult = self.super_trail if roe > self.super_trigger else self.std_trail
                        
                        # Calculate new stop
                        potential_stop = record['high'] * current_mult
                        
                        # Ensure stop never goes DOWN, only UP.
                        # Also ensure it never drops below our initial $0.05 guard.
                        new_stop = max(self.initial_guard, potential_stop)
                        
                        if new_stop > record['stop']:
                            record['stop'] = new_stop
                            if roe > self.super_trigger:
                                print(f">> RATCHET: {coin} SUPERMAX ACTIVE (Stop ${new_stop:.2f})")
                    
                    # 2. CHECK STOP LOSS (Execution)
                    if pnl < record['stop']:
                        print(f">> RATCHET: Closing {coin}. PnL ${pnl:.2f} < Stop ${record['stop']:.2f}")
                        
                        # EXECUTE CLOSE
                        side = "SELL" if size > 0 else "BUY"
                        if hands.place_market_order(coin, side, abs(size)):
                            events.append(f"💰 {coin}: BANKED @ ${pnl:.2f} (Peak ${record['high']:.2f})")
                            del self.trauma_ward[coin]

                # CASE B: NOT SECURED YET (Waiting for Trigger)
                else:
                    if pnl >= trigger_val:
                        # INITIALIZE TRAUMA RECORD
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
