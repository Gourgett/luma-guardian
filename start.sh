#!/bin/bash
# Start the Trading Bot in the background
python main.py &

# Start the Web Dashboard in the foreground
python dashboard_server.py
