import json
import requests
import time
from config import conf 

class Messenger:
    def __init__(self):
        self.hooks = conf.discord_hooks
        # Fallback: If CFO hook is missing, send finance data to INFO channel
        self.cfo_hook = self.hooks.get("cfo") or self.hooks.get("info")

    def _send_payload(self, url, payload):
        """Internal engine to push data to Discord"""
        if not url: return
        try:
            requests.post(url, json=payload)
        except Exception as e:
            print(f"xx MSG FAIL: {e}")

    def send(self, channel_key, text):
        """Legacy text sender for simple logs"""
        url = self.hooks.get(channel_key)
        self._send_payload(url, {"content": text})

    def notify_trade(self, coin, signal, price, size):
        """Sends a RICH EMBED for trading activity"""
        url = self.hooks.get("trades")
        if not url: return

        # 1. Determine Identity (Buy/Sell/Green/Red)
        signal = signal.upper()
        if "BUY" in signal or "LONG" in signal:
            color = 5763719  # GREEN (0x57F287)
            emoji = "🟢"
            action = "OPEN LONG"
        elif "SELL" in signal or "SHORT" in signal:
            color = 15548997 # RED (0xED4245)
            emoji = "🔴"
            action = "OPEN SHORT"
        else:
            color = 3447003  # BLUE
            emoji = "🔵"
            action = "ORDER"

        # 2. Format Price
        try:
            if str(price).lower() == "market":
                p_str = "Market Price"
            else:
                p_str = f"${float(price):,.4f}"
        except: p_str = str(price)

        # 3. Construct the Embed
        payload = {
            "embeds": [{
                "title": f"{emoji} {action}: {coin}",
                "color": color,
                "fields": [
                    {"name": "Entry Price", "value": p_str, "inline": True},
                    {"name": "Position Size", "value": f"${size}", "inline": True},
                    {"name": "Signal Type", "value": signal, "inline": True}
                ],
                "footer": {"text": f"Luma Cloud • {time.strftime('%H:%M:%S')}"}
            }]
        }
        self._send_payload(url, payload)

    def notify_financial(self, equity, pnl, active_count, mode):
        """Sends a FINANCIAL REPORT to the CFO/Info channel"""
        url = self.cfo_hook
        if not url: return

        # Color based on PnL (Green if profitable, Red if loss, Gray if flat)
        if pnl > 0: color = 5763719 # Green
        elif pnl < 0: color = 15548997 # Red
        else: color = 9807270 # Gray

        payload = {
            "embeds": [{
                "title": "💰 Luma Financial Report",
                "color": color,
                "fields": [
                    {"name": "Total Equity", "value": f"${equity:,.2f}", "inline": True},
                    {"name": "Session PnL", "value": f"${pnl:+.2f}", "inline": True},
                    {"name": "Active Positions", "value": str(active_count), "inline": True},
                    {"name": "Risk Mode", "value": mode, "inline": False}
                ],
                "footer": {"text": f"System Heartbeat • {time.strftime('%H:%M:%S')}"}
            }]
        }
        self._send_payload(url, payload)
        
    def notify_error(self, error_msg):
        """Alerts the error channel"""
        url = self.hooks.get("errors")
        if not url: return
        
        payload = {
            "content": "@everyone ⚠️ **SYSTEM ALERT**",
            "embeds": [{
                "description": str(error_msg),
                "color": 15548997 # RED
            }]
        }
        self._send_payload(url, payload)
