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
        # 🟢 INSTANT START: No connection here.
        self.exchange = None
        self.info = None
        self.account = None
        self.manual_overrides = {'kPEPE': 0, 'WIF': 0, 'PEPE': 0, 'BONK': 0}
        print(">> HANDS: Initialized (Lazy Mode)")

    def _connect(self):
        try:
            print(">> HANDS: Connecting...")
            self.account = eth_account.Account.from_key(conf.private_key)
            self.info = Info(conf.base_url, skip_ws=True)
            self.exchange = Exchange(self.account, conf.base_url, self.account.address)
            try:
                self.meta = self.info.meta()
                self.coin_rules = {a['name']: a['szDecimals'] for a in self.meta['universe']}
                print(f">> HANDS CONNECTED: {len(self.coin_rules)} Assets")
            except: pass
            return True
        except Exception as e:
            print(f"xx CONNECTION FAILED: {e}")
            self.exchange = None
            return False

    def _ensure_connection(self):
        if self.exchange is None: return self._connect()
        return True

    def _get_precise_size(self, coin, size):
        try:
            decimals = self.manual_overrides.get(coin, 2)
            if not self.coin_rules: decimals = 2
            elif coin not in self.manual_overrides: decimals = self.coin_rules.get(coin, 2)
            
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
            time.sleep(0.5)
            return True
        except:
            self.exchange = None
            return False

    def place_market_order(self, coin, side, size):
        if not self._ensure_connection(): return "CONNECTION_DIED"
        try:
            final_size = self._get_precise_size(coin, size)
            is_buy = True if side == "BUY" else False
            if final_size <= 0: return "ZERO_SIZE"
            
            print(f">> EXEC {coin} {side}: {final_size}")
            result = self.exchange.market_open(coin, is_buy, final_size, None, 0.05)
            if result['status'] == 'ok': return True
            return str(result)
        except Exception as e:
            if "attribute" in str(e): self.exchange = None
            return str(e)

    def place_trap(self, coin, side, price, size_usd):
        if not self._ensure_connection(): return False
        try:
            is_buy = True if side == "BUY" else False
            raw_size = size_usd / float(price)
            final_size = self._get_precise_size(coin, raw_size)
            final_price = float(f"{float(price):.5g}")
            self.exchange.order(coin, is_buy, final_size, final_price, {"limit": {"tif": "Gtc"}})
            return True
        except: return False
