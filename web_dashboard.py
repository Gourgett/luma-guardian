from flask import Flask, render_template_string, jsonify
import json
import os
import re

app = Flask(__name__)

# --- PAGE 1: COMMAND CENTER (With Leverage Column) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>LUMA COMMAND</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="2"> 
    <style>
        body { background-color: #0d1117; color: #c9d1d9; font-family: monospace; padding: 20px; }
        .card { background-color: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 15px; margin-bottom: 20px; }
        .green { color: #2ea043; } .red { color: #da3633; } .gold { color: #d29922; } .cyan { color: #58a6ff; }
        .header { font-size: 1.2em; font-weight: bold; border-bottom: 1px solid #30363d; padding-bottom: 10px; margin-bottom: 10px; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 10px; }
        th, td { text-align: left; padding: 8px; border-bottom: 1px solid #21262d; font-size: 0.9em; }
        .btn { background: #238636; color: white; padding: 5px 10px; text-decoration: none; border-radius: 4px; font-size: 0.8em; }
        .btn:hover { background: #2ea043; }
        
        .ticker { font-size: 0.9em; color: #8b949e; border: 1px dashed #30363d; padding: 8px; background-color: #0d1117; min-height: 120px; }
        a { color: inherit; text-decoration: none; border-bottom: 1px dotted #8b949e; }
    </style>
</head>
<body>
    <div class="card">
        <div class="header" style="display:flex; justify-content:space-between;">
            <span>🦅 LUMA GUARDIAN [V3.3 LIVE]</span>
            <a href="/history" target="_blank" class="btn">📜 PERFORMANCE VAULT</a>
        </div>
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
            <thead>
                <tr> <th>COIN</th> <th>SIDE</th> <th>LEV</th> <th>PNL</th> <th>ROE</th> <th>CONF%</th> </tr>
            </thead>
            <tbody></tbody>
        </table>
        <div id="risk-report" style="font-size: 0.8em; color: #8b949e;"></div>
    </div>

    <div class="card">
        <div class="header">🤖 SYSTEM ACTIVITY (LIVE)</div>
        <div style="margin-bottom: 10px;"> >> <span id="activity" class="cyan">Initializing...</span> </div>
        <div id="ticker-log" class="ticker"> Waiting for updates... </div>
    </div>

    <script>
        function updateDashboard() {
            fetch('/data').then(r => r.json()).then(data => {
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
                document.getElementById('activity').innerText = data.live_activity || "Idle";

                let tbody = document.querySelector("#pos-table tbody");
                tbody.innerHTML = "";
                
                if (data.positions && data.positions !== "NO_TRADES") {
                    let rows = data.positions.split("::");
                    rows.forEach(row => {
                        let parts = row.split("|");
                        if (parts.length >= 4) {
                            let tr = document.createElement("tr");
                            let color = parseFloat(parts[2]) >= 0 ? "green" : "red";
                            let icon = parts[4] || ""; 
                            let link = `<a href="https://app.hyperliquid.xyz/trade/${parts[0]}" target="_blank">${icon} ${parts[0]}</a>`;
                            let score = parts[6] || "---"; 
                            let lev = parts[7] || "---"; // Catch the new Leverage item
                            
                            tr.innerHTML = `<td>${link}</td><td>${parts[1]}</td><td style='color:#8b949e'>${lev}</td><td class="${color}">$${parts[2]}</td><td class="${color}">${parts[3]}%</td><td class="gold">${score}</td>`;
                            tbody.appendChild(tr);
                        }
                    });
                } else { tbody.innerHTML = "<tr><td colspan='6' style='text-align:center; color:#555;'>NO ACTIVE TRADES</td></tr>"; }

                if (data.risk_report) document.getElementById('risk-report').innerText = data.risk_report.replace(/::/g, " | ");

                if (data.trade_history) {
                    let allLogs = data.trade_history.split("||").reverse();
                    let tickerDiv = document.getElementById('ticker-log');
                    tickerDiv.innerHTML = allLogs.slice(0, 6).join("<br>");
                }
            }).catch(err => { document.getElementById('status').innerText = "VISUAL CONNECTION LOST"; });
        }
        updateDashboard();
        setInterval(updateDashboard, 2000);
    </script>
</body>
</html>
"""

# --- PAGE 2: THE VAULT (Smart PnL Coloring) ---
HISTORY_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>LUMA PERFORMANCE</title>
    <style>
        body { background-color: #0d1117; color: #c9d1d9; font-family: monospace; padding: 20px; }
        .log-entry { border-bottom: 1px solid #30363d; padding: 10px; font-size: 1.0em; display: flex; align-items: center;}
        .green { color: #2ea043; border-left: 4px solid #2ea043; background: #0f1e13; } 
        .red { color: #da3633; border-left: 4px solid #da3633; background: #241010; }
        h1 { border-bottom: 2px solid #30363d; padding-bottom: 10px; margin-bottom: 20px; }
        .btn { background: #1f6feb; color: white; padding: 5px 15px; text-decoration: none; border-radius: 4px; font-size: 0.8em; }
    </style>
</head>
<body>
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <h1>📜 CLOSED TRADES (RESULTS ONLY)</h1>
        <a href="/" class="btn">BACK TO COMMAND</a>
    </div>
    
    <div style="margin-bottom: 20px; color: #8b949e; font-size: 0.9em;">
        Filtering for: PROFIT, LOSS, SECURED, STOP, CUT. (Open orders hidden).
    </div>

    <div id="content">
        {{ content | safe }}
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/history')
def history():
    try:
        archive_path = "/app/data/luma_archive.txt"
        if os.path.exists(archive_path):
            with open(archive_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            formatted = []
            for line in reversed(lines):
                u = line.upper()
                
                # --- STRICT FILTER ---
                if any(x in u for x in ["PROFIT", "LOSS", "SECURED", "WIN", "LOSE", "STOP", "CUT"]):
                    
                    # --- SMART COLOR LOGIC ---
                    color = "green" 
                    try:
                        match = re.search(r'\(([+-]?\d*\.?\d+)\s*\|', line)
                        if match:
                            pnl_str = match.group(1)
                            if pnl_str.startswith('-'): color = "red"
                        else:
                            if any(x in u for x in ["LOSS", "LOSE", "CUT", "STOP"]): color = "red"
                    except:
                         if any(x in u for x in ["LOSS", "LOSE", "CUT", "STOP"]): color = "red"
                    
                    formatted.append(f"<div class='log-entry {color}'>{line.strip()}</div>")
            
            if not formatted:
                return render_template_string(HISTORY_TEMPLATE, content="<div style='padding:20px; color:#8b949e;'>NO CLOSED TRADES FOUND YET.</div>")

            return render_template_string(HISTORY_TEMPLATE, content="".join(formatted))
        else:
            return render_template_string(HISTORY_TEMPLATE, content="<div style='padding:20px; color:#8b949e;'>NO ARCHIVE DATA FOUND YET.</div>")
    except Exception as e:
        return f"ERROR LOADING ARCHIVE: {e}"

@app.route('/data')
def data():
    try:
        with open("dashboard_state.json", "r") as f:
            return jsonify(json.load(f))
    except:
        return jsonify({"status": "RESTORING VISUALS...", "equity": "0.00", "cash": "0.00", "pnl": "0.00"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
