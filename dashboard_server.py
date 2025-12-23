import http.server
import socketserver
import os
import json
import threading
import time
import sys
from config import conf

# 1. SETUP PORT (Crucial for Railway)
PORT = int(os.environ.get("PORT", 8080))

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/data":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            state_path = conf.get_path("dashboard_state.json")
            if os.path.exists(state_path):
                with open(state_path, "r") as f:
                    self.wfile.write(f.read().encode())
            else:
                self.wfile.write(json.dumps({
                    "status": "BOOTING...", 
                    "equity": "---", 
                    "events": "System Starting..."
                }).encode())
        else:
            super().do_GET()

def launch_trading_bot():
    """Starts the trading engine in the background"""
    print(">> SERVER: Launching Trading Engine...")
    time.sleep(2) # Wait 2s to ensure Server is fully alive
    try:
        import main
        main.main_loop()
    except Exception as e:
        print(f"xx BOT DIED: {e}")

if __name__ == "__main__":
    # 2. START SERVER FIRST (To pass Healthcheck)
    print(f"🦅 DASHBOARD ONLINE: Listening on port {PORT}")
    
    # Create the server object
    server = socketserver.TCPServer(("", PORT), DashboardHandler)

    # 3. LAUNCH BOT IN BACKGROUND THREAD
    bot_thread = threading.Thread(target=launch_trading_bot, daemon=True)
    bot_thread.start()

    # 4. RUN SERVER FOREVER (Main Process)
    try:
        server.serve_forever()
    except Exception as e:
        print(f"xx SERVER FAILED: {e}")
