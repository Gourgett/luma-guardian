from flask import Flask, jsonify, make_response
import json
import os
import time
from config import conf

app = Flask(__name__)

# TIER: MISSION CONTROL V4 (WITH WATCHDOG)
# Uses "Raw Mode" HTML to prevent syntax crashes
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>LUMA :: COMMAND</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="5">
    <style>
        body { background-color: #0b0e11; color: #c9d1d9; font-family: monospace; margin: 0; padding: 10px; }
        .grid-container { display: grid; gap: 15px; grid-template-columns: 1fr; }
        .card { background: #161b22; border: 1px solid #30363d; border-radius: 6px; overflow: hidden; }
        .card-header { background: #0d1117; padding: 8px 12px; border-bottom: 1px solid #30363d; font-weight: bold; color: #8b949e; display: flex; justify-content: space-between; }
        
        /* VAULT GRID */
        .vault-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1px; background: #30363d; }
        .vault-box { background: #161b22; padding: 15px 10px; text-align: center; }
        .vault-label { display: block; font-size: 0.7em; color: #8b949e; margin-bottom: 5px; }
        .vault-value { font-size: 1.1em; font-weight: bold; }
        .green { color: #3fb950; }
        .red { color: #f85149; }
        
        /* RISK METER */
        .risk-container { background: #0d1117; padding: 10px; border-top: 1px solid #30363d; }
        .risk-label { font-size: 0.7em; color: #8b949e; margin-bottom: 5px; display: block; }
        .risk-bar-bg { background: #21262d; height: 6px; border-radius: 3px; overflow: hidden; }
        .risk-bar-fill { height: 100%; background: #3fb950; width: 0%; transition: width 0.5s; }
        
        /* TABLES */
        table { width: 100%; border-collapse: collapse; font-size: 0.9em; }
        th { text-align: left; padding: 8px 12px; color: #484f58; border-bottom: 1px solid #21262d; font-size: 0.8em; }
        td { padding: 8px 12px; border-bottom: 1px solid #21262d; }
        
        /* STATUS COLORS */
        .status-active { color: #58a6ff; }
        .status-scan { color: #8b949e; }
        .status-attack { color: #e3b341; font-weight: bold; }
        .status-trap { color: #39c5cf; font-weight: bold; }
        .status-warn { color: #d2a8ff; }
        
        .footer { text-align: center; font-size: 0.75em; color: #484f58; margin-top: 20px; }

        @media (min-width: 768px) {
            .grid-container { grid-template-columns: 1fr 1fr; }
            .full-width { grid-column: span 2; }
            .vault-grid { grid-template-columns: repeat(4, 1fr); } 
        }
    </style>
</head>
<body>
    <div class="grid-container">
        <div class="card full-width">
            <div class="card-header">
                <span>LUMA SYSTEM</span>
                <span style="color:#e3b341"><span id="mode">---</span> | <span id="session" style="color:#58a6ff">---</span></span>
            </div>
            <div class="vault-grid">
                <div class="vault-box"><span class="vault-label">EQUITY</span><span class="vault-value" id="equity">---</span></div>
                <div class="vault-box"><span class="vault-label">BUYING POWER</span><span class="vault-value" id="cash">---</span></div>
                <div class="vault-box"><span class="vault-label">SESSION PNL</span><span class="vault-value" id="pnl">---</span></div>
                <div class="vault-box"><span class="vault-label">30D PROJECTION</span><span class="vault-value" id="proj">---</span></div>
            </div>
            <div class="risk-container">
                <span class="risk-label">RISK LEVEL: <span id="risk-pct">0%</span></span>
                <div class="risk-bar-bg"><div class="risk-bar-fill" id="risk-bar"></div></div>
            </div>
        </div>

        <div class="card">
            <div class="card-header">ACTIVE OPS</div>
            <table>
                <thead><tr><th>ASSET</th><th>SIDE</th><th>PNL</th></tr></thead>
                <tbody id="ops-body"><tr><td colspan="3" style="text-align:center;padding:20px;color:#484f58">NO TRADES</td></tr></tbody>
            </table>
        </div>

        <div class="card">
            <div class="card-header">FLEET RADAR</div>
            <table>
                <thead><tr><th>ASSET</th><th>PRICE</th><th>STATUS</th></tr></thead>
                <tbody id="radar-body"><tr><td colspan="3" style="text-align:center;padding:20px;color:#484f58">SCANNING...</td></tr></tbody>
            </table>
        </div>
        
        <div class="card full-width">
            <div class="card-header">LOGS</div>
            <div id="logs" style="padding:10px;font-size:0.8em;color:#8b949e;font-family:monospace">waiting...</div>
        </div>
    </div>
    <div class="footer">LUMA CLOUD NATIVE • <span id="timestamp">--:--:--</span></div>

    <script>
        function update() {
            fetch('/data').then(r => r.json()).then(d => {
                document.getElementById('equity').innerText = '$' + d.equity;
                document.getElementById('cash').innerText = '$' + d.cash;
                
                const pnlEl = document.getElementById('pnl');
                pnlEl.innerText = (d.pnl >= 0 ? '+' : '') + '$' + d.pnl;
                pnlEl.className = 'vault-value ' + (d.pnl >= 0 ? 'green' : 'red');

                const projEl = document.getElementById('proj');
                projEl.innerText = (d.proj >= 0 ? '+' : '') + '$' + d.proj;
                projEl.className = 'vault-value ' + (d.proj >= 0 ? 'green' : 'red');

                document.getElementById('mode').innerText = d.mode;
                document.getElementById('session').innerText = d.session || "--";
                document.getElementById('timestamp').innerText = new Date(d.updated * 1000).toLocaleTimeString();

                let risk = 0;
                if(parseFloat(d.equity) > 0) risk = ((parseFloat(d.equity) - parseFloat(d.cash)) / parseFloat(d.equity)) * 100;
                document.getElementById('risk-pct').innerText = risk.toFixed(1) + '%';
                const bar = document.getElementById('risk-bar');
                bar.style.width = Math.min(risk, 100) + '%';
                bar.style.backgroundColor = risk < 50 ? '#3fb950' : (risk < 80 ? '#e3b341' : '#f85149');

                const ops = document.getElementById('ops-body');
                if(d.positions && d.positions !== "NO_TRADES") {
                    ops.innerHTML = d.positions.split('::').map(r => {
                        const [c, s, p, roe, i] = r.split('|');
                        const col = parseFloat(p) >= 0 ? '#3fb950' : '#f85149';
                        return `<tr><td>${i} <b>${c}</b></td><td style="color:${s==='LONG'?'#58a6ff':'#f85149'}">${s}</td><td style="color:${col}">$${p}</td></tr>`;
                    }).join('');
                } else ops.innerHTML = '<tr><td colspan="3" style="text-align:center;padding:20px;color:#484f58">NO TRADES</td></tr>';

                const rad = document.getElementById('radar-body');
                if(d.radar) {
                    rad.innerHTML = d.radar.split('::').map(r => {
                        const [c, p, st, col] = r.split('|');
                        let cls = 'status-scan';
                        if(col === 'blue') cls = 'status-active';
                        if(col === 'orange') cls = 'status-attack';
                        if(col === 'cyan') cls = 'status-trap';
                        if(col === 'purple') cls = 'status-warn';
                        return `<tr><td><b>${c}</b></td><td>${p}</td><td class="${cls}">${st}</td></tr>`;
                    }).join('');
                }

                if(d.events) document.getElementById('logs').innerHTML = d.events.split('||').reverse().join('<br>');
            });
        }
        setInterval(update, 2000);
        update();
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    return HTML_TEMPLATE 

@app.route('/data')
def get_data():
    try:
        path = conf.get_path("dashboard_state.json")
        if os.path.exists(path):
            with open(path, 'r') as f: return jsonify(json.load(f))
    except: pass
    return jsonify({"equity": "0.00", "cash": "0.00", "pnl": "0.00", "proj": "0.00", "mode": "BOOTING", "updated": time.time()})

# --- THE WATCHDOG (HEALTHCHECK) ---
@app.route('/health')
def health_check():
    try:
        path = conf.get_path("dashboard_state.json")
        if not os.path.exists(path):
            # Still booting up, don't kill it yet.
            return make_response("BOOTING", 200)
            
        with open(path, 'r') as f:
            data = json.load(f)
            last_update = float(data.get('updated', 0))
            
        # If Brain hasn't written to disk in 60s, it's frozen.
        if time.time() - last_update > 60:
            return make_response("BRAIN_DEAD", 500) # Triggers Restart
            
        return make_response("HEALTHY", 200)
    except:
        return make_response("ERROR", 500)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
