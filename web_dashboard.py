from flask import Flask, render_template_string, jsonify
import json
import os

app = Flask(__name__)

# HTML TEMPLATE
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>LUMA COMMAND</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="5">
    <style>
        body { background-color: #0d1117; color: #c9d1d9; font-family: monospace; padding: 20px; }
        .card { background-color: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 15px; margin-bottom: 20px; }
        .green { color: #2ea043; }
        .red { color: #da3633; }
        .gold { color: #d29922; }
        .header { font-size: 1.2em; font-weight: bold; border-bottom: 1px solid #30363d; padding-bottom: 10px; margin-bottom: 10px; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 10px; }
        th, td { text-align: left; padding: 8px; border-bottom: 1px solid #21262d; }
        .log { font-size: 0.8em; opacity: 0.8; height: 400px; overflow-y: scroll; border: 1px solid #21262d; padding: 5px; }
    </style>
</head>
<body>
    <div class="card">
        <div class="header">🦅 LUMA GUARDIAN [MEME FLEET]</div>
        <div id="status" style="font-size: 0.9em; margin-bottom: 10px;">CONNECTING...</div>
        
        <div style="margin-top: 10px; display: flex; justify-content: space-between;">
            <div>EQUITY: <span id="equity" class="green">---</span></div>
            <div>CASH: <span id="cash">---</span></div>
        </div>
        
        <div style="margin-top: 5px; display: flex; justify-content: space-between;">
            <div>PNL: <span id="pnl">---</span></div>
            <div>WIN RATE: <span id="winrate" class="gold">---</span></div>
        </div>
        
        <div style="margin-top: 5px; text-align: right; color: #8b949e; font-size: 0.9em;">
            MODE: <span id="mode" style="color:#c9d1d9;">---</span> | SESSION: <span id="session">---</span>
        </div>
    </div>

    <div class="card">
        <div class="header">⚡ ACTIVE POSITIONS</div>
        <table id="pos-table">
            <thead><tr><th>COIN</th><th>SIDE</th><th>PNL</th><th>ROE</th></tr></thead>
            <tbody></tbody>
        </table>
        <div id="risk-report" style="font-size: 0.8em; color: #8b949e;"></div>
    </div>

    <div class="card">
        <div class="header">📜 MARKET LOGS (LAST 60)</div>
        <div id="logs" class="log">
             <div style="padding:10px; text-align:center;">Loading logs...</div>
        </div>
    </div>

    <script>
        fetch('/data').then(r => r.json()).then(data => {
            // Header Data
            document.getElementById('status').innerText = data.status || "ONLINE";
            document.getElementById('equity').innerText = "$" + data.equity;
            document.getElementById('cash').innerText = "$" + data.cash;
            
            let pnl = parseFloat(data.pnl);
            let pnlEl = document.getElementById('pnl');
            pnlEl.innerText = (pnl > 0 ? "+" : "") + data.pnl;
            pnlEl.className = pnl >= 0 ? "green" : "red";

            document.getElementById('winrate').innerText = data.win_rate || "0/0 (0%)";
            document.getElementById('mode').innerText = data.mode;
            document.getElementById('session').innerText = data.session || "WAITING";

            // Live Positions Table
            let tbody = document.querySelector("#pos-table tbody");
            tbody.innerHTML = "";
            if (data.positions && data.positions !== "NO_TRADES") {
                let rows = data.positions.split("::");
                rows.forEach(row => {
                    let parts = row.split("|"); // coin|side|pnl|roe|icon|target
                    let tr = document.createElement("tr");
                    let color = parseFloat(parts[2]) >= 0 ? "green" : "red";
                    tr.innerHTML = `<td>${parts[4]} ${parts[0]}</td><td>${parts[1]}</td><td class="${color}">$${parts[2]}</td><td class="${color}">${parts[3]}%</td>`;
                    tbody.appendChild(tr);
                });
            } else {
                tbody.innerHTML = "<tr><td colspan='4' style='text-align:center; color:#555;'>NO ACTIVE TRADES</td></tr>";
            }
            
            // Risk Report Text
            if (data.risk_report) {
                document.getElementById('risk-report').innerText = data.risk_report.replace(/::/g, " | ");
            }

            // Logs (Reversed so newest is at top)
            let logDiv = document.getElementById('logs');
            if (data.events) {
                // events are joined by "||"
                logDiv.innerHTML = data.events.split("||").reverse().join("<br>");
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/data')
def data():
    try:
        with open("dashboard_state.json", "r") as f:
            return jsonify(json.load(f))
    except:
        return jsonify({"status": "BOOTING...", "equity": "0.00", "cash": "0.00", "pnl": "0.00"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
