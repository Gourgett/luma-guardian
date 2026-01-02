from datetime import datetime, timezone

class Seasonality:
    def __init__(self):
        print(">> Seasonality Engine (Stable) Loaded")

    def get_multiplier(self, coin_type):
        """
        Returns a Risk Multiplier based on Day/Hour/Minute.
        """
        now = datetime.now(timezone.utc)
        hour = now.hour
        minute = now.minute
        weekday = now.weekday() # 0=Mon, 6=Sun

        mult = 1.0
        note = "Standard"

        # 1. WEEKEND LOGIC (Friday 20:00 UTC - Sunday 22:00 UTC)
        # Simplified logic: If it is Saturday or Sunday, boost risk for Memes.
        if weekday >= 5 or (weekday == 4 and hour >= 20):
            mult *= 1.1 
            note = "Weekend Degen"
        
        # 2. INTRADAY "KILL ZONES" (High Volatility Windows)
        # London/NY Overlap (13:00 - 16:00 UTC) - Prime time.
        elif 13 <= hour < 16:
            mult *= 1.2
            note = "NY/London Overlap"
        
        # 3. THE "LUNCH LULL" (NY Lunch: 17:00 - 18:00 UTC)
        # Avoid fakeouts during low volume
        elif 17 <= hour < 18:
            mult *= 0.7
            note = "NY Lunch Lull"

        # 4. MICRO-BURST (Turn of the Candle)
        # Algorithms trade at :00 and :30.
        if minute <= 10 or (30 <= minute <= 40):
            mult *= 1.1
            if note == "Standard": note = "Micro-Burst"
            else: note += " + Micro-Burst"

        return {"mult": mult, "note": note}
