import json
import time
import math
import eth_account
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from config import conf

class Hands:
    def __init__(self):
        # DAY ONE ARCHITECTURE: Connect immediately on startup.
        print(">> HANDS: Connecting to Exchange...")
        try:
            self.account = eth_account.Account.from_key(conf.private_key)
            self.info = Info(conf.base_url, skip_ws=True)
            self.exchange = Exchange(self.account, conf.base_url, self.account.address)
            
            # Load Universe for precision rules
            self.meta = self.info.meta()
            self.coin_rules = {a['name']: a['szDecimals'] for a in self.meta['universe']}
            print(f">> HANDS: CONNECTED. Loaded {len(self.coin_rules)} assets.")
        except Exception as e:
            print(f"xx HANDS CONNECTION FAILED: {e}")
            self.exchange = None

    def set_leverage_all(self, coins, leverage):
        if not self.exchange: return
        for coin in coins:
            try:
                self.exchange.update_leverage(leverage, coin)
                print(f">> LEVERAGE: Set {coin} to {leverage}x")
            except: pass

    def _get_precise_size(self, coin, size):
        # The ONLY patch we keep: kPEPE Integer Fix
        try:
            decimals = self.coin_rules.get(coin, 2)
            # Force integers for these known meme coins
            if coin in ['kPEPE', 'WIF', 'PEPE', 'BONK', 'SHIB']: 
                decimals = 0
            
            if decimals == 0: return int(size)
            factor = 10 ** decimals
            return math.floor(size * factor) / factor
        except:
            return int(size)

    def cancel_active_orders(self, coin):
        if not self.exchange: return False
        try:
            self.exchange.cancel_all_orders(coin)
            return True
        except: return False

    def place_market_order(self, coin, side, size):
        if not self.exchange: return False
        try:
            final_size = self._get_precise_size(coin, size)
            is_buy = (side == "BUY")
            
            print(f">> EXEC {coin} {side} {final_size}...")
            result = self.exchange.market_open(coin, is_buy, final_size, None, 0.05)
            
            if result['status'] == 'ok':
                return True
            else:
                print(f"xx REJECT: {result}")
                return False
        except Exception as e:
            print(f"xx EXEC ERROR: {e}")
            return False

    def place_trap(self, coin, side, price, size_usd):
        if not self.exchange: return False
        try:
            is_buy = (side == "BUY")
            raw_size = size_usd / float(price)
            final_size = self._get_precise_size(coin, raw_size)
            final_price = float(f"{float(price):.5g}")
            
            self.exchange.order(coin, is_buy, final_size, final_price, {"limit": {"tif": "Gtc"}})
            return True
        except: return False
