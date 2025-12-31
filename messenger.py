import json
import os
import time
# We use standard requests or curl if strictly standard libs,
# but for Termux 'requests' is usually standard or easily added.
# If requests is missing, we use a subprocess curl for 100% compatibility.
import subprocess

class Messenger:
    def __init__(self):
        print(">> Messenger (Discord) Loaded")
        self.config_file = "server_config.json"
        self.webhooks = self._load_webhooks()

    def _load_webhooks(self):
        try:
            with open(self.config_file, 'r') as f:
                cfg = json.load(f)
                return cfg.get('discord_webhooks', {})
        except: return {}

    def send(self, channel, message):
        # channel: "info", "trades", or "errors"
        url = self.webhooks.get(channel)
        if not url: return
        
        # Payload
        data = {"content": message}

        try:
            # Using curl is safer on Termux than assuming 'requests' library exists
            subprocess.Popen([
                "curl", "-H", "Content-Type: application/json",
                "-d", json.dumps(data),
                url
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"xx MSG FAILED: {e}")

    def notify_trade(self, coin, side, price, size):
        msg = f"🦅 **EXECUTED:** {side} **{coin}**\nPrice: `${price}`\nSize: `${size}`"
        self.send("trades", msg)

    def notify_error(self, error):
        msg = f"⚠️ **CRITICAL ERROR:**\n`{error}`"
        self.send("errors", msg)
