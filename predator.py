class Predator:
    def __init__(self):
        print(">> Predator (Patient Hunter) Loaded [HYBRID RSI SYNC]")

    def analyze_divergence(self, candles, coin="UNKNOWN"):
        """
        Detects if a move is 'Real' or a 'Trap'.
        UPDATED: Now respects Asset Class (Princes vs Memes).
        """
        try:
            if len(candles) < 15: return None
            
            # 1. Prepare Data & RSI
            curr = candles[-1]
            prev = candles[-2]

            closes = [float(c['c']) for c in candles]
            rsi = self._calculate_rsi(closes)

            # 2. BULLISH DIVERGENCE (Absorption)
            # Price dropping hard, but Volume is massive.
            if curr['c'] < prev['l']:
                if curr['v'] > (prev['v'] * 1.5):
                    # Only valid if we aren't already overbought
                    if rsi < 50:
                        return "ABSORPTION_BUY"

            # 3. BEARISH DIVERGENCE (Exhaustion)
            if curr['c'] > prev['h']:
                if curr['v'] < (prev['v'] * 0.7):
                    return "EXHAUSTION_SELL"

            # 4. KILLA MOVE (The Trap Detector)
            # Huge move on Huge volume.
            body_size = abs(curr['c'] - curr['o'])
            avg_body = sum([abs(c['c'] - c['o']) for c in candles[-11:-1]]) / 10
            
            if body_size > (avg_body * 3) and curr['v'] > (prev['v'] * 2):
                is_green = curr['c'] > curr['o']
                
                if is_green:
                    # SAFETY FILTER (HYBRID LOGIC)
                    # ----------------------------------------
                    meme_coins = ["WIF", "DOGE", "PENGU", "PEPE", "SHIB"]
                    
                    if coin in meme_coins:
                        rsi_limit = 85 # Memes are allowed to run hot
                    else:
                        rsi_limit = 75 # Princes are dangerous here
                    
                    if rsi > rsi_limit:
                        # print(f">> 🛡️ PREDATOR: Ignoring Pump (RSI {rsi:.1f} > {rsi_limit})")
                        return None
                    # ----------------------------------------
                    
                    return "REAL_PUMP"
                else:
                    return "REAL_DUMP"
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
