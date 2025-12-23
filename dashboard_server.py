import http.server
import socketserver
import os
import json
import threading
import time
import sys
from config import conf

# PORT CONFIGURATION (Required for Railway)
PORT = int(os.environ.get("PORT", 8080))

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/data":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # Serve the state file, or empty default if not ready
            state_path = conf.get_path("dashboard_state.json")
            if os.path.exists(state_path):
                with open(state_path, "r") as f:
                    self.wfile.write(f.read().encode())
            else:
                # Default "Booting" state
                self.wfile.write(json.dumps({
                    "equity": "---", "cash": "---", "pnl": "---",
                    "status": "SYSTEM BOOTING...", "events": "Wait for init...",
                    "positions": "NO_TRADES", "radar": "", "updated": time.time()
                }).encode())
        else:
            # Serve the HTML dashboard
            super().do_GET()

def start_bot_logic():
    """Runs the main bot loop in a separate thread so it doesn't block the server"""
    print(">> SERVER: Launching Bot Logic in Background...")
    time.sleep(1) # Give server 1s to breathe
    try:
        import main
        main.main_loop()
    except Exception as e:
        print(f"xx BOT CRASHED: {e}")

if __name__ == "__main__":
    # 1. Start the Bot Thread
    bot_thread = threading.Thread(target=start_bot_logic, daemon=True)
    bot_thread.start()

    # 2. Start the Web Server (Main Thread)
    # This must happen on the main thread for Railway to detect the port binding
    print(f"🦅 LUMA DASHBOARD SERVER LISTENING ON PORT {PORT}")
    try:
        with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
            httpd.serve_forever()
    except Exception as e:
        print(f"xx SERVER CRASH: {e}")
