import http.server
import socketserver
import os
import json

# Railway automatically provides the PORT
PORT = int(os.environ.get("PORT", 8080))
DATA_FILE = "data/dashboard_state.json"

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/data":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # Simple file read. No logic. No imports.
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, "r") as f:
                    self.wfile.write(f.read().encode())
            else:
                # If the bot hasn't written the file yet, we stay calm.
                self.wfile.write(b'{"status": "WAITING FOR BOT...", "equity": "---"}')
        else:
            super().do_GET()

if __name__ == "__main__":
    print(f"🦅 DASHBOARD LIVE ON PORT {PORT}")
    # Allow the port to be reused immediately if the server restarts
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
        httpd.serve_forever()
