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
        self.initial_guard = 0.05   # Initial safety net ($)
        self.trail_percent = 0.80   # Secure 80% of the peak profit

    def check_trauma(self, hands, coin):
        pass

    def manage_positions(self, hands, positions, fleet_config):
        events = []
        active_coins = [p['coin'] for p in positions]
        
        # 1. CLEANUP: Remove coins we are no longer holding
        # We must use list() to avoid runtime errors while modifying dict
        for coin in list(self.trauma_ward.keys()):
            if coin not in active_coins:
                del self.trauma_ward[coin]

        for p in positions:
            coin = p['coin']
            try:
                pnl = float(p['pnl'])
                size = float(p['size'])
                
                # --- IDENTIFY TYPE ---
                c_data = fleet_config.get(coin, {'type': 'MEME'})
                c_type = c_data.get('type', 'MEME')
                trigger_val = self.trigger_meme if c_type == 'MEME' else self.trigger_prince

                # --- LOGIC BRANCH ---
                
                # CASE A: ALREADY SECURED (Trailing Mode)
                if coin in self.trauma_ward:
                    record = self.trauma_ward[coin]
                    
                    # 1. UPDATE HIGH WATER MARK (If we made new highs)
                    if pnl > record['high']:
                        record['high'] = pnl
                        # RATCHET UP: Stop is max of ($0.05) OR (80% of Peak)
                        new_stop = max(self.initial_guard, pnl * self.trail_percent)
                        record['stop'] = new_stop
                        # Note: We don't spam events for every update, only the first lock
                    
                    # 2. CHECK STOP LOSS (If we dropped)
                    if pnl < record['stop']:
                        print(f">> RATCHET: Trailing Stop hit on {coin} @ ${pnl:.2f} (Peak: ${record['high']:.2f})")
                        
                        # EXECUTE CLOSE
                        side = "SELL" if size > 0 else "BUY"
                        if hands.place_market_order(coin, side, abs(size)):
                            events.append(f"💰 {coin}: BANKED @ ${pnl:.2f} (Peak ${record['high']:.2f})")
                            # Remove from ward immediately
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
        # Returns just the names for the dashboard to display the Lock Icon
        return list(self.trauma_ward.keys())
