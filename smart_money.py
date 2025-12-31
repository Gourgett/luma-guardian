class SmartMoney:
    def __init__(self):
        print(">> Smart Money (FULL ARSENAL: PRINCE, MEME & GHOSTS) Loaded")

    def hunt_ghosts(self, candles):
        # TIER 284: GHOST HUNTER (Fair Value Gaps)
        # RESTORED: This catches rapid price imbalances (wicks).
        try:
            c = candles
            if len(c) < 3: return None

            # 1. BULLISH FVG (Buys)
            c1_high = float(c[-3]['h'])
            c3_low = float(c[-1]['l'])

            if c3_low > c1_high:
                fvg_size = c3_low - c1_high
                # Entry at the top of the gap for higher fill probability
                entry = c1_high + (fvg_size * 0.5)
                return {"type": "FVG_BUY", "side": "BUY", "price": entry}

            # 2. BEARISH FVG (Shorts)
            c1_low = float(c[-3]['l'])
            c3_high = float(c[-1]['h'])

            if c3_high < c1_low:
                fvg_size = c1_low - c3_high
                entry = c3_high + (fvg_size * 0.5)
                return {"type": "FVG_SELL", "side": "SELL", "price": entry}
            
        except: pass
        return None

    def hunt_turtle(self, candles):
        # TIER 286: HYBRID STRUCTURE HUNTER (Princes vs Memes)
        try:
            if len(candles) < 55: return None
            
            closes = [float(c['c']) for c in candles]
            volumes = [float(c['v']) for c in candles]
            current_price = closes[-1]

            # Indicators
            ema_50 = self._calculate_ema(closes, 50)
            rsi = self._calculate_rsi(closes)
            
            curr_vol = volumes[-1]
            avg_vol = sum(volumes[-11:-1]) / 10
            vol_spike = curr_vol > (avg_vol * 1.5)

            # --- STRATEGY A: THE "PRINCE" PLAY (Reliable Support) ---
            # Best for SOL, SUI, ETH.
            # Logic: Trend is UP + RSI is Cool (Pullback)
            if current_price > ema_50:
                if 40 < rsi < 55:
                    return {"type": "TREND_PULLBACK", "side": "BUY", "price": current_price}
            
            # Logic: Trend is DOWN + RSI is Hot (Relief Rally)
            if current_price < ema_50:
                if 45 < rsi < 60:
                    return {"type": "TREND_REJECTION", "side": "SELL", "price": current_price}

            # --- STRATEGY B: THE "MEME" PLAY (Momentum Breakout) ---
            # Best for PENGU, DOGE, WIF.
            # Logic: Price is blasting off + Volume is HUGE.

            # Bullish Breakout
            if current_price > ema_50 and vol_spike:
                # Catch the momentum early (RSI 55-75 range)
                if 55 < rsi < 75:
                    return {"type": "MOMENTUM_BREAKOUT", "side": "BUY", "price": current_price}
            
            # Bearish Panic Dump
            if current_price < ema_50 and vol_spike:
                if 25 < rsi < 45:
                    return {"type": "PANIC_DUMP", "side": "SELL", "price": current_price}
        
        except Exception as e:
            pass

        return None

    def _calculate_rsi(self, prices, period=14):
        try:
            if len(prices) < period + 1: return 50
            deltas = [prices[i+1] - prices[i] for i in range(len(prices)-1)]
            recent_deltas = deltas[-period:]
            
            gains = [x if x > 0 else 0 for x in recent_deltas]
            losses = [abs(x) if x < 0 else 0 for x in recent_deltas]
            
            avg_gain = sum(gains) / period
            avg_loss = sum(losses) / period
            
            if avg_loss == 0: return 100
            rs = avg_gain / avg_loss
            return 100 - (100 / (1 + rs))
        except:
            return 50

    def _calculate_ema(self, prices, period):
        try:
            k = 2 / (period + 1)
            ema = prices[0]
            for p in prices[1:]:
                ema = (p * k) + (ema * (1 - k))
            return ema
        except:
            return prices[-1]
