import pandas as pd

class SmartMoney:
    def __init__(self):
        print(">> Smart Money (FULL ARSENAL: PRINCE, MEME & GHOSTS) Loaded")

    def calculate_position_size(self, total_equity, active_positions_count=0):
        """
        TIER 1 (Financial Logic): 
        - 30% Safety Net (Untouchable)
        - 70% Active Trading Capital
        - Split evenly among the 6 Fleet Coins (approx 11.6% per coin)
        """
        if total_equity <= 0: return 0.0
        
        # 1. Safety Net Calculation
        safe_net = total_equity * 0.30
        tradeable_equity = total_equity * 0.70
        
        # 2. Allocation per Coin (Fixed to 6 slots: SOL, SUI, BNB, WIF, DOGE, PENGU)
        # We divide the total tradeable equity by 6, regardless of how many are currently open.
        # This ensures we never over-allocate if we add more coins later.
        allocation_per_coin = tradeable_equity / 6.0
        
        # Safety check: Ensure we don't return tiny dust amounts
        if allocation_per_coin < 5.0: return 0.0
        
        return round(allocation_per_coin, 2)

    def hunt_ghosts(self, candles):
        # TIER 284: GHOST HUNTER (Fair Value Gaps)
        try:
            c = candles
            if len(c) < 3: return None

            # 1. BULLISH FVG
            c1_high = float(c[-3]['h'])
            c3_low = float(c[-1]['l'])

            if c3_low > c1_high:
                fvg_size = c3_low - c1_high
                entry = c1_high + (fvg_size * 0.5)
                return {"type": "FVG_BUY", "side": "BUY", "price": entry}

            # 2. BEARISH FVG
            c1_low = float(c[-3]['l'])
            c3_high = float(c[-1]['h'])

            if c3_high < c1_low:
                fvg_size = c1_low - c3_high
                entry = c3_high + (fvg_size * 0.5)
                return {"type": "FVG_SELL", "side": "SELL", "price": entry}
            
        except: pass
        return None

    def hunt_turtle(self, candles, coin_type="MEME"):
        # TIER 286: HYBRID STRUCTURE HUNTER
        try:
            if len(candles) < 55: return None
            
            closes = [float(c['c']) for c in candles]
            volumes = [float(c['v']) for c in candles]
            current_price = closes[-1]

            ema_50 = self._calculate_ema(closes, 50)
            rsi = self._calculate_rsi(closes)
            
            curr_vol = volumes[-1]
            avg_vol = sum(volumes[-11:-1]) / 10
            vol_spike = curr_vol > (avg_vol * 1.5)

            # --- STRATEGY A: THE "PRINCE" PLAY (Strict Structure) ---
            # Princes need TREND CONFIRMATION to avoid fakeouts.
            # We strictly trade WITH the trend (Above EMA50 for buys).
            if coin_type == "PRINCE":
                if current_price > ema_50:
                    # Pullback Buy: Price is above EMA, but RSI dipped (Cooling off)
                    if 40 < rsi < 55:
                         return {"type": "PRINCE_TREND_FOLLOW", "side": "BUY", "price": current_price}
                
                elif current_price < ema_50:
                    # Trend Rejection Short: Price below EMA, RSI rallied (Dead cat bounce)
                    if 45 < rsi < 60:
                        return {"type": "PRINCE_TREND_REJECT", "side": "SELL", "price": current_price}

            # --- STRATEGY B: THE "MEME" PLAY (Momentum Chaos) ---
            # Memes care about VOLUME and HYPE.
            elif coin_type == "MEME":
                if vol_spike:
                    # Momentum Breakout (RSI Heating Up)
                    if current_price > ema_50 and 55 < rsi < 75:
                        return {"type": "MEME_BREAKOUT", "side": "BUY", "price": current_price}
                    
                    # Panic Dump (RSI Oversold but heavy volume = capitulation)
                    if current_price < ema_50 and rsi < 30:
                        # Risky knife catch, or momentum short? 
                        # For safety, we treat high volume drop as Sell continuation
                        return {"type": "MEME_DUMP", "side": "SELL", "price": current_price}
        
        except Exception as e: pass
        return None

    def _calculate_rsi(self, prices, period=14):
        try:
            if len(prices) < period + 1: return 50
            deltas = [prices[i+1] - prices[i] for i in range(len(prices)-1)]
            recent = deltas[-period:]
            gains = [x for x in recent if x > 0]
            losses = [abs(x) for x in recent if x < 0]
            avg_gain = sum(gains)/period if gains else 0
            avg_loss = sum(losses)/period if losses else 0
            if avg_loss == 0: return 100
            rs = avg_gain / avg_loss
            return 100 - (100 / (1 + rs))
        except: return 50

    def _calculate_ema(self, prices, period):
        try:
            k = 2 / (period + 1)
            ema = prices[0]
            for p in prices[1:]:
                ema = (p * k) + (ema * (1 - k))
            return ema
        except: return prices[-1]
