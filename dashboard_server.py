from flask import Flask, jsonify, render_template_string
import json
import os
import time
from config import conf

app = Flask(__name__)

# HTML TEMPLATE (The Visual Interface)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>LUMA :: HOLOGRAM</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="5">
    <style>
        body { background-color: #0d1117; color: #00ff41; font-family: 'Courier New', monospace; margin: 0; padding: 20px; }
        .card { border: 1px solid #30363d; background: #161b22; padding: 15px; margin-bottom: 15px; border-radius: 6px; }
        .header { display: flex; justify-content: space-between; border-bottom: 1px solid #30363d; padding-bottom: 10px; margin-bottom: 10px; }
        .stat-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
        .stat-box { background: #0d1117; padding: 10px; border: 1px solid #30363d; text-align: center; }
        .stat-label { font-size: 0.8em; color: #8b949e; display: block; }
        .stat-value { font-size: 1.2em; font-weight: bold; }
        .pnl-green { color: #3fb950; }
        .pnl-red { color: #f85149; }
        .table { width: 100%; border-collapse: collapse; font-size: 0.9em; }
        .table th { text-align: left; color: #8b949e; border-bottom: 1px solid #30363d; padding: 5px; }
        .table td { padding: 5px; border-bottom: 1px solid #21262d; }
        .status-pulse { animation: pulse 2s infinite; }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
    </style>
</head>
<body>
    <div class="card">
        <div class="header">
            <span class="status-pulse">🦅 LUMA SYSTEM ONLINE</span>
            <span id="timestamp">--:--:--</span>
        </div>
        <div class="stat-grid">
            <div class="stat-box">
                <span class="stat-label">EQUITY</span>
                <span class="stat-value" id="equity">Loading...</span>
            </div>
            <div class="stat-box">
                <span class="stat-label">SESSION PNL</span>
                <span class="stat-value" id="pnl">Loading...</span>
            </div>
        </div>
        <div style="margin-top: 10px; text-align: center; font-size: 0.9em; color: #8b949e;">
            MODE: <span id="mode" style="color: #e3b341;">---</span>
        </div>
    </div>

    <div class="card">
        <div class="header"><span>ACTIVE POSITIONS</span></div>
        <table class="table" id="pos-table">
            <thead><tr><th>COIN</th><th>SIDE</th><th>PNL</th><th>ROE</th></tr></thead>
            <tbody id="pos-body">
                <tr><td colspan="4" style="text-align: center; padding: 20px; color: #8b949e;">SCANNING MARKETS...</td></tr>
            </tbody>
        </table>
    </div>

    <div class="card">
        <div class="header"><span>EVENT LOG</span></div>
        <div id="logs" style="font-size: 0.8em; color: #8b949e; line-height: 1.4;">
            No events logged yet.
        </div>
    </div>

    <script>
        function update() {
            fetch('/data')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('equity').innerText = '$' + data.equity;
                    
                    const pnlEl = document.getElementById('pnl');
                    pnlEl.innerText = (parseFloat(data.pnl) >= 0 ? '+' : '') + '$' + data.pnl;
                    pnlEl.className = 'stat-value ' + (parseFloat(data.pnl) >= 0 ? 'pnl-green' : 'pnl-red');
                    
                    document.getElementById('mode').innerText = data.mode;
                    document.getElementById('timestamp').innerText = new Date(data.updated * 1000).toLocaleTimeString();
                    
                    // Logs
                    if(data.events) {
                        document.getElementById('logs').innerHTML = data.events.split('||').reverse().join('<br>');
                    }

                    // Positions
                    const tbody = document.getElementById('pos-body');
                    if (data.positions && data.positions !== "NO_TRADES") {
                        let html = '';
                        data.positions.split('::').forEach(row => {
                            const [coin, side, pnl, roe, icon, target] = row.split('|');
                            const color = parseFloat(pnl) >= 0 ? '#3fb950' : '#f85149';
                            html += `<tr>
                                <td>${icon} <b>${coin}</b></td>
                                <td style="color:${side==='LONG'?'#58a6ff':'#f85149'}">${side}</td>
                                <td style="color:${color}">$${pnl}</td>
                                <td style="color:${color}">${roe}%</td>
                            </tr>`;
                        });
                        tbody.innerHTML = html;
                    } else {
                        tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; padding: 20px; color: #8b949e;">NO ACTIVE TRADES</td></tr>';
                    }
                });
        }
        update();
        setInterval(update, 3000);
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    return render_template_string(HTML_TEMPLATE)

@app.route('/data')
def get_data():
    try:
        # Read from the PERSISTENT VOLUME
        file_path = conf.get_path("dashboard_state.json")
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return jsonify(json.load(f))
    except: pass
    return jsonify({"equity": "---", "pnl": "0.00", "mode": "BOOTING", "events": "", "positions": "NO_TRADES", "updated": time.time()})

if __name__ == "__main__":
    # Run on port 8080 (Railway Default)
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
