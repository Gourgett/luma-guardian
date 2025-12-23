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

            # 1. LOAD RULES
            self.meta = self.info.meta()
            self.coin_rules = {}
            for asset in self.meta['universe']:
                self.coin_rules[asset['name']] = asset['szDecimals']
            
            # 2. SAFETY OVERRIDES (Force Integer for Meme Coins)
            self.manual_overrides = {
                'kPEPE': 0,
                'WIF': 0,
                'PEPE': 0,
                'BONK': 0
            }
            
            print(f">> HANDS ARMED: Loaded {len(self.coin_rules)} Assets")
        except Exception as e:
            print(f"xx HANDS INIT FAIL: {e}")
            self.coin_rules = {}
            self.manual_overrides = {'kPEPE': 0, 'WIF': 0}

    def _get_precise_size(self, coin, size):
        try:
            # CHECK OVERRIDE FIRST
            if coin in self.manual_overrides:
                decimals = self.manual_overrides[coin]
            else:
                decimals = self.coin_rules.get(coin, 2) 
            
            # FORCE INTEGER (The Anti-Reject Fix)
            if decimals == 0:
                return int(size)
            
            # TRUNCATE DECIMALS (The Precision Fix)
            factor = 10 ** decimals
            truncated = math.floor(size * factor) / factor
            return truncated
            
        except:
            return int(size) # Safe fallback

    def set_leverage_all(self, coins, leverage):
        for coin in coins:
            try: self.exchange.update_leverage(leverage, coin)
            except: pass

    def place_market_order(self, coin, side, size):
        try:
            # 1. FORMAT SIZE
            final_size = self._get_precise_size(coin, size)
            is_buy = True if side == "BUY" else False

            if final_size <= 0: return "ZERO_SIZE"

            print(f">> EXEC {coin} {side}: {final_size}")
            
            # 2. SEND ORDER
            result = self.exchange.market_open(coin, is_buy, final_size, None, 0.05)

            # 3. CHECK RESULT
            if result['status'] == 'ok': 
                return True
            else:
                # CRITICAL: Return the ACTUAL error message
                # Hyperliquid errors are often inside response['data']
                print(f"xx REJECT {coin}: {result}")
                return str(result) 
        except Exception as e:
            print(f"xx EXEC ERROR {coin}: {e}")
            return str(e)

    def place_trap(self, coin, side, price, size_usd):
        try:
            is_buy = True if side == "BUY" else False
            raw_size = size_usd / float(price)
            final_size = self._get_precise_size(coin, raw_size)
            final_price = float(f"{float(price):.5g}")
            self.exchange.order(coin, is_buy, final_size, final_price, {"limit": {"tif": "Gtc"}})
            return True
        except: return False
