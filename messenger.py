import json
import os
import requests  # Replaces the unstable 'subprocess' method

class Messenger:
    def __init__(self):
        print(">> Messenger (Discord v3.5: Native Requests) Loaded")
        self.config_file = "server_config.json"
        self.webhooks = self._load_webhooks()

    def _load_webhooks(self):
        # 1. Try Env Vars (Your Railway/Cloud Config)
        webhooks = {
            "info": os.environ.get("DISCORD_INFO"),
            "trades": os.environ.get("DISCORD_TRADES"),
            "errors": os.environ.get("DISCORD_ERRORS")
        }
        
        # Check if they exist in Env Vars first
        if any(webhooks.values()):
            # Cleanup: Remove None values if some are missing
            return {k: v for k, v in webhooks.items() if v}

        # 2. Fallback to file (for local testing)
        try:
            with open(self.config_file, 'r') as f:
                cfg = json.load(f)
                return cfg.get('discord_webhooks', {})
        except: return {}

    def send(self, channel, message):
        url = self.webhooks.get(channel)
        if not url: 
            # Silent return if no webhook configured for this channel
            return
        
        data = {"content": message}
        try:
            # FIX: Use requests.post instead of subprocess/curl
            # timeout=2.0 ensures this never freezes your trading loop
            resp = requests.post(url, json=data, timeout=2.0)
            
            # Error Handling: Print if Discord rejects it (e.g. 404 or 429)
            if resp.status_code not in [200, 204]:
                print(f"xx DISCORD ERROR [{resp.status_code}]: {resp.text}")
                
        except Exception as e:
            print(f"xx MSG FAILED: {e}")

    def notify_trade(self, coin, side, price, size):
        # Format: 🦅 EXECUTED: BUY SPX | Price: $0.45 | Size: $1000
        msg = f"🦅 **EXECUTED:** {side} **{coin}**\nPrice: `${price}`\nSize: `${size}`"
        self.send("trades", msg)

    def notify_error(self, error):
        msg = f"⚠️ **CRITICAL ERROR:**\n`{error}`"
        self.send("errors", msg)
