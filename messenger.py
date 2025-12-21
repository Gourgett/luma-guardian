import json
import requests
from config import conf 

class Messenger:
    def __init__(self):
        self.hooks = conf.discord_hooks

    def send(self, channel, message):
        url = self.hooks.get(channel)
        if url:
            try: requests.post(url, json={"content": message})
            except: pass
            
    def notify_trade(self, coin, signal, price, size):
        self.send("trades", f"🦅 **LUMA CLOUD:** {signal} {coin} @ {price} (${size})")
