import json
import time
import math
from eth_account.signers.local import LocalAccount
import eth_account
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from config import conf

class Hands:
    def __init__(self):
        try:
            self.account = eth_account.Account.from_key(conf.private_key)
            self.info = Info(conf.base_url, skip_ws=True)
            self.exchange = Exchange(self.account, conf.base_url, self.account.address)

            # UNIVERSAL CODE: Ask Hyperliquid for the "Rules of Engagement"
            # We map every single asset to its strict decimal limits immediately.
            self.meta = self.info.meta()
            self.coin_rules = {}
            for asset in self.meta['universe']:
                self.coin_rules[asset['name']] = asset['szDecimals']
            
            print(f">> HANDS ARMED: Loaded Rules for {len(self.coin_rules)} Assets")
        except Exception as e:
            print(f"xx HANDS INIT FAIL: {e}")

    def _get_precise_size(self, coin, size):
        """
        THE UNIVERSAL FORMATTER
        Does not 'round' mathematically. It asks the Exchange Rules for the specific
        decimal count (szDecimals) and formats the number to match perfectly.
        """
        try:
            # 1. Ask Hyperliquid: "How many decimals for this coin?"
            # Default to 2 if unknown, but for WIF/kPEPE this returns 0 or 1.
            decimals = self.coin_rules.get(coin, 2)
            
            # 2. The "Russia" Logic (Safe Truncation via String Formatting)
            # This avoids the "Round Up" bug that causes "Insufficient Margin" errors.
            # We create a formatter string like "{:.0f}" or "{:.4f}" dynamically.
            
            if decimals == 0:
                return int(size) # Force Integer for Memecoins (WIF, kPEPE)
            
            # Create a string factor to chop off decimals without rounding up
            factor = 10 ** decimals
            truncated = math.floor(size * factor) / factor
            return truncated
            
        except Exception as e:
            print(f"xx FORMAT ERROR {coin}: {e}")
            return size

    def set_leverage_all(self, coins, leverage):
        for coin in coins:
            try: self.exchange.update_leverage(leverage, coin)
            except: pass

    def place_market_order(self, coin, side, size):
        try:
            # STEP 1: Get the exact allowed size format
            final_size = self._get_precise_size(coin, size)
            is_buy = True if side == "BUY" else False

            if final_size <= 0: return False

            print(f">> EXEC {coin} {side}: {final_size}")
            
            # STEP 2: Send with Slippage Tolerance
            result = self.exchange.market_open(coin, is_buy, final_size, None, 0.05)

            if result['status'] == 'ok': 
                return True
            else:
                # This will show us "Margin" or "Precision" errors if they happen
                print(f"xx REJECT {coin}: {result}")
                return False
        except Exception as e:
            print(f"xx EXEC ERROR {coin}: {e}")
            return False

    def place_trap(self, coin, side, price, size_usd):
        try:
            is_buy = True if side == "BUY" else False
            
            # Calculate raw size
            raw_size = size_usd / float(price)
            
            # Format Size (Universal)
            final_size = self._get_precise_size(coin, raw_size)
            
            # Format Price (Hyperliquid usually takes 5 sig figs, but we just need safety)
            final_price = float(f"{float(price):.5g}")
            
            self.exchange.order(coin, is_buy, final_size, final_price, {"limit": {"tif": "Gtc"}})
            return True
        except: return False
