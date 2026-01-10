import json
import os
import subprocess
from datetime import datetime

class Messenger:
    def __init__(self):
        print(">> Messenger (Discord) Loaded")
        # Load from Env Vars (Railway)
        self.webhooks = {
            "trades": os.environ.get("DISCORD_TRADES"),
            "errors": os.environ.get("DISCORD_ERRORS"),
            "info":   os.environ.get("DISCORD_INFO")
        }

    def _send_payload(self, channel, payload):
        """Internal method to send data via Curl (Robustness)"""
        url = self.webhooks.get(channel)
        if not url: return

        try:
            # Using Curl for maximum container compatibility
            subprocess.Popen([
                "curl", "-H", "Content-Type: application/json",
                "-d", json.dumps(payload),
                url
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"xx MSG FAILED: {e}")

    def send_info(self, message):
        """Called by main.py for startup/status updates"""
        payload = {
            "username": "Luma Guardian",
            "embeds": [{
                "title": "ℹ️ System Info",
                "description": message,
                "color": 3447003, # Blue
                "footer": {"text": datetime.utcnow().strftime('%H:%M:%S')}
            }]
        }
        self._send_payload("info", payload)

    def send_error(self, message):
        """Called by main.py for critical failures"""
        payload = {
            "username": "Luma Guardian",
            "embeds": [{
                "title": "🚨 Critical Error",
                "description": message,
                "color": 15158332, # Red
                "footer": {"text": datetime.utcnow().strftime('%H:%M:%S')}
            }]
        }
        self._send_payload("errors", payload)

    def send_trade(self, coin, signal, price, size):
        """Called by main.py for Buy/Sell signals"""
        is_buy = "BUY" in signal or "BREAKOUT" in signal
        color = 5763719 if is_buy else 15548997 # Green vs Red
        
        msg = f"**SIGNAL:** {signal}\n**PRICE:** ${price}\n**SIZE:** ${size}"
        
        payload = {
            "username": "Luma Guardian",
            "embeds": [{
                "title": f"⚡ TRADE: {coin}",
                "description": msg,
                "color": color,
                "footer": {"text": datetime.utcnow().strftime('%H:%M:%S')}
            }]
        }
        self._send_payload("trades", payload)
