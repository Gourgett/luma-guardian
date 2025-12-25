import json
import time
import math
import eth_account
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from config import conf

class Hands:
    def __init__(self):
        self.exchange = None
        self.info = None
        self.manual_overrides = {'kPEPE': 0, 'WIF': 0, 'PEPE': 0, 'BONK': 0}
        print(">> HANDS: Initialized (Safe Mode)")

    def _connect(self):
        try:
            self.account = eth_account.Account.from_key(conf.private_key)
            self.info = Info(conf.base_url, skip_ws=True)
            self.exchange = Exchange(self.account, conf.base_url, self.account.address)
            try:
                self.meta = self.info.meta()
                self.coin_rules = {a['name']: a['szDecimals'] for a in self.meta['universe']}
            except:
                self.coin_rules = {}
            return True
        except Exception as e:
            print(f"xx HANDS CONNECT FAIL: {e}")
            return False

    def _ensure_connection(self):
        if self.exchange is None:
            return self._connect()
        return True

    def _get_precise_size(self, coin, size):
        if coin in self.manual_overrides: return int(size)
        try:
            decimals = self.coin_rules.get(coin, 2)
            if decimals == 0: return int(size)
            factor = 10 ** decimals
            return math.floor(size * factor) / factor
        except: return int(size)

    def set_leverage_all(self, coins, leverage):
        if not self._ensure_connection(): return
        for coin in coins:
            try: self.exchange.update_leverage(leverage, coin)
            except: pass

    def cancel_active_orders(self, coin):
        if not self._ensure_connection(): return False
        try:
            self.exchange.cancel_all_orders(coin)
            return True
        except: return False

    def place_market_order(self, coin, side, size):
        if not self._ensure_connection(): return False
        try:
            final_size = self._get_precise_size(coin, size)
            is_buy = (side == "BUY")
            result = self.exchange.market_open(coin, is_buy, final_size, None, 0.05)
            if result['status'] == 'ok': return True
            print(f"xx REJECT: {result}")
            return False
        except Exception as e:
            print(f"xx ERROR: {e}")
            return False

    def place_trap(self, coin, side, price, size_usd):
        if not self._ensure_connection(): return False
        try:
            is_buy = (side == "BUY")
            raw_size = size_usd / float(price)
            final_size = self._get_precise_size(coin, raw_size)
            final_price = float(f"{float(price):.5g}")
            self.exchange.order(coin, is_buy, final_size, final_price, {"limit": {"tif": "Gtc"}})
            return True
        except: return False
