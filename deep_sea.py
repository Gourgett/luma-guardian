import time
import json
import os
from config import conf # NEW IMPORT

class DeepSea:
    def __init__(self):
        print(">> Deep Sea (Shield & Ratchet) Loaded")
        # SAVE STATE TO PERSISTENT VOLUME
        self.state_file = conf.get_path("ratchet_state.json")
        self.ratchet_state = self._load_state()
        self.secured_coins = list(self.ratchet_state.keys())

    # ... [KEEP THE REST OF YOUR FUNCTIONS EXACTLY THE SAME] ...
