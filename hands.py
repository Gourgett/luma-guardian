import json
import time
import os
import math
from eth_account import Account
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants

class Hands:
    def __init__(self):
        print(">> HANDS ARMED: Exchange Connected (v3.5: DYNAMIC LEV)")
        self.config = self._load_config()
        
        # Priority: Railway Env Var -> server_config.json
        key = os.environ.get("PRIVATE_KEY") or self.config.get('private_key') or self.config.get('secret_key')
        
        if not key:
            raise ValueError("CRITICAL: No 'PRIVATE_KEY' found in Environment Variables.")

        self.account = Account.from_key(key)
        self.address = os.environ.get("WALLET_ADDRESS") or self.config.get('wallet_address')
        
        self.info = Info(constants.MAINNET_API_URL, skip_ws=True)
        self.exchange = Exchange(self.account, constants.MAINNET_API_URL)
        
        # --- UNIVERSAL SIZING FIX ---
        # Load the "Universe" (Metadata) from Hyperliquid to get exact decimals for EVERY coin.
        try:
            print(">> HANDS: Loading Universe Metadata...")
            self.meta = self.info.meta()
            # Create a lookup dictionary: {'BTC': {'szDecimals': 3}, ...}
            self.coin_map = {c['name']: c for c in self.meta['universe']}
            print(">> HANDS: Universe Loaded (Universal Sizing Active).")
        except Exception as e:
            print(f"xx HANDS WARNING: Could not load Universe: {e}")
            self.coin_map = {}

    def _load_config(self):
        try:
            with open("server_config.json") as f:
                return json.load(f)
        except: return {}

    def set_leverage_all(self, coins, leverage):
        """
        V4.3 Compatible: Accepts dynamic leverage (3x or 5x).
        """
        print(f">> HANDS: Enforcing {leverage}x Leverage on Fleet...")
        for coin in coins:
            try:
                # The Fix: We explicitly cast to int here just to be 100% safe
                self.exchange.update_leverage(int(leverage), coin)
            except Exception as e:
                # The Fix: No more silent failing. We print the error.
                print(f"xx LEVERAGE FAILED for {coin}: {e}")
        # print(">> HANDS: Leverage Synced.")

    def cancel_all_orders(self, coin):
        try:
            open_orders = self.info.open_orders(self.address)
            for order in open_orders:
                if order['coin'] == coin:
                    print(f"🧹 SWEEPING: Canceling old order for {coin}")
                    self.exchange.cancel(coin, order['oid'])
                    time.sleep(0.5)
        except Exception as e:
            print(f"xx CLEANUP FAILED: {e}")

    def _get_precision(self, coin):
        # --- UNIVERSAL LOOKUP ---
        # Instead of a hardcoded list, we ask the Exchange what the rule is.
        if coin in self.coin_map:
            # Get the official size decimals allowed by Hyperliquid
            sz_dec = self.coin_map[coin]['szDecimals']
            # Price precision is generally safe at 5 or 6 decimals for calculations
            return (5, sz_dec)
        
        # Fallback for unexpected coins (Safety Net)
        return (4, 1)

    def place_trap(self, coin, side, price, size_usd):
        """
        Placing a Limit Order. 
        Returns: TRUE if successful, FALSE if rejected.
        """
        self.cancel_all_orders(coin)
        px_prec, sz_prec = self._get_precision(coin)
        final_price = round(price, px_prec)

        # Main.py passes size in USD (Notional). We convert to Coins here.
        raw_size = size_usd / final_price
        if sz_prec == 0:
            final_size = int(raw_size)
        else:
            final_size = round(raw_size, sz_prec)

        if final_size == 0:
            print(f"xx SIZE TOO SMALL: {size_usd} -> 0 {coin}")
            return False

        print(f">> SETTING TRAP: {side} {coin} @ ${final_price} (Size: {final_size})")

        try:
            is_buy = True if side == "BUY" else False
            # We use Gtc (Good Til Canceled) to ensure it hits the book
            result = self.exchange.order(coin, is_buy, final_size, final_price, {"limit": {"tif": "Gtc"}})
            
            # --- CRITICAL FIX: RETURN RECEIPT ---
            if result['status'] == 'ok':
                return True
            elif result['status'] == 'err':
                print(f"xx EXCHANGE REJECTED {coin}: {result['response']}")
                return False
            else:
                return False

        except Exception as e:
            print(f"xx ORDER REJECTED (SDK): {e}")
            return False

    def place_market_order(self, coin, side, size_coins):
        """
        Executes Market Order.
        Used by DeepSea for Stop Losses and Take Profits.
        """
        is_buy = True if side == "BUY" else False
        try:
            _, sz_prec = self._get_precision(coin)
            if sz_prec == 0: sz = int(size_coins)
            else: sz = round(float(size_coins), sz_prec)
            
            if sz == 0: return False
            print(f"⚡ CASTING SPELL: MARKET {side} {sz} {coin}")
            
            result = self.exchange.market_open(coin, is_buy, sz)
            
            if result['status'] == 'ok':
                return True
            else:
                print(f"xx MARKET FAILED: {result['response']}")
                return False
                
        except Exception as e:
            print(f"xx MARKET EXECUTION FAILED: {e}")
            return False

    def place_stop(self, coin, price):
        # Placeholder if needed later
        pass
