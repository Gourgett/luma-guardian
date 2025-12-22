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
            
            # LOAD PRECISION RULES
            self.meta = self.info.meta()
            self.coin_info = {}
            for asset in self.meta['universe']:
                self.coin_info[asset['name']] = {'sz_decimals': asset['szDecimals']}
            print(">> HANDS ARMED")
        except Exception as e:
            print(f"xx HANDS INIT FAIL: {e}")

    def _round_size(self, coin, size):
        decimals = self.coin_info.get(coin, {'sz_decimals': 2})['sz_decimals']
        if decimals == 0: return int(size)
        return round(size, decimals)

    def set_leverage_all(self, coins, leverage):
        for coin in coins:
            try: self.exchange.update_leverage(leverage, coin)
            except: pass

    def place_market_order(self, coin, side, size):
        # CRITICAL FIX: Aggressive Execution
        try:
            final_size = self._round_size(coin, size)
            is_buy = True if side == "BUY" else False
            
            # SLIPPAGE: 0.05 = 5%. This ensures execution during crashes.
            result = self.exchange.market_open(coin, is_buy, final_size, None, 0.05)
            
            if result['status'] == 'ok': return True
            else:
                print(f"xx REJECT: {result}")
                return False
        except Exception as e:
            print(f"xx EXEC ERROR: {e}")
            return False

    def place_trap(self, coin, side, price, size_usd):
        try:
            is_buy = True if side == "BUY" else False
            final_size = self._round_size(coin, size_usd / float(price))
            final_price = float(f"{float(price):.5g}")
            self.exchange.order(coin, is_buy, final_size, final_price, {"limit": {"tif": "Gtc"}})
            return True
        except: return False
