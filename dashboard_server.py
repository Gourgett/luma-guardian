from flask import Flask, jsonify, render_template_string
import json
import os
import time
from config import conf

app = Flask(__name__)

# TIER: MISSION CONTROL (SINGLE PANE GRID)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>LUMA :: COMMAND</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="5">
    <style>
        body { background-color: #0b0e11; color: #c9d1d9; font-family: 'Consolas', 'Monaco', monospace; margin: 0; padding: 10px; }
        .grid-container { display: grid; gap: 15px; grid-template-columns: 1fr; }
        
        /* CARDS */
        .card { background: #161b22; border: 1px solid #30363d; border-radius: 6px; overflow: hidden; }
        .card-header { background: #0d1117; padding: 8px 12px; border-bottom: 1px solid #30363d; font-size: 0.85em; font-weight: bold; color: #8b949e; letter-spacing: 1px; display: flex; justify-content: space-between; }
        
        /* SECTION A: VAULT (FINANCE) */
        .vault-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1px; background: #30363d; }
        .vault-box { background: #161b22; padding: 15px 10px; text-align: center; }
        .vault-label { display: block; font-size: 0.7em; color: #8b949e; margin-bottom: 5px; }
        .vault-value { font-size: 1.1em; font-weight: bold; }
        .green { color: #3fb950; }
        .red { color: #f85149; }
        .gold { color: #e3b341; }
        
        /* SECTION B & C: TABLES */
        .table-container { padding: 0; }
        table { width: 100%; border-collapse: collapse; font-size: 0.9em; }
        th { text-align: left; padding: 8px 12px; color: #484f58; border-bottom: 1px solid #21262d; font-size: 0.8em; }
        td { padding: 8px 12px; border-bottom: 1px solid #21262d; }
        tr:last-child td { border-bottom: none; }
        
        /* RADAR SPECIFIC */
        .radar-status-active { color: #58a6ff; font-size: 0.8em; }
        .radar-status-scan { color: #8b949e; font-size: 0.8em; }
        .radar-status-attack { color: #e3b341; font-weight: bold; font-size: 0.8em; }
        
        /* UTILS */
        .status-dot { height: 8px; width: 8px; background-color: #3fb950; border-radius: 50%; display: inline-block; margin-right: 5px; animation: pulse 2s infinite; }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }
        .footer { text-align: center; font-size: 0.75em; color: #484f58; margin-top: 20px; }

        @media (min-width: 768px) {
            .grid-container { grid-template-columns: 1fr 1fr; }
            .full-width { grid-column: span 2; }
        }
    </style>
</head>
<body>
    <div class="grid-container">
        
        <div class="card full-width">
            <div class="card-header">
                <span><span class="status-dot"></span>LUMA SYSTEM ONLINE</span>
                <span id="mode" style="color: #e3b341;">---</span>
            </div>
            <div class="vault-grid">
                <div class="vault-box">
                    <span class="vault-label">TOTAL EQUITY</span>
                    <span class="vault-value" id="equity">---</span>
                </div>
                <div class="vault-box">
                    <span class="vault-label">SESSION PNL</span>
                    <span class="vault-value" id="pnl">---</span>
                </div>
                <div class="vault-box">
                    <span class="vault-label">30D PROJECTION</span>
                    <span class="vault-value" id="proj">---</span>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-header">ACTIVE OPERATIONS</div>
            <div class="table-container">
                <table id="ops-table">
                    <thead><tr><th>ASSET</th><th>SIDE</th><th>PNL</th></tr></thead>
                    <tbody id="ops-body">
                        <tr><td colspan="3" style="text-align: center; color: #484f58; padding: 20px;">NO ACTIVE CONTRACTS</td></tr>
                    </tbody>
                </table>
            </div>
        </div>

        <div class="card">
            <div class="card-header">FLEET RADAR</div>
            <div class="table-container">
                <table id="radar-table">
                    <thead><tr><th>ASSET</th><th>PRICE</th><th>STATUS</th></tr></thead>
                    <tbody id="radar-body">
                        <tr><td colspan="3" style="text-align: center; color: #484f58; padding: 20px;">INITIALIZING SCAN...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="card full-width">
            <div class="card-header">SYSTEM LOG</div>
            <div id="logs" style="padding: 10px; font-size: 0.8em; color: #8b949e; line-height: 1.5; font-family: monospace;">
                waiting for events...
            </div>
        </div>

    </div>
    <div class="footer">
        LUMA CLOUD NATIVE • UPDATED: <span id="timestamp">--:--:--</span>
    </div>

    <script>
        function update() {
            fetch('/data')
                .then(response => response.json())
                .then(data => {
                    // 1. UPDATE VAULT
                    document.getElementById('equity').innerText = '$' + data.equity;
                    const pnl = parseFloat(data.pnl);
                    const pnlEl = document.getElementById('pnl');
                    pnlEl.innerText = (pnl >= 0 ? '+' : '') + '$' + data.pnl;
                    pnlEl.className = 'vault-value ' + (pnl >= 0 ? 'green' : 'red');

                    // 2. UPDATE PROJECTION
                    const proj = parseFloat(data.proj || 0);
                    const projEl = document.getElementById('proj');
                    projEl.innerText = (proj >= 0 ? '+' : '') + '$' + parseFloat(data.proj).toFixed(2);
                    projEl.className = 'vault-value ' + (proj >= 0 ? 'green' : 'red');

                    document.getElementById('mode').innerText = data.mode;
                    document.getElementById('timestamp').innerText = new Date(data.updated * 1000).toLocaleTimeString();
                    
                    // 3. UPDATE ACTIVE OPS
                    const opsBody = document.getElementById('ops-body');
                    if (data.positions && data.positions !== "NO_TRADES") {
                        let html = '';
                        data.positions.split('::').forEach(row => {
                            const [coin, side, pnl, roe, icon] = row.split('|');
                            const color = parseFloat(pnl) >= 0 ? '#3fb950' : '#f85149';
                            html += `<tr>
                                <td>${icon} <b>${coin}</b></td>
                                <td style="color:${side==='LONG'?'#58a6ff':'#f85149'}">${side}</td>
                                <td style="color:${color}">$${pnl} <span style="font-size:0.8em">(${roe}%)</span></td>
                            </tr>`;
                        });
                        opsBody.innerHTML = html;
                    } else {
                        opsBody.innerHTML = '<tr><td colspan="3" style="text-align: center; color: #484f58; padding: 20px;">NO ACTIVE CONTRACTS</td></tr>';
                    }

                    // 4. UPDATE RADAR
                    const radarBody = document.getElementById('radar-body');
                    if (data.radar) {
                        let rHtml = '';
                        data.radar.split('::').forEach(row => {
                            const [coin, price, status, color] = row.split('|');
                            let statusClass = 'radar-status-scan';
                            if(color === 'blue') statusClass = 'radar-status-active';
                            if(color === 'orange') statusClass = 'radar-status-attack';
                            
                            rHtml += `<tr>
                                <td><b>${coin}</b></td>
                                <td>${price}</td>
                                <td class="${statusClass}">${status}</td>
                            </tr>`;
                        });
                        radarBody.innerHTML = rHtml;
                    }

                    // 5. LOGS
                    if(data.events) {
                        document.getElementById('logs').innerHTML = data.events.split('||').reverse().join('<br>');
                    }
                });
        }
        update();
        setInterval(update, 2000); // Fast refresh for radar
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
        file_path = conf.get_path("dashboard_state.json")
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return jsonify(json.load(f))
    except: pass
    return jsonify({"equity": "---", "pnl": "0.00", "proj": "0.00", "mode": "BOOTING", "events": "", "positions": "NO_TRADES", "radar": "", "updated": time.time()})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
