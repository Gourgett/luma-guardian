#!/bin/bash

# 1. Start the Independent Dashboard in the background
# The '&' symbol is crucial—it lets the script continue to the next line immediately.
python3 dashboard_server.py &

# 2. Wait 3 seconds to ensure the port is open and Railway is happy
sleep 3

# 3. Start the Trading Bot in the foreground
# If the bot crashes, the logs will show here, but the server will stay alive.
python3 main.py
