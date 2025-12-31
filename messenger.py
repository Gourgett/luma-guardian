import json
import os
import time
import subprocess

class Messenger:
    def __init__(self):
        print(">> Messenger (Discord) Loaded")
        self.config_file = "server_config.json"
        self.webhooks = self._load_webhooks()

    def _load_webhooks(self):
        # 1. Try Env Vars (Railway)
        webhooks = {
            "info": os.environ.get("WEBHOOK_INFO"),
            "trades": os.environ.get("WEBHOOK_TRADES"),
            "errors": os.environ.get("WEBHOOK_ERRORS")
        }
        # If any found, return them
        if any(webhooks.values()):
            return webhooks

        # 2. Fallback to file
        try:
            with open(self.config_file, 'r') as f:
                cfg = json.load(f)
                return cfg.get('discord_webhooks', {})
        except: return {}

    def send(self, channel, message):
        url = self.webhooks.get(channel)
        if not url: return
        
        data = {"content": message}
        try:
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
