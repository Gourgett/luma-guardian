import json
import time
import os
from eth_account import Account
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants
from config import conf # NEW IMPORT

class Hands:
    def __init__(self):
        print(">> HANDS ARMED: Exchange Connected")
        
        # KEY CHECK: Load directly from Secure Config
        key = conf.private_key
        if not key:
            raise ValueError("CRITICAL: No 'PRIVATE_KEY' found in Environment Variables")
            
        self.account = Account.from_key(key)
        self.address = conf.wallet_address
        self.info = Info(constants.MAINNET_API_URL, skip_ws=True)
        self.exchange = Exchange(self.account, constants.MAINNET_API_URL)

    # ... [KEEP THE REST OF YOUR FUNCTIONS (cancel_all_orders, _get_precision, etc.) EXACTLY THE SAME] ...
