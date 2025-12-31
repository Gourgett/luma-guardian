from datetime import datetime, timezone

class Chronos:
    def __init__(self):
        print(">> Chronos (Timekeeper) Loaded")

    def get_session(self):
        # Get current hour in UTC
        hour = datetime.now(timezone.utc).hour

        # Define Sessions (UTC)
        # ASIA: 21:00 - 07:00 (Safe Mode)
        if hour >= 21 or hour < 7:
            return {"name": "ASIA", "aggression": 0.5, "leverage": 5}
        
        # LONDON: 07:00 - 13:00 (Breakout Mode)
        elif 7 <= hour < 13:
            return {"name": "LONDON", "aggression": 1.0, "leverage": 10}

        # NEW YORK: 13:00 - 21:00 (Trend Mode)
        else: # 13 to 21
            return {"name": "NEW YORK", "aggression": 1.2, "leverage": 10}

    def check_market_open(self):
        # Returns True if mostly liquid (skips weekend dead zones if needed)
        # For Crypto, we run 24/7, but we respect the Volume Sessions above.
        return True
