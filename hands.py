import time
from web3 import Web3
from eth_account import Account
import json
import os

class Hands:
    def __init__(self, config=None):
        """
        The Execution Module (Hands).
        Updated to handle optional config to maintain compatibility with main.py calls.
        """
        # FIX: Handle cases where config is not passed (main.py calls Hands() empty)
        self.config = config if config else {}
        
        self.w3 = None
        self.account = None
        self.wallet_address = None
        self.connected = False
        
        # Initialize Connection
        self._connect()

    def _connect(self):
        try:
            # 1. Setup Web3 Provider
            # Look in config first, then environment variable, then default to localhost
            rpc_url = self.config.get('RPC_URL', os.getenv('RPC_URL', 'http://127.0.0.1:8545'))
            self.w3 = Web3(Web3.HTTPProvider(rpc_url))
            
            if not self.w3.is_connected():
                print(">> HANDS ERROR: Could not connect to RPC.")
                # We do not return here to allow the bot to start in 'Offline Mode' if needed
            
            # 2. Load Wallet
            # Look in config first, then environment variable
            private_key = self.config.get('PRIVATE_KEY', os.getenv("PRIVATE_KEY"))
            
            if not private_key:
                print(">> HANDS ERROR: No Private Key found in environment.")
                self.connected = False
                return
            
            self.account = Account.from_key(private_key)
            
            # --- CRITICAL FIX [2026-01-10] ---
            # Solves the 'LocalAccount object is not subscriptable' error
            self.wallet_address = self.account.address
            self._private_key = self.account.key
            # ---------------------------------

            self.connected = True
            print(f">> Hands (Execution Module) Loaded")
            print(f">> Wallet Connected: {self.wallet_address[:6]}...{self.wallet_address[-4:]}")

        except Exception as e:
            print(f">> HANDS INIT ERROR: {e}")
            self.connected = False

    def execute_trade(self, token_address, action, amount_usd):
        """
        Executes a swap.
        """
        if not self.connected or not self.account:
            print(">> EXECUTION FAILED: Hands not connected.")
            return False

        print(f">> HANDS: Executing {action} on {token_address} for ${amount_usd}...")
        
        # Placeholder for actual router interaction (Uniswap/Raydium etc.)
        time.sleep(1) # Simulation of network latency
        return True

    def get_balance(self):
        if self.connected and self.w3 and self.w3.is_connected():
            try:
                balance_wei = self.w3.eth.get_balance(self.wallet_address)
                return self.w3.from_wei(balance_wei, 'ether')
            except Exception as e:
                print(f">> HANDS ERROR (Get Balance): {e}")
                return 0.0
        return 0.0
