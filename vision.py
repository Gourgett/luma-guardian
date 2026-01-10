import json
import time
import requests
import logging

class Vision:
    def __init__(self):
        print(">> Vision Module (v3.5: OPTIMIZED REQUESTS) Loaded")
        self.base_url = "https://api.hyperliquid.xyz/info"
        self.cache = {}
        # Map intervals to milliseconds for accurate math
        self.interval_map = {
            "1m": 60 * 1000,
            "5m": 5 * 60 * 1000,
            "15m": 15 * 60 * 1000,
            "30m": 30 * 60 * 1000,
            "1h": 60 * 60 * 1000,
            "4h": 4 * 60 * 60 * 1000,
            "1d": 24 * 60 * 60 * 1000,
        }

    def _post(self, payload, retries=3):
        """Robust POST with retries for network blips."""
        for attempt in range(retries):
            try:
                headers = {"Content-Type": "application/json"}
                # Timeout increased slightly to 10s for stability
                resp = requests.post(self.base_url, json=payload, headers=headers, timeout=10)
                
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 429:
                    print(f"xx RATE LIMIT (Attempt {attempt+1}) - Sleeping 2s...")
                    time.sleep(2)
                else:
                    # Log non-200 errors but don't crash
                    if attempt == retries - 1:
                        print(f"xx API ERROR: {resp.status_code} - {resp.text[:50]}")
                        
            except requests.exceptions.RequestException as e:
                print(f"xx NETWORK ERROR (Attempt {attempt+1}): {e}")
                time.sleep(1)
            except Exception as e:
                print(f"xx UNKNOWN VISION ERROR: {e}")
        
        return None

    def get_user_state(self, address):
        """Fetches account Equity and Positions."""
        if not address: return {}
        payload = {"type": "clearinghouseState", "user": address}
        return self._post(payload) or {}

    def get_global_prices(self):
        """Fetches all mid prices."""
        payload = {"type": "allMids"}
        return self._post(payload) or {}

    def get_candles(self, coin, interval):
        """
        Fetches OHLCV data.
        FIXED: Dynamically calculates start time based on the actual interval.
        """
        try:
            end_time = int(time.time() * 1000)
            
            # 1. Get Milliseconds per candle from map (Default to 1h if missing)
            ms_per_candle = self.interval_map.get(interval, 3600000)
            
            # 2. Logic Lock: Fetch exactly 70 candles (Safety buffer for EMA 50)
            # 60 was tight, 70 is safer for calculation lag
            lookback_window = 70 * ms_per_candle
            
            # Special Case: Historian logic for Daily candles
            if interval == "1d":
                lookback_window = 250 * 24 * 3600 * 1000

            start_time = end_time - lookback_window

            payload = {
                "type": "candleSnapshot",
                "req": {
                    "coin": coin,
                    "interval": interval,
                    "startTime": start_time,
                    "endTime": end_time
                }
            }
            
            raw_candles = self._post(payload)
            if not raw_candles: return []

            # Format for Predator/SmartMoney
            formatted = []
            for c in raw_candles:
                formatted.append({
                    't': c['t'],
                    'o': float(c['o']),
                    'h': float(c['h']),
                    'l': float(c['l']),
                    'c': float(c['c']),
                    'v': float(c['v'])
                })
            
            return formatted

        except Exception as e:
            print(f"xx CANDLE DATA ERROR ({coin}): {e}")
            return []

    def get_price(self, coin):
        """Quick price lookup helper."""
        prices = self.get_global_prices()
        return float(prices.get(coin, 0))

    def get_meta(self):
        """
        NEW: Fetches Universe details (Coin list, decimals).
        Useful for validating FLEET_CONFIG.
        """
        payload = {"type": "meta"}
        return self._post(payload)
