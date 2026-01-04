import time

class DeepSea:
    def __init__(self):
        print(">> DEEP SEA: Ratchet System Loaded (Mode: VOLATILITY SURVIVOR)")
        self.secured_coins = []
        self.peak_roe = {}
        self.trauma_record = {}

    def check_trauma(self, hands, coin):
        # 5-Minute Cooldown for LOSSES only.
        last_loss = self.trauma_record.get(coin, 0)
        if time.time() - last_loss < 300:
            return True # BLOCK TRADES
        return False

    def manage_positions(self, hands, positions, fleet_config):
        events = []
        # Cleanup peaks for closed positions
        current_coins = [p['coin'] for p in positions]
        for c in list(self.peak_roe.keys()):
            if c not in current_coins: del self.peak_roe[c]

        for p in positions:
            coin = p['coin']
            pnl = float(p['pnl'])
            size = float(p['size'])
            entry = float(p['entry'])

            if coin not in fleet_config: continue
            rules = fleet_config[coin]
            leverage = float(rules['lev']) # Ensure float

            # CALCULATE ROE
            margin = (abs(size) * entry) / leverage if leverage > 0 else 1
            if margin == 0: continue
            roe = pnl / margin

            # TRACK PEAK ROE
            if coin not in self.peak_roe: self.peak_roe[coin] = roe
            else:
                if roe > self.peak_roe[coin]: self.peak_roe[coin] = roe
            
            peak = self.peak_roe[coin]

            # --- VOLATILITY SURVIVOR STRATEGY ---

            # 1. HARD STOP LOSS (Widened to -8% for Wicks)
            # Uses config value if present, otherwise defaults to 0.08 (Safe)
            stop_loss_val = rules.get('stop_loss', 0.08)
            current_floor = -(stop_loss_val)

            # 2. EARLY BREAKEVEN (Trigger at 1.5%)
            # Logic: We wait for 1.5% pump before locking profit to avoid chop.
            if peak >= 0.015:
                current_floor = 0.002 # Lock small profit to cover fees

            # 3. THE "RUNNER" TRAIL (Trigger at 4.0%)
            # Logic: Once we hit 4% profit, we trail by 2%. 
            # This 2% gap allows the coin to wiggle without selling early.
            if peak >= 0.04:
                current_floor = peak - 0.02

            # CHECK EXIT
            if roe < current_floor:
                tag = "STOP LOSS" if current_floor < 0 else "PROFIT SECURED"
                
                # Only record Trauma if it was a LOSS
                if current_floor < 0:
                    self.trauma_record[coin] = time.time()

                # HARD SELL EXECUTION
                hands.place_market_order(coin, "SELL" if size > 0 else "BUY", abs(size))

                # LOGGING
                pnl_str = f"{pnl:+.2f}"
                events.append(f"💰 {tag}: {coin} ({pnl_str} | {roe*100:.1f}%)")
                
                if coin in self.secured_coins: self.secured_coins.remove(coin)

            # VISUAL MARKER
            elif current_floor > 0 and coin not in self.secured_coins:
                self.secured_coins.append(coin)

            # Emergency Hard Stop (Sanity Check widened to -50%)
            if roe < -0.50:
                hands.place_market_order(coin, "SELL" if size > 0 else "BUY", abs(size))
                self.trauma_record[coin] = time.time()
                events.append(f"xx EMERGENCY CUT: {coin}")

        return events
