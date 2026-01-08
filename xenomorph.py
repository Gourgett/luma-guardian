import time

class Xenomorph:
    def __init__(self):
        print(">> Xenomorph (Patient Hunter) Loaded [HYBRID RSI LOGIC]")

    def hunt(self, coin, candles):
        try:
            if not candles or len(candles) < 20: return "WAIT"
            closes = [float(c['c']) for c in candles]
            volumes = [float(c['v']) for c in candles]
            current_price = closes[-1]

            # 2. HYBRID RSI FILTER
            rsi = self._calculate_rsi(closes, 14)
            # UPDATE: Added kBONK/kFLOKI
            meme_coins = ["WIF", "DOGE", "PENGU", "SHIB", "kBONK", "kFLOKI"]

            if coin in meme_coins: rsi_limit = 85
            else: rsi_limit = 75

            if rsi > rsi_limit: return "WAIT"

            # 3. Breakout Logic
            avg_vol = sum(volumes[-10:]) / 10
            vol_spike = volumes[-1] > (avg_vol * 1.5)
            ema_20 = self._calculate_ema(closes, 20)
            uptrend = current_price > ema_20

            if vol_spike and uptrend: return "ATTACK"
            return "WAIT"

        except Exception as e: return "WAIT"

    def _calculate_rsi(self, prices, period=14):
        try:
            deltas = [prices[i+1] - prices[i] for i in range(len(prices)-1)]
            gains = [d for d in deltas if d > 0]
            losses = [abs(d) for d in deltas if d < 0]
            if len(gains) == 0: return 0
            if len(losses) == 0: return 100
            avg_gain = sum(gains[-period:]) / period
            avg_loss = sum(losses[-period:]) / period
            if avg_loss == 0: return 100
            rs = avg_gain / avg_loss
            return 100 - (100 / (1 + rs))
        except: return 50

    def _calculate_ema(self, prices, period):
        try:
            k = 2 / (period + 1)
            ema = prices[0]
            for p in prices[1:]: ema = (p * k) + (ema * (1 - k))
            return ema
        except: return prices[-1]
