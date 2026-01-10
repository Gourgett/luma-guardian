import json
import os
import subprocess

class Messenger:
    def __init__(self):
        print(">> Messenger (Discord) Loaded")
        # Load from Env Vars (Railway)
        self.webhooks = {
            "trades": os.environ.get("DISCORD_TRADES"),
            "errors": os.environ.get("DISCORD_ERRORS"),
            "info":   os.environ.get("DISCORD_INFO")
        }

    def send(self, channel, message):
        # channel: "info", "trades", or "errors"
        url = self.webhooks.get(channel)
        if not url: return

        data = {"content": message}
        try:
            # Using curl is safer/standard on many linux containers if requests isn't guaranteed
            # But since we have requirements.txt, you could use requests. 
            # Sticking to subprocess for robustness as per your blueprint preference.
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
