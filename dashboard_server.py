import http.server
import socketserver
import os
import json
from config import conf

# The original simple server
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
                self.wfile.write(json.dumps({"status": "LOADING..."}).encode())
        else:
            super().do_GET()

if __name__ == "__main__":
    print(f"🦅 DASHBOARD SERVING ON {PORT}")
    httpd = socketserver.TCPServer(("", PORT), DashboardHandler)
    httpd.serve_forever()
