import time
from config import conf

class DeepSea:
    def __init__(self):
        self.trauma_ward = {}
        
        # --- CASH TRIGGERS ---
        self.trigger_meme = 0.25
        self.trigger_prince = 0.50
        
        # --- STOP LIMITS ---
        self.stop_limit_meme = 25.0
        self.stop_limit_prince = 30.0
        
        # --- TRAILING ---
        self.initial_guard = 0.05
        self.std_trail = 0.80
        self.super_trail = 0.99
        self.super_trigger = 10.0

    def check_trauma(self, hands, coin):
        pass

    def manage_positions(self, hands, positions, fleet_config):
        events = []
        active_coins = [p['coin'] for p in positions]
        
        # 1. CLEANUP (Only if active_coins is not empty to prevent glitch wipes)
        if active_coins:
            for coin in list(self.trauma_ward.keys()):
                if coin not in active_coins:
                    del self.trauma_ward[coin]

        for p in positions:
            coin = p['coin']
            try:
                pnl = float(p['pnl'])
                size = float(p['size'])
                entry = float(p['entry'])
                
                c_data = fleet_config.get(coin, {'type': 'MEME', 'lev': 10})
                lev = c_data.get('lev', 10)
                margin = (abs(size) * entry) / lev
                roe = (pnl / margin) * 100 if margin > 0 else 0.0

                c_type = c_data.get('type', 'MEME')
                trigger_val = self.trigger_meme if c_type == 'MEME' else self.trigger_prince

                # --- 🛑 LAYER 1: HARD STOP ---
                stop_threshold = self.stop_limit_meme if c_type == 'MEME' else self.stop_limit_prince
                if roe < -(stop_threshold):
                    print(f">> RATCHET: 🚨 HARD STOP {coin}")
                    hands.cancel_active_orders(coin)
                    side = "SELL" if size > 0 else "BUY"
                    res = hands.place_market_order(coin, side, abs(size))
                    if res is True:
                        events.append(f"💀 {coin}: STOPPED OUT")
                        continue

                # --- 💰 LAYER 2: PROFIT ---
                if coin in self.trauma_ward:
                    record = self.trauma_ward[coin]
                    
                    # Update High Water Mark
                    if pnl > record['high']:
                        record['high'] = pnl
                        current_mult = self.super_trail if roe > self.super_trigger else self.std_trail
                        potential_stop = record['high'] * current_mult
                        
                        new_stop = max(self.initial_guard, potential_stop)
                        
                        # LOG THE UPDATE (Visual Confirmation)
                        if new_stop > record['stop']:
                            record['stop'] = new_stop
                            # Only log significant moves to avoid spam (>$0.01 change)
                            events.append(f"📈 {coin}: STOP UP -> ${new_stop:.2f}")

                    # THE EXIT TRIGGER
                    if pnl < record['stop']:
                        print(f">> RATCHET: Bank {coin}. PnL ${pnl:.2f} < Stop ${record['stop']:.2f}")
                        hands.cancel_active_orders(coin)
                        side = "SELL" if size > 0 else "BUY"
                        res = hands.place_market_order(coin, side, abs(size))
                        if res is True:
                            events.append(f"💰 {coin}: BANKED @ ${pnl:.2f}")
                            del self.trauma_ward[coin]
                        else:
                            events.append(f"⚠️ {coin}: CLOSE FAIL {res}")

                else:
                    if pnl >= trigger_val:
                        self.trauma_ward[coin] = {
                            'high': pnl,
                            'stop': self.initial_guard
                        }
                        events.append(f"🔒 {coin}: SECURED (>${trigger_val})")

            except Exception as e:
                print(f"xx RATCHET ERROR {coin}: {e}")
                    
        return events

    @property
    def secured_coins(self):
        return list(self.trauma_ward.keys())
