import http.server
import socketserver
import os
import json

# Railway automatically provides the PORT. Defaults to 8080.
PORT = int(os.environ.get("PORT", 8080))

# We look for the file in the current directory or 'data' folder
# This matches where main.py writes it.
DATA_FILES = ["dashboard_state.json", "data/dashboard_state.json"]

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/data":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            content = b'{"status": "WAITING FOR BOT...", "equity": "---"}'
            
            # Try to find the file without crashing
            for path in DATA_FILES:
                if os.path.exists(path):
                    try:
                        with open(path, "rb") as f:
                            content = f.read()
                        break
                    except: pass
            
            self.wfile.write(content)
        else:
            # Serve index.html if it exists, otherwise just say "Online"
            if os.path.exists("index.html"):
                super().do_GET()
            else:
                self.send_response(200)
                self.wfile.write(b"🦅 LUMA DASHBOARD: ONLINE")

if __name__ == "__main__":
    print(f"🦅 DASHBOARD STANDALONE LISTENING ON {PORT}")
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
            httpd.serve_forever()
    except Exception as e:
        print(f"xx SERVER CRASH: {e}")
