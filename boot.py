import threading
import time
import os
import http.server
import socketserver
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
                self.wfile.write(b'{"status": "BOOTING", "equity": "---"}')
        else:
            super().do_GET()

def start_server():
    """Starts the Web Server to satisfy Railway Healthcheck"""
    print(f"🦅 LUMA: Server listening on {PORT}")
    with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
        httpd.serve_forever()

# 2. SETUP THE TRADING BOT (The Muscle)
def start_bot():
    """Starts the Trading Engine in the background"""
    time.sleep(3) # Wait 3s for server to settle
    print("🦅 LUMA: Launching Trading Engine...")
    try:
        import main
        main.main_loop()
    except Exception as e:
        print(f"xx CRITICAL BOT FAILURE: {e}")

if __name__ == "__main__":
    # A. Launch Bot in Background Thread (Daemon)
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()

    # B. Launch Server in Main Thread (Blocking)
    # This keeps the app 'alive' for Railway
    start_server()
