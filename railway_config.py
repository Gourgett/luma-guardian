import os
import json

# RAILWAY PERSISTENCE CONFIG
# We will mount a volume at /app/data to keep memory safe between restarts.
DATA_DIR = "/app/data"
if not os.path.exists(DATA_DIR):
    # Fallback for local testing
    DATA_DIR = "."

class Config:
    def __init__(self):
        # 1. Try Loading from Environment Variables (Railway Standard)
        self.wallet_address = os.environ.get("WALLET_ADDRESS")
        self.private_key = os.environ.get("PRIVATE_KEY")
        
        # 2. Discord Webhooks
        self.discord_hooks = {
            "trades": os.environ.get("DISCORD_TRADES"),
            "errors": os.environ.get("DISCORD_ERRORS"),
            "info": os.environ.get("DISCORD_INFO")
        }

        # 3. Fallback: Try loading local JSON (Only for local testing)
        if not self.wallet_address:
            try:
                with open("server_config.json") as f:
                    data = json.load(f)
                    self.wallet_address = data.get("wallet_address")
                    self.private_key = data.get("private_key")
                    self.discord_hooks = data.get("discord_webhooks", {})
            except: pass

    def get_path(self, filename):
        # Ensures files are saved to the Persistent Volume
        return os.path.join(DATA_DIR, filename)

# Initialize Global Config
conf = Config()
