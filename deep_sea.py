import time

class DeepSea:
    def __init__(self):
        print(">> DEEP SEA: Trailing Logic Restored (1% Gap)")
        self.secured_coins = []
        self.peak_roe = {}
        self.trauma_record = {}
        # TRAUMA: If a coin hits stop loss, ignore it for 5 mins
        self.TRAUMA_DURATION = 300  

    def check_trauma(self, hands, coin):
        """
        Prevents 'Revenge Trading'. If we just lost on a coin, 
        block it for 5 minutes.
        """
        if coin in self.trauma_record:
            last_loss_time = self.trauma_record.get(coin, 0)
            if time.time() - last_loss_time < self.TRAUMA_DURATION:
                return True
            else:
                del self.trauma_record[coin]
        return False

    def manage_positions(self, hands, positions, fleet_config):
        events = []
        
        # Cleanup peaks for closed positions
        current_coins = [p['coin'] for p in positions]
        for c in list(self.peak_roe.keys()):
            if c not in current_coins: del self.peak_roe[c]

        for p in positions:
            coin = p['coin']
            if coin not in fleet_config: continue

            # Extract Data
            pnl = float(p['pnl'])
            size = float(p['size'])
            entry = float(p['entry'])
            
            # Real Leverage
            lev = float(p.get('leverage', fleet_config[coin]['lev']))
            
            # Calculate ROE (decimal)
            margin = (abs(size) * entry) / lev if lev > 0 else 1
            roe = pnl / margin if margin > 0 else 0.0
            roe_pct = roe * 100 

            # TRACK PEAK ROE
            if coin not in self.peak_roe: self.peak_roe[coin] = roe
            else:
                if roe > self.peak_roe[coin]: self.peak_roe[coin] = roe
            
            peak = self.peak_roe[coin]

            # --- CONFIG RULES ---
            # Stop Loss is -4% (-0.04)
            stop_loss_decimal = fleet_config[coin].get('stop_loss', 0.04)
            current_floor = -(stop_loss_decimal)

            # --- YOUR LOGIC ---
            
            # 1. BREAKEVEN (Trigger at 1.0%)
            # Logic: If peak hits 1%, move stop to 0.2% (covers fees).
            if peak >= 0.01:
                current_floor = 0.002 

            # 2. TRAILING ACTIVATION (Trigger at 2.0%)
            # Logic: Jump to 1.5%, then trail by 1%.
            if peak >= 0.02:
                # Calculate the 1% trail: (Peak - 0.01)
                trail_value = peak - 0.01
                # Enforce the 1.5% minimum jump
                current_floor = max(0.015, trail_value)

            # --- EXECUTION ---
            if roe < current_floor:
                tag = "STOP LOSS" if current_floor < 0 else "PROFIT SECURED"
                
                # Only record Trauma if it was a LOSS
                if current_floor < 0:
                    self.trauma_record[coin] = time.time()
                
                hands.place_market_order(coin, "SELL" if size > 0 else "BUY", abs(size))
                events.append(f"💰 {tag}: {coin} ({pnl:.2f} | {roe_pct:.1f}%)")
                
                if coin in self.secured_coins: self.secured_coins.remove(coin)

            # Visual Marker for Dashboard
            elif current_floor > 0 and coin not in self.secured_coins:
                self.secured_coins.append(coin)

        return events
