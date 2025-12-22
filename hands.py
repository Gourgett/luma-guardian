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
            self.account: LocalAccount = eth_account.Account.from_key(conf.private_key)
            self.info = Info(conf.base_url, skip_ws=True)
            self.exchange = Exchange(self.account, conf.base_url, self.account.address)
            
            # 1. LOAD PRECISION RULES
            print(">> HANDS: Calibrating Precision...")
            self.meta = self.info.meta()
            self.coin_info = {}
            for asset in self.meta['universe']:
                self.coin_info[asset['name']] = {
                    'sz_decimals': asset['szDecimals'],
                    'max_decimals': 6
                }
            print(">> HANDS ARMED: Calibration Complete.")
        except Exception as e:
            print(f"xx HANDS INITIALIZATION FAILED: {e}")

    def _round_size(self, coin, size):
        # Round size to the exact decimals the asset allows
        info = self.coin_info.get(coin, {'sz_decimals': 2})
        decimals = info['sz_decimals']
        if decimals == 0: return int(size)
        return round(size, decimals)

    def _round_price(self, price):
        if price == 0: return 0.0
        try:
            # Hyperliquid requires max 5 significant figures
            sig_figs = 5
            magnitude = math.floor(math.log10(abs(price)))
            decimals = sig_figs - 1 - magnitude
            if decimals < 0: decimals = 0
            if decimals > 6: decimals = 6
            return round(price, int(decimals))
        except:
            return float(f"{price:.4f}")

    def set_leverage_all(self, coins, leverage):
        for coin in coins:
            try: self.exchange.update_leverage(leverage, coin)
            except: pass

    def place_market_order(self, coin, side, size):
        # THIS executes the Ratchet (Stop Loss/Take Profit)
        try:
            final_size = self._round_size(coin, size)
            is_buy = True if side == "BUY" else False
            
            if final_size <= 0: return False

            print(f">> EXECUTING MARKET: {side} {coin} Size: {final_size}")
            
            # CRITICAL FIX: SLIPPAGE TOLERANCE
            # Default is often 1%. We set to 5% (0.05) to ensure execution during crashes.
            # "slippage" is the 4th argument in market_open(coin, is_buy, size, px, slippage)
            result = self.exchange.market_open(coin, is_buy, final_size, None, 0.05)
            
            if result['status'] == 'ok': return True
            else:
                print(f"xx MARKET REJECTED: {result}")
                return False
        except Exception as e:
            print(f"xx MARKET FAIL: {e}")
            return False

    def place_trap(self, coin, side, price, size_usd):
        # Used for Entry Limits
        try:
            is_buy = True if side == "BUY" else False
            price = float(price)
            size_coins = size_usd / price
            
            final_size = self._round_size(coin, size_coins)
            final_price = self._round_price(price)

            print(f">> SETTING TRAP: {side} {coin} @ {final_price}")
            self.exchange.order(coin, is_buy, final_size, final_price, {"limit": {"tif": "Gtc"}})
            return True
        except Exception as e:
            print(f"xx TRAP FAIL: {e}")
            return False
