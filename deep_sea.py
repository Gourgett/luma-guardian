import time

class DeepSea:
    def __init__(self):
        print(">> DEEP SEA: Ratchet System Loaded (Mode: AGGRESSIVE JUMP)")
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

            # --- AGGRESSIVE JUMP STRATEGY ---

            # 1. HARD STOP LOSS (Updated to use Config -4%)
            # We use the config value to ensure the new Safety Protocol (-0.04) is respected.
            stop_loss_val = rules.get('stop_loss', 0.04)
            current_floor = -(stop_loss_val)

            # 2. EARLY BREAKEVEN (Trigger at 1.0%)
            # Logic: Lock 0.2% immediately to cover fees.
            if peak >= 0.01:
                current_floor = 0.002 

            # 3. THE "JUMP" TRAIL (Trigger at 2.0%)
            # Logic: If we hit 2%, we force the stop to 1.5%.
            # We maintain this 1.5% floor until the "1% Gap" naturally catches up
            # (which happens at 2.5% peak). Then we trail with the 1% gap.
            if peak >= 0.02:
                # Math: Choose the higher of (1.5%) OR (Peak - 1%)
                current_floor = max(0.015, peak - 0.01)

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

            # Emergency Hard Stop (Sanity Check)
            if roe < -0.40:
                hands.place_market_order(coin, "SELL" if size > 0 else "BUY", abs(size))
                self.trauma_record[coin] = time.time()
                events.append(f"xx EMERGENCY CUT: {coin}")

        return events
