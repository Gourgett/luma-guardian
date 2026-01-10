import json
import time
import os
import logging
from eth_account import Account
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants

class Hands:
    def __init__(self, config=None):
        """
        LUMA EXECUTION MODULE (Hyperliquid Restore)
        Restores ability to trade SOL, SUI, BNB, and MEMES via Perps.
        """
        print(">> Hands (Execution): Initializing Hyperliquid Bridge...")
        self.config = config if config else self._load_local_config()
        
        # 1. Credentials
        self.private_key = self.config.get('private_key') or os.getenv("PRIVATE_KEY")
        self.wallet_address = self.config.get('wallet_address') or os.getenv("WALLET_ADDRESS")

        if not self.private_key:
            print(">> HANDS ERROR: Missing Private Key. Execution Disabled.")
            self.exchange = None
            return

        # 2. Connect to Exchange
        try:
            self.account = Account.from_key(self.private_key)
            # Ensure address matches key derivation
            if not self.wallet_address:
                self.wallet_address = self.account.address
            
            # API Connection
            self.info = Info(constants.MAINNET_API_URL, skip_ws=True)
            self.exchange = Exchange(self.account, constants.MAINNET_API_URL)
            print(f">> HANDS ARMED: Connected to Hyperliquid [{self.wallet_address[:6]}...]")
            
        except Exception as e:
            print(f">> HANDS CONNECTION FAILED: {e}")
            self.exchange = None

    def _load_local_config(self):
        try:
            with open("server_config.json", "r") as f:
                return json.load(f)
        except:
            return {}

    def _get_precision(self, coin):
        # BLUEPRINT PRECISION MAP (Source: Termux Dump)
        # (Price Decimals, Size Decimals)
        if coin == "SOL":   return (2, 2)
        if coin == "SUI":   return (4, 1)
        if coin == "BNB":   return (1, 3) # Added BNB
        if coin == "WIF":   return (4, 1)
        if coin == "DOGE":  return (5, 0)
        if coin == "PENGU": return (5, 0)
        # Default
        return (4, 1)

    def cancel_all_orders(self, coin):
        """Sweeps active orders for a specific coin to prevent conflicts."""
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
        """Places a Limit Order (The Trap)."""
        if not self.exchange: return
        
        # 1. Cleanup
        self.cancel_all_orders(coin)

        # 2. Calculate Precision
        px_prec, sz_prec = self._get_precision(coin)
        final_price = round(price, px_prec)
        
        if final_price == 0: return

        # 3. Calculate Size in Coins
        raw_size = size_usd / final_price
        if sz_prec == 0:
            final_size = int(raw_size)
        else:
            final_size = round(raw_size, sz_prec)

        if final_size == 0:
            print(f"xx SIZE ERROR: {size_usd} USD is too small for {coin}")
            return

        # 4. Execute
        print(f">> 🕸️ TRAP: {side} {coin} @ {final_price} (Size: {final_size})")
        try:
            is_buy = True if side == "BUY" else False
            # Gtc = Good Til Cancelled
            res = self.exchange.order(coin, is_buy, final_size, final_price, {"limit": {"tif": "Gtc"}})
            
            if res['status'] == 'err':
                print(f"xx EXCHANGE REJECTED: {res['response']}")
            else:
                print(f">> ORDER CONFIRMED.")
                
        except Exception as e:
            print(f"xx ORDER EXCEPTION: {e}")

    def place_market_order(self, coin, side, size_coins):
        """Panic/Secure Profit execution."""
        if not self.exchange: return
        try:
            _, sz_prec = self._get_precision(coin)
            if sz_prec == 0:
                sz = int(size_coins)
            else:
                sz = round(float(size_coins), sz_prec)

            is_buy = True if side == "BUY" else False
            print(f"⚡ MARKET {side}: {coin} x {sz}")
            self.exchange.market_open(coin, is_buy, sz)
            
        except Exception as e:
            print(f"xx MARKET FAIL: {e}")

    def update_leverage(self, coin, lev):
        if not self.exchange: return
        try:
            self.exchange.update_leverage(lev, coin)
            # print(f">> Lev set to {lev}x for {coin}")
        except: pass
