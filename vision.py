import json
import time
import requests

class Vision:
    def __init__(self):
        print(">> Vision Module (v3.1) Loaded")
        self.base_url = "https://api.hyperliquid.xyz/info"
        self.cache = {}

    def _post(self, payload):
        try:
            # We use a simple requests call.
            # In a full prod system, we'd use the SDK, but this is faster/lighter.
            headers = {"Content-Type": "application/json"}
            resp = requests.post(self.base_url, json=payload, headers=headers, timeout=5)
            if resp.status_code == 200:
                return resp.json()
            return None
        except Exception as e:
            print(f"xx VISION ERROR: {e}")
            return None

    def get_user_state(self, address):
        if not address: return {}
        payload = {"type": "clearinghouseState", "user": address}
        return self._post(payload)

    def get_global_prices(self):
        # Fetches all coin prices
        payload = {"type": "allMids"}
        data = self._post(payload)
        if data:
            return data
        return {}

    def get_candles(self, coin, interval):
        # TIER 376 FIX: Restored this critical function
        # Fetches OHLCV data for Strategies
        try:
            # Hyperliquid uses millisecond timestamps
            end_time = int(time.time() * 1000)
            # Fetch last 50 candles approx (enough for Xenomorph 20 + buffer)
            # 1h = 3600000 ms. 50 * 3.6m = 180,000,000 ms roughly
            start_time = end_time - (50 * 3600 * 1000)

            if interval == "1d":
                start_time = end_time - (250 * 24 * 3600 * 1000) # 250 days for Historian

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

            # Format standardized for our Brains:
            # {'t': time, 'o': open, 'h': high, 'l': low, 'c': close, 'v': volume}
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
            print(f"xx CANDLE ERROR ({coin}): {e}")
            return []

    def get_price(self, coin):
        # Quick helper for single price
        prices = self.get_global_prices()
        return float(prices.get(coin, 0))
