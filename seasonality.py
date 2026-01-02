def get_multiplier(self, coin_type):
        """
        Returns a Risk Multiplier based on Day/Hour/Minute.
        coin_type: "PRINCE" (SOL/SUI) or "MEME" (DOGE/WIF)
        """
        now = datetime.now(timezone.utc)
        hour = now.hour
        minute = now.minute
        weekday = now.weekday() # 0=Mon, 6=Sun

        mult = 1.0
        note = "Standard"

        # 1. WEEKEND LOGIC (Friday 20:00 UTC - Sunday 22:00 UTC)
        # FIX: Changed (weekday > 4) to (weekday == 5) so Sunday logic works
        is_weekend = (weekday == 4 and hour >= 20) or \
                     (weekday == 5) or \
                     (weekday == 6 and hour < 22)
        
        if is_weekend:
            if coin_type == "PRINCE":
                mult *= 0.8 # Lower risk on SOL/SUI (Institutional money is gone)
                note = "Weekend Hold"
            elif coin_type == "MEME":
                mult *= 1.1 # Memes often run on weekends (Retail only)
                note = "Weekend Degen"
        
        # 2. INTRADAY "KILL ZONES" (High Volatility Windows)
        # London/NY Overlap (13:00 - 16:00 UTC) - Prime time for all coins
        elif 13 <= hour < 16:  # Changed 'if' to 'elif' so Weekend logic takes priority if overlapping
            mult *= 1.2
            note = "NY/London Overlap"
        
        # 3. THE "LUNCH LULL" (NY Lunch: 17:00 - 18:00 UTC)
        # Avoid fakeouts during low volume
        elif 17 <= hour < 18:
            mult *= 0.7
            note = "NY Lunch Lull"

        # 4. MICRO-BURST (Turn of the Candle)
        # Algorithms trade at :00 and :30.
        # This acts as a bonus modifier on top of the others.
        if minute <= 10 or (30 <= minute <= 40):
            mult *= 1.1
            if note == "Standard": note = "Micro-Burst"
            else: note += " + Micro-Burst"

        return {"mult": mult, "note": note}
