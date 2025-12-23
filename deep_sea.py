import time
from config import conf

class DeepSea:
    def __init__(self):
        self.secured_coins = []
        
        # --- CASH TRIGGERS ---
        self.trigger_meme = 0.25    # Lock if PnL > $0.25
        self.trigger_prince = 0.50  # Lock if PnL > $0.50
        
        # --- DEFENSE SETTINGS ---
        # If a secured coin drops below this PnL, WE SELL.
        # $0.05 covers fees so you don't lose money.
        self.breakeven_limit = 0.05 

    def check_trauma(self, hands, coin):
        pass

    def manage_positions(self, hands, positions, fleet_config):
        events = []
        active_coins = [p['coin'] for p in positions]
        
        # 1. CLEANUP: Remove coins we are no longer holding
        self.secured_coins = [c for c in self.secured_coins if c in active_coins]

        for p in positions:
            coin = p['coin']
            try:
                pnl = float(p['pnl'])
                size = float(p['size'])
                
                # --- IDENTIFY TYPE ---
                # Default to MEME if not found, just to be safe
                c_data = fleet_config.get(coin, {'type': 'MEME'})
                c_type = c_data.get('type', 'MEME')
                
                trigger_val = self.trigger_meme if c_type == 'MEME' else self.trigger_prince

                # --- LOGIC BRANCH ---
                
                # CASE A: COIN IS ALREADY SECURED (Watching for drop)
                if coin in self.secured_coins:
                    # THE GUARD: If profit drops below $0.05, KILL IT.
                    if pnl < self.breakeven_limit:
                        print(f">> RATCHET: Protecting {coin} at ${pnl:.2f}")
                        
                        # EXECUTE CLOSE
                        side = "SELL" if size > 0 else "BUY"
                        # We use abs(size) to ensure positive number
                        if hands.place_market_order(coin, side, abs(size)):
                            events.append(f"🛡️ {coin}: PROTECTED @ ${pnl:.2f}")
                            # Remove from monitored list since it's closed
                            if coin in self.secured_coins: self.secured_coins.remove(coin)
                
                # CASE B: COIN IS NOT SECURED YET (Waiting for profit)
                else:
                    if pnl >= trigger_val:
                        self.secured_coins.append(coin)
                        events.append(f"🔒 {coin}: SECURED (>${trigger_val})")

            except Exception as e:
                print(f"xx RATCHET ERROR {coin}: {e}")
                    
        return events

    @property
    def secured_list(self):
        return self.secured_coins
