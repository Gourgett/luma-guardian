import threading
import time
import os
import http.server
import socketserver
import json
import sys
from config import conf

# 1. SETUP THE DASHBOARD SERVER (The Face)
PORT = int(os.environ.get("PORT", 8080))

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/data":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            try:
                with open(conf.get_path("dashboard_state.json"), "r") as f:
                    self.wfile.write(f.read().encode())
            except:
                self.wfile.write(b'{"status": "BOOTING", "equity": "---", "events": "System Starting..."}')
        else:
            super().do_GET()

def start_server():
    print(f"🦅 LUMA: Server listening on {PORT}")
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
        httpd.serve_forever()

# 2. SETUP THE TRADING BOT (The Muscle)
def start_bot():
    time.sleep(3) # Wait 3s for server to settle
    print("🦅 LUMA: Launching Trading Engine...")
    try:
        import main
        main.main_loop()
    except Exception as e:
        print(f"xx CRITICAL BOT FAILURE: {e}", file=sys.stderr)

if __name__ == "__main__":
    # Launch Bot in Background
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()

    # Launch Server in Main Thread (Satisfies Railway Healthcheck)
    start_server()
