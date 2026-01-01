from flask import Flask, render_template_string, jsonify
import json
import os

app = Flask(__name__)

# --- PATH CONFIGURATION ---
DATA_DIR = "/app/data"
STATE_FILE = os.path.join(DATA_DIR, "dashboard_state.json")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>LUMA COMMAND</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="3">
    <style>
        body { background-color: #0d1117; color: #c9d1d9; font-family: monospace; padding: 20px; }
        .card { background-color: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 15px; margin-bottom: 20px; }
        .green { color: #2ea043; }
        .red { color: #da3633; }
        .gold { color: #d29922; }
        .cyan { color: #58a6ff; }
        .gray { color: #8b949e; }
        .header { font-size: 1.2em; font-weight: bold; border-bottom: 1px solid #30363d; padding-bottom: 10px; margin-bottom: 10px; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 10px; }
        th, td { text-align: left; padding: 8px; border-bottom: 1px solid #21262d; font-size: 0.9em; }
        .ticker { font-size: 0.85em; color: #8b949e; border: 1px dashed #30363d; padding: 8px; margin-bottom: 20px; background-color: #0d1117; }
        .log { font-size: 0.8em; opacity: 0.9; height: 300px; overflow-y: scroll; border: 1px solid #21262d; padding: 5px; }
        a { color: inherit; text-decoration: none; border-bottom: 1px dotted #8b949e; }
    </style>
</head>
<body>
    <div class="card">
        <div class="header">🦅 LUMA GUARDIAN [MEME FLEET]</div>
        <div id="status" style="font-size: 0.9em; margin-bottom: 10px;">CONNECTING...</div>
        <div style="display: flex; justify-content: space-between;">
            <div>EQUITY: <span id="equity" class="green">---</span></div>
            <div>PNL: <span id="pnl">---</span></div>
        </div>
        <div style="margin-top: 5px; text-align: right; color: #8b949e; font-size: 0.8em;">
            MODE: <span id="mode">---</span> | WIN RATE: <span id="winrate">---</span>
        </div>
    </div>

    <div class="card">
        <div class="header">⚡ ACTIVE POSITIONS</div>
        <table id="pos-table">
            <thead>
                <tr><th>COIN</th><th>SIDE</th><th>PNL</th><th>ROE</th><th>CONF</th></tr>
            </thead>
            <tbody></tbody>
        </table>
    </div>

    <div class="card">
        <div class="header">🤖 SYSTEM ACTIVITY</div>
        <div style="margin-bottom: 10px; font-size: 0.9em;">
            >> <span id="activity" class="cyan">Scanning...</span>
        </div>
        <div id="ticker-log" class="ticker">Waiting...</div>

        <div class="header">📜 PERFORMANCE LOG</div>
        <div id="closed-log" class="log">Waiting for closed trades...</div>
    </div>

    <script>
        fetch('/data').then(r => r.json()).then(data => {
            if (!data || data.status === "BOOTING...") return;
            document.getElementById('status').innerText = data.status;
            document.getElementById('equity').innerText = "$" + data.equity;
            document.getElementById('mode').innerText = data.mode;
            document.getElementById('winrate').innerText = data.win_rate;
            document.getElementById('activity').innerText = data.live_activity;

            let pnlVal = parseFloat(data.pnl);
            let pnlEl = document.getElementById('pnl');
            pnlEl.innerText = (pnlVal > 0 ? "+" : "") + data.pnl;
            pnlEl.className = pnlVal >= 0 ? "green" : "red";

            let tbody = document.querySelector("#pos-table tbody");
            tbody.innerHTML = "";
            if (data.positions && data.positions !== "NO_TRADES") {
                data.positions.split("::").forEach(row => {
                    let p = row.split("|"); // 0:coin, 1:side, 2:pnl, 3:roe, 4:icon, 5:target, 6:logic%
                    let color = parseFloat(p[2]) >= 0 ? "green" : "red";
                    let conf = parseInt(p[6] || 0);
                    let confClass = conf > 75 ? "green" : (conf > 40 ? "gold" : "gray");
                    
                    let tr = document.createElement("tr");
                    tr.innerHTML = `
                        <td>${p[4]} ${p[0]}</td>
                        <td>${p[1]}</td>
                        <td class="${color}">$${p[2]}</td>
                        <td class="${color}">${p[3]}%</td>
                        <td class="${confClass}">${conf}%</td>
                    `;
                    tbody.appendChild(tr);
                });
            } else {
                tbody.innerHTML = "<tr><td colspan='5' style='text-align:center;'>NO ACTIVE TRADES</td></tr>";
            }

            if (data.trade_history) {
                let logs = data.trade_history.split("||").reverse();
                document.getElementById('ticker-log').innerHTML = logs.slice(0, 3).join("<br>");
                let closed = logs.filter(l => ["PROFIT","LOSS","SECURED","STOP","WIN"].some(k => l.toUpperCase().includes(k)));
                document.getElementById('closed-log').innerHTML = closed.length ? closed.join("<br>") : "NO TRADES";
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index(): return render_template_string(HTML_TEMPLATE)

@app.route('/data')
def data():
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as f: return jsonify(json.load(f))
        return jsonify({"status": "BOOTING..."})
    except: return jsonify({"status": "ERROR"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
