class Historian:
    def __init__(self):
        print(">> Historian (Cycle Logic) Loaded")
    
    def check_regime(self, btc_candles):
        # TIER 298: HISTORICAL CYCLE FILTER
        # Logic: Bitcoin 200-Day Moving Average (Approximated by 200 daily closes)
        
        if not btc_candles or len(btc_candles) < 200:
            return {"regime": "NEUTRAL", "multiplier": 1.0}
        
        try:
            # Calculate 200 SMA
            closes = [float(c['c']) for c in btc_candles[-200:]]
            sma_200 = sum(closes) / len(closes)
            current_price = closes[-1]
            
            # DETERMINATE CYCLE PHASE
            if current_price > sma_200:
                # BULL MARKET (Golden Era)
                # Reinforcement: Aggressive Buying Allowed
                return {"regime": "BULL", "multiplier": 1.5, "note": "Price > 200DMA"}
            else:
                # BEAR MARKET (Dark Age)
                # Reinforcement: Defensive Mode
                return {"regime": "BEAR", "multiplier": 0.5, "note": "Price < 200DMA"}
        except Exception as e:
            print(f"xx HISTORIAN ERROR: {e}")
            return {"regime": "NEUTRAL", "multiplier": 1.0}
