class Predator:
    def __init__(self):
        print(">> Predator (Patient Hunter) Loaded [HYBRID RSI SYNC]")

    def analyze_divergence(self, candles, coin="UNKNOWN"):
        try:
            if len(candles) < 15: return None
            curr = candles[-1]
            prev = candles[-2]
            closes = [float(c['c']) for c in candles]
            rsi = self._calculate_rsi(closes)

            if curr['c'] < prev['l'] and curr['v'] > (prev['v'] * 1.5) and rsi < 50:
                return "ABSORPTION_BUY"

            if curr['c'] > prev['h'] and curr['v'] < (prev['v'] * 0.7):
                return "EXHAUSTION_SELL"

            # KILLA MOVE
            body_size = abs(curr['c'] - curr['o'])
            avg_body = sum([abs(c['c'] - c['o']) for c in candles[-11:-1]]) / 10
            if body_size > (avg_body * 3) and curr['v'] > (prev['v'] * 2):
                if curr['c'] > curr['o']:
                    # UPDATE: Added kBONK/kFLOKI
                    meme_coins = ["WIF", "DOGE", "PENGU", "SHIB", "kBONK", "kFLOKI"]
                    if coin in meme_coins: rsi_limit = 85
                    else: rsi_limit = 75
                    if rsi > rsi_limit: return None
                    return "REAL_PUMP"
                else: return "REAL_DUMP"
        except: pass
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
        except: return 50
