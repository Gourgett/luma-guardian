import time
from config import conf

class DeepSea:
    def __init__(self):
        self.secured_coins = []
        
        # --- CASH TRIGGERS (THE RULES) ---
        self.trigger_meme = 0.25    # Lock if PnL >= $0.25 (DOGE, WIF, kPEPE)
        self.trigger_prince = 0.50  # Lock if PnL >= $0.50 (SOL, ETH, SUI)
        
        # Buffer to ensure we cover fees when stopping out
        self.fee_buffer = 0.0015 

    def check_trauma(self, hands, coin):
        pass

    def manage_positions(self, hands, positions, fleet_config):
        events = []
        active_coins = [p['coin'] for p in positions]
        
        # Cleanup "Ghost" Secured Coins
        self.secured_coins = [c for c in self.secured_coins if c in active_coins]

        for p in positions:
            coin = p['coin']
            
            # Skip if already locked/secured
            if coin in self.secured_coins:
                continue

            try:
                pnl = float(p['pnl'])
                entry = float(p['entry'])
                size = float(p['size'])
                
                # 1. IDENTIFY TYPE (Meme vs Prince)
                coin_rules = fleet_config.get(coin, {'type': 'MEME'}) # Default to MEME if unknown
                c_type = coin_rules.get('type', 'MEME')
                
                # 2. SELECT TRIGGER PRICE
                trigger_price = self.trigger_meme if c_type == 'MEME' else self.trigger_prince
                
                # 3. THE TRIGGER LOGIC (Cash Based)
                # If PnL hits the target ($0.25 or $0.50), we LOCK it.
                if pnl >= trigger_price:
                    self.secured_coins.append(coin)
                    events.append(f"🔒 {coin}: LOCKED @ ${pnl:.2f} (>{trigger_price})")
                    
                    # Optional: Print to console for verification
                    print(f">> RATCHET: Locking {coin} (PnL ${pnl:.2f} >= ${trigger_price})")

            except Exception as e:
                print(f"xx RATCHET ERROR {coin}: {e}")
                    
        return events

    @property
    def secured_list(self):
        return self.secured_coins
