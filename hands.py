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

            # 1. LOAD RULES FROM EXCHANGE
            self.meta = self.info.meta()
            self.coin_rules = {}
            for asset in self.meta['universe']:
                self.coin_rules[asset['name']] = asset['szDecimals']
            
            # 2. SAFETY OVERRIDES (The "Anti-Reject" Layer)
            # We explicitly force these coins to Integer-Only (0 decimals)
            # This prevents the "Default to 2" bug that kills kPEPE orders.
            self.manual_overrides = {
                'kPEPE': 0,
                'WIF': 0,
                'PEPE': 0,
                'BONK': 0,
                'SHIB': 0
            }
            
            print(f">> HANDS ARMED: Loaded {len(self.coin_rules)} Assets (With Safety Overrides)")
        except Exception as e:
            print(f"xx HANDS INIT FAIL: {e}")
            # Fallback to empty if init fails, logic below handles it
            self.coin_rules = {}
            self.manual_overrides = {'kPEPE': 0, 'WIF': 0}

    def _get_precise_size(self, coin, size):
        """
        Determines the exact allowed size format.
        Priority: 
        1. Manual Override (Safety)
        2. Exchange Rule (Meta)
        3. Default (2 decimals)
        """
        try:
            # CHECK OVERRIDE FIRST
            if coin in self.manual_overrides:
                decimals = self.manual_overrides[coin]
            else:
                decimals = self.coin_rules.get(coin, 2) # Default to 2 if unknown
            
            # THE INTEGER FORCE (For kPEPE/WIF)
            if decimals == 0:
                return int(size) 
            
            # THE TRUNCATOR (For SOL/ETH)
            factor = 10 ** decimals
            truncated = math.floor(size * factor) / factor
            return truncated
            
        except Exception as e:
            print(f"xx FORMAT ERROR {coin}: {e}")
            return int(size) # Panic fallback to integer

    def set_leverage_all(self, coins, leverage):
        for coin in coins:
            try: self.exchange.update_leverage(leverage, coin)
            except: pass

    def place_market_order(self, coin, side, size):
        try:
            # STEP 1: Format Size
            final_size = self._get_precise_size(coin, size)
            is_buy = True if side == "BUY" else False

            if final_size <= 0: 
                print(f"xx SIZE ZERO {coin}")
                return False

            print(f">> EXEC {coin} {side}: {final_size}")
            
            # STEP 2: Send Order (5% Slippage for Volatility)
            result = self.exchange.market_open(coin, is_buy, final_size, None, 0.05)

            if result['status'] == 'ok': 
                return True
            else:
                # If this prints, it's a balance or limit issue
                print(f"xx REJECT {coin}: {result}")
                return False
        except Exception as e:
            print(f"xx EXEC ERROR {coin}: {e}")
            return False

    def place_trap(self, coin, side, price, size_usd):
        try:
            is_buy = True if side == "BUY" else False
            
            # Calculate raw size
            raw_size = size_usd / float(price)
            
            # Format Size
            final_size = self._get_precise_size(coin, raw_size)
            
            # Format Price (5 Sig Figs)
            final_price = float(f"{float(price):.5g}")
            
            self.exchange.order(coin, is_buy, final_size, final_price, {"limit": {"tif": "Gtc"}})
            return True
        except: return False
