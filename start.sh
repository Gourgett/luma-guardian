#!/bin/bash

# 1. Start the Dashboard in the background (So Railway sees the port OPEN)
python dashboard_server.py &

# 2. Start the Trading Bot in the foreground (So it keeps running)
python main.py
