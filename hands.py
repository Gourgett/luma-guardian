import os
import time
import json
from eth_account import Account
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants
from hyperliquid.info import Info

class Hands:
    def __init__(self, private_key=None, wallet_address=None):
        print(">> Hands (Execution Module) Loaded")
        
        # 1. LOAD CREDENTIALS (Env Vars Priority)
        self.private_key = private_key or os.environ.get("PRIVATE_KEY")
        self.wallet_address = wallet_address or os.environ.get("WALLET_ADDRESS")
        
        if not self.private_key:
            print(">> ⚠️ HANDS ERROR: Missing Private Key (Env Vars or Args)")
            return

        # 2. INITIALIZE HYPERLIQUID SDK
        try:
            # Load Account (LocalAccount object)
            self.account = Account.from_key(self.private_key)
            
            # CRITICAL FIX: Handle LocalAccount object correctly (Dot notation vs Dictionary)
            # This fixes the "object is not subscriptable" error
            if hasattr(self.account, 'address'):
                derived_address = self.account.address
            else:
                # Fallback if library changes
                derived_address = str(self.account)

            # If wallet_address wasn't provided in env, use the derived one
            if not self.wallet_address:
                self.wallet_address = derived_address
            
            print(f">> Wallet Connected: {self.wallet_address[:6]}...{self.wallet_address[-4:]}")

            # Mainnet by default. Change base_url if using Testnet.
            self.info = Info(constants.MAINNET_API_URL, skip_ws=True)
            self.exchange = Exchange(self.account, constants.MAINNET_API_URL, self.account)
            
            print(">> Hands: Connected to Hyperliquid Mainnet")

        except Exception as e:
            print(f">> ⚠️ HANDS INIT ERROR: {e}")
            # We allow the bot to continue even if Hands fails, so it can still scan (Silent Mode)

    def get_positions(self):
        """
        Returns a normalized list of open positions.
        Format: [{'coin': 'WIF', 'size': 100.0, 'entry': 2.50, 'pnl': 5.0}, ...]
        """
        try:
            if not self.wallet_address: return []

            user_state = self.info.user_state(self.wallet_address)
            raw_pos = user_state.get("assetPositions", [])
            clean_pos = []
            
            for item in raw_pos:
                p = item.get("position", {})
                size = float(p.get("szi", 0))
                
                if size != 0:
                    clean_pos.append({
                        "coin": p.get("coin"),
                        "size": size,
                        "entry": float(p.get("entryPx", 0)),
                        "pnl": float(p.get("unrealizedPnl", 0))
                    })
            return clean_pos
            
        except Exception as e:
            print(f"xx HANDS (Get Pos) ERROR: {e}")
            return []

    def place_trap(self, coin, side, price, size_usd):
        """
        Places a Limit Order (The 'Trap').
        Auto-calculates the coin amount based on size_usd / price.
        """
        try:
            # Rounding for API precision (Hyperliquid is picky)
            # Calculate size in COINS (sz)
            sz = round(size_usd / price, 1) # 1 decimal place usually safe for memes
            if sz == 0: return # Too small
            
            # Hyperliquid expects price as string sometimes, but SDK handles floats well if rounded
            # Sig Figs: 5 for price usually safe
            px = round(price, 5) 
            
            is_buy = True if side.upper() == "BUY" else False
            
            print(f">> ✋ PLACING TRAP: {side} {coin} | ${size_usd} (@ {px})")
            
            # Execute Limit Order
            result = self.exchange.order(coin, is_buy, sz, px, {"limit": {"tif": "Gtc"}})
            
            if result.get("status") == "ok":
                return True
            else:
                print(f"xx ORDER FAILED: {result}")
                return False

        except Exception as e:
            print(f"xx TRAP ERROR: {e}")
            return False

    def place_market_order(self, coin, side, size_coin):
        """
        Executes an immediate Market Order (used for Stop Loss / Hard Take Profit).
        size_coin: The exact amount of coins to close (abs value).
        """
        try:
            is_buy = True if side.upper() == "BUY" else False
            sz = abs(round(size_coin, 1)) # Ensure positive size
            
            print(f">> 🚨 MARKET EXECUTION: {side} {coin} | Size: {sz}")
            
            # Execute Market Order (limit with Tif: Ioc can simulate, but SDK has market_open helper usually)
            # Standard generic order with is_buy, sz, px (ignored for market roughly), order_type
            
            # Using limit IOC with aggressive price crossing to simulate market
            # Buy = High Price, Sell = Low Price
            px = 999999 if is_buy else 0.00001
            
            result = self.exchange.order(coin, is_buy, sz, px, {"limit": {"tif": "Ioc"}})
            
            if result.get("status") == "ok":
                return True
            else:
                print(f"xx MARKET ORDER FAILED: {result}")
                return False

        except Exception as e:
            print(f"xx MARKET ERROR: {e}")
            return False

    def cancel_all(self, coin):
        # Helper to clear traps
        try:
            self.exchange.cancel_all_orders(coin)
        except: pass
