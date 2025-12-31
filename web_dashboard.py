from flask import Flask, render_template_string, jsonify
import json
import os
import time

app = Flask(__name__)

# HTML TEMPLATE
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
        .green { color: #2ea043; }
        .red { color: #da3633; }
        .gold { color: #d29922; }
        .cyan { color: #58a6ff; }
        .header { font-size: 1.2em; font-weight: bold; border-bottom: 1px solid #30363d; padding-bottom: 10px; margin-bottom: 10px; }
        
        table { width: 100%; border-collapse: collapse; margin-bottom: 10px; }
        th, td { text-align: left; padding: 8px; border-bottom: 1px solid #21262d; }
        
        /* LOG WINDOWS */
        .ticker { 
            font-size: 0.9em; 
            color: #8b949e; 
            border: 1px dashed #30363d; 
            padding: 8px; 
            margin-bottom: 20px; 
            background-color: #0d1117;
        }
        
        .log { 
            font-size: 0.8em; 
            opacity: 0.9; 
            height: 350px; 
            overflow-y: scroll; 
            border: 1px solid #21262d; 
            padding: 5px; 
        }
        
        a { color: inherit; text-decoration: none; border-bottom: 1px dotted #8b949e; }
        a:hover { color: #58a6ff; border-bottom: 1px solid #58a6ff; }
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
        <div class="header">🤖 SYSTEM ACTIVITY</div>
        <div class="ticker">
            <span id="activity" class="cyan">Initializing...</span>
        </div>

        <div class="header">📜 MARKET LOGS (LAST 60)</div>
        <div id="logs" class="log">
             <div style="padding:10px; text-align:center;">Waiting for trades...</div>
        </div>
    </div>

    <script>
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
            
            // --- ACTIVITY FIX ---
            // Your main.py sends "live_activity" as a simple string. 
            // We display it directly. No parsing needed.
            document.getElementById('activity').innerText = data.live_activity || "Idle";

            // --- POSITIONS TABLE ---
            let tbody = document.querySelector("#pos-table tbody");
            tbody.innerHTML = "";
            if (data.positions && data.positions !== "NO_TRADES") {
                let rows = data.positions.split("::");
                rows.forEach(row => {
                    let parts = row.split("|"); 
                    let coinName = parts[0];
                    let tr = document.createElement("tr");
                    let color = parseFloat(parts[2]) >= 0 ? "green" : "red";
                    let link = `<a href="https://app.hyperliquid.xyz/trade/${coinName}" target="_blank">${parts[4]} ${coinName}</a>`;
                    tr.innerHTML = `<td>${link}</td><td>${parts[1]}</td><td class="${color}">$${parts[2]}</td><td class="${color}">${parts[3]}%</td>`;
                    tbody.appendChild(tr);
                });
            } else {
                tbody.innerHTML = "<tr><td colspan='4' style='text-align:center; color:#555;'>NO ACTIVE TRADES</td></tr>";
            }
            
            if (data.risk_report) {
                document.getElementById('risk-report').innerText = data.risk_report.replace(/::/g, " | ");
            }

            // --- TRADE HISTORY ---
            // Your main.py sends "trade_history" joined by "||". 
            // We split it to show the list.
            let logDiv = document.getElementById('logs');
            if (data.trade_history) {
                logDiv.innerHTML = data.trade_history.split("||").reverse().join("<br>");
            }
        });
    </script>
</body>
</html>
