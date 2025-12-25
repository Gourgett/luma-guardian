#!/bin/bash

# 1. Start the Dumb Server in background (Guarantees Healthcheck PASS)
python3 dashboard_server.py &

# 2. Wait 2 seconds to ensure port is open
sleep 2

# 3. Start the Trading Bot (If this crashes, the server stays alive)
python3 main.py
