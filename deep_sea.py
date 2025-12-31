import time

class DeepSea:
    def __init__(self):
        print(">> DEEP SEA: Ratchet System Loaded (Mode: SURGICAL | PRINCE -4% | MEME -6% | SECURE 5)")
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
            leverage = rules['lev']
            coin_type = rules['type'] # PRINCE or MEME

            # CALCULATE ROE
            margin = (abs(size) * entry) / leverage
            if margin == 0: continue
            roe = pnl / margin

            # TRACK PEAK ROE
            if coin not in self.peak_roe: self.peak_roe[coin] = roe
            else:
                if roe > self.peak_roe[coin]: self.peak_roe[coin] = roe
            
            peak = self.peak_roe[coin]

            # --- SMART RISK STRATEGY ---
            
            # 1. DIFFERENTIAL HARD STOPS (The Only Major Change)
            # Princes: Cut losses at -4% (Fixes the Risk Ratio)
            # Memes: Keep at -8% (Standard)
            if coin_type == "PRINCE":
                current_floor = -0.04
            else:
                current_floor = -0.06

            # 2. BREAKEVEN LOCK (Standard)
            # Banks small wins so green trades don't turn red.
            if peak >= 0.025:
                current_floor = 0.005

            # 3. BANKER TRAIL (Standard 2%)
            # We keep this tight (0.02) to ensure Memes bank cash aggressively.
            if peak >= 0.05:
                current_floor = peak - 0.015

            # CHECK EXIT
            if roe < current_floor:
                tag = "STOP LOSS" if current_floor < 0 else "PROFIT SECURED"

                # Only record Trauma if it was a LOSS
                if current_floor < 0:
                    self.trauma_record[coin] = time.time()
                
                hands.place_market_order(coin, "SELL" if size > 0 else "BUY", abs(size))

                # LOGGING
                pnl_str = f"{pnl:+.2f}"
                events.append(f"💰 {tag}: {coin} ({pnl_str} | {roe*100:.1f}%)")

                if coin in self.secured_coins: self.secured_coins.remove(coin)

            # VISUAL MARKER
            elif current_floor > 0 and coin not in self.secured_coins:
                self.secured_coins.append(coin)

            # Emergency Hard Stop
            if roe < -0.40:
                 hands.place_market_order(coin, "SELL" if size > 0 else "BUY", abs(size))
                 self.trauma_record[coin] = time.time()
                 events.append(f"xx EMERGENCY CUT: {coin}")

        return events
