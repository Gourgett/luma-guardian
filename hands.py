import json
import time
import os
from eth_account import Account
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants

class Hands:
    def __init__(self, config=None):
        print(">> HANDS ARMED: Initializing Hyperliquid Bridge...")
        
        # Load Keys (Railway Env Vars)
        self.private_key = os.getenv("PRIVATE_KEY")
        self.wallet_address = os.getenv("WALLET_ADDRESS")
        
        if config and not self.private_key:
            self.private_key = config.get("private_key")
            self.wallet_address = config.get("wallet_address")

        if not self.private_key:
            print(">> HANDS ERROR: Missing Private Key. Execution Disabled.")
            self.exchange = None
            self.wallet_address = None
            return

        try:
            # Initialize Hyperliquid Connection
            self.account = Account.from_key(self.private_key)
            if not self.wallet_address:
                self.wallet_address = self.account.address
            
            self.info = Info(constants.MAINNET_API_URL, skip_ws=True)
            self.exchange = Exchange(self.account, constants.MAINNET_API_URL)
            print(f">> HANDS CONNECTED: {self.wallet_address[:8]}...")
            
        except Exception as e:
            print(f"xx HANDS CONNECTION FAILED: {e}")
            self.exchange = None
            self.wallet_address = None

    def _get_precision(self, coin):
        # HARDCODED FLEET PRECISION
        if coin == "SOL":   return (2, 2)
        if coin == "SUI":   return (4, 1)
        if coin == "BNB":   return (1, 3)
        if coin == "WIF":   return (4, 1)
        if coin == "DOGE":  return (5, 0)
        if coin == "PENGU": return (5, 0)
        return (4, 1)

    def cancel_all_orders(self, coin):
        if not self.exchange: return
        try:
            open_orders = self.info.open_orders(self.wallet_address)
            for order in open_orders:
                if order['coin'] == coin:
                    self.exchange.cancel(coin, order['oid'])
                    print(f">> 🧹 SWEEP: Cancelled active order on {coin}")
        except Exception as e:
            print(f"xx CLEANUP ERROR: {e}")

    def place_trap(self, coin, side, price, size_usd):
        if not self.exchange: return
        self.cancel_all_orders(coin)

        px_prec, sz_prec = self._get_precision(coin)
        final_price = round(price, px_prec)
        
        if final_price == 0: return

        raw_size = size_usd / final_price
        if sz_prec == 0: final_size = int(raw_size)
        else: final_size = round(raw_size, sz_prec)

        if final_size == 0: return

        print(f">> 🕸️ TRAP: {side} {coin} @ {final_price} (Size: {final_size})")
        try:
            is_buy = True if side == "BUY" else False
            res = self.exchange.order(coin, is_buy, final_size, final_price, {"limit": {"tif": "Gtc"}})
            if res['status'] == 'err':
                print(f"xx REJECTED: {res['response']}")
        except Exception as e:
            print(f"xx ORDER EXCEPTION: {e}")

    def place_market_order(self, coin, side, size_usd):
        # NOTE: size_usd is passed here. We convert to coins.
        if not self.exchange: return
        try:
            # 1. Get Price for Conversion
            # We assume current price is close to last trade, or we fetch fresh?
            # For speed, we just trust the call, but ideally we fetch price here.
            # Simplified: We treat size_usd as "number of coins" if the caller failed to convert,
            # BUT main.py passes 60.0 USD. We need the price.
            
            # SAFEGUARD: To avoid crash, we need to fetch price to convert USD -> Coins
            # Since Hands shouldn't depend on Vision, we use the Exchange info if possible,
            # or we rely on the caller to pass 'size_coins'. 
            
            # HOTFIX for Main.py passing USD:
            # We will use the 'allMids' from info to convert quickly.
            prices = self.info.all_mids()
            price = float(prices.get(coin, 0))
            if price == 0: return

            size_coins = size_usd / price

            _, sz_prec = self._get_precision(coin)
            if sz_prec == 0: sz = int(size_coins)
            else: sz = round(float(size_coins), sz_prec)

            is_buy = True if side == "BUY" else False
            print(f"⚡ MARKET {side}: {coin} x {sz}")
            self.exchange.market_open(coin, is_buy, sz)
        except Exception as e:
            print(f"xx MARKET FAIL: {e}")
