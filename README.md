# 🦅 LUMA GUARDIAN [CLOUD NATIVE]

> **System Status:** ONLINE  
> **Infrastructure:** Railway Cloud (High Frequency)  
> **Exchange:** Hyperliquid DEX  
> **Version:** 2.4 (Cloud Commander Edition)

## 📡 System Overview
Luma Guardian is an autonomous, algorithmic trading system designed for high-frequency execution on the Hyperliquid Decentralized Exchange. It creates a "Cloud Singularity," running 24/7 on server-grade infrastructure with persistent state management and real-time "Hologram" telemetry.

The system utilizes a modular "Organ" architecture, where independent Python modules (Organs) handle specific cognitive tasks (Vision, Execution, Risk, Analysis) to drive a central decision loop.

---

## 🖥️ Mission Control (The Dashboard)
The system broadcasts a live, low-latency web interface known as the **Hologram**.
* **The Vault:** Real-time tracking of Equity, PnL, and 30-Day Projections.
* **The Radar:** Background scanning of the entire fleet, showing market regimes even for assets not currently traded.
* **Active Ops:** Live management of open positions with calculated "Ratchet" locks.

**Access:** [Your Railway Domain URL]

---

## ⚙️ Architecture & Modules

### 🧠 The Core
* **`main.py`**: The Central Nervous System. Runs the infinite decision loop (3s tick), integrates all modules, and manages the "Fleet Config."
* **`config.py`**: Secure configuration loader. Handles environment variables and file paths for the Cloud Volume.
* **`start.sh`**: The Bootloader. Launches both the Trading Engine (`main.py`) and the Web Dashboard (`dashboard_server.py`) simultaneously.

### 👁️ Perception (Input)
* **`vision.py`**: Optical Interface. Fetches market data (candles) and account state (balances) from Hyperliquid.
* **`historian.py`**: Long-term memory. Analyzes daily trends (BTC Regime) to set the global risk multiplier.
* **`chronos.py`**: Time perception. Identifies trading sessions (NY, London, Asia) to adjust aggression.

### ⚔️ Execution (Output)
* **`hands.py`**: The Executor. Formats and signs orders (Limit/Market) and sends them to the exchange via API.
* **`messenger.py`**: Communications Officer. Sends Rich Embeds (Financial Reports, Trade Alerts) to Discord.
* **`dashboard_server.py`**: The Face. A Flask web server that renders the `dashboard_state.json` file into the visual HTML interface.

### 🧠 Intelligence (Strategy)
* **`xenomorph.py`**: Momentum Hunter. Detects aggressive breakouts and volatility expansion.
* **`predator.py`**: Divergence Scanner. Looks for RSI/Price divergences to predict reversals.
* **`smart_money.py`**: Whale Tracker. Identifies institutional "Traps" and liquidity sweeps.
* **`oracle.py`**: The Judge. A final confirmation layer that validates signals against higher timeframes.
* **`seasonality.py`**: Time Wizard. Applies multipliers based on time-of-day statistical probability.

### 🛡️ Defense (Risk)
* **`deep_sea.py`**: The Shield & Ratchet. Manages Stop Losses (Shield) and Trailing Profits (Ratchet). Saves state to the persistent volume.
* **`medic.py`**: Health check system (embedded in loop) to prevent crashes.

---

## 🚀 Deployment Guide (Railway)

### 1. Environment Variables
The following keys must be set in the Railway "Variables" tab:
* `WALLET_ADDRESS`: (Your Public Arbitrum Address)
* `PRIVATE_KEY`: (Your Private Key - **CONFIDENTIAL**)
* `DISCORD_TRADES`: (Webhook URL for Trade Alerts)
* `DISCORD_INFO`: (Webhook URL for System Status)
* `DISCORD_ERRORS`: (Webhook URL for Crash Logs)
* `DISCORD_CFO`: (Webhook URL for Financial Reports)

### 2. Persistent Storage (The Brain)
To prevent "Amnesia" on restarts, a Volume must be mounted:
* **Mount Path:** `/app/data`
* *This stores `ratchet_state.json`, `equity_anchor.json`, and `dashboard_state.json`.*

### 3. Start Command
In Railway Settings -> Deploy -> Custom Start Command:
```bash
bash start.sh
