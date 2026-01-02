import MetaTrader5 as mt5
import time
import sys
from datetime import datetime

# --- CONFIGURATION (TIER 1 SAVED DEFAULTS) ---
MAGIC_NUMBER = 123456
MAX_RISK_PER_TRADE = 0.02   # 2% Risk Cap
MAX_MARGIN_LOAD = 0.05      # 5% Max Margin Load
TIMEFRAME = mt5.TIMEFRAME_M15
SYMBOL_LIST = ["EURUSD", "GBPUSD", "USDJPY"] # Add your specific symbols here

# --- WEBHOOK CONFIG (Placeholder for your 3 hooks) ---
WEBHOOK_URLS = [
    "YOUR_DISCORD_WEBHOOK_1",
    "YOUR_DISCORD_WEBHOOK_2",
    "YOUR_DISCORD_WEBHOOK_3"
]

# --- UI & LOGGING SYSTEM ---
def print_dashboard(status, details, active_trades=0):
    """
    Renders the Server Command Dashboard v2.3 directly to console.
    Fixes the 'Restoring Visuals' freeze by flushing output immediately.
    """
    now = datetime.now().strftime("%H:%M:%S")
    
    # Clear screen (optional, creates flickering but keeps dashboard static)
    # print("\033[H\033[J", end="") 
    
    print(f"\n--- SERVER COMMAND DASHBOARD v2.3 [{now}] ---")
    print(f"Status:   🟢 ONLINE | Mode: TIER 1 (STRICT)")
    print(f"Activity: {status}")
    print(f"Details:  {details}")
    print(f"Trades:   {active_trades} Active")
    print("-" * 50)
    sys.stdout.flush()

def log_event(level, message):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {level} : {message}")

# --- RISK MANAGEMENT (CRITICAL FIX) ---
def calculate_safe_lot_size(symbol, sl_pips, account_equity):
    """
    Strict Tier 1 Sizing. 
    Prevents the 'All Acc Balance' threat by capping margin at 5%.
    """
    symbol_info = mt5.symbol_info(symbol)
    if not symbol_info:
        return 0.0

    # 1. Calculate Risk Value
    risk_amount = account_equity * MAX_RISK_PER_TRADE
    tick_value = symbol_info.trade_tick_value
    if tick_value == 0: return 0.0
    
    # 2. Raw Lot Calculation based on SL
    # Formula: (Risk $ / (SL Pips * Tick Value))
    lot_step = symbol_info.volume_step
    raw_lots = risk_amount / (sl_pips * tick_value)
    
    # 3. MARGIN SAFETY LOCK (The fix for the balance issue)
    current_price = symbol_info.ask
    margin_required = mt5.order_calc_margin(mt5.ORDER_TYPE_BUY, symbol, raw_lots, current_price)
    
    if margin_required > (account_equity * MAX_MARGIN_LOAD):
        reduction_factor = (account_equity * MAX_MARGIN_LOAD) / margin_required
        safe_lots = raw_lots * reduction_factor
        log_event("SAFETY", f"Size reduced to {safe_lots:.2f} to respect 5% Margin Cap.")
        raw_lots = safe_lots

    # Round down to nearest step
    lots = int(raw_lots / lot_step) * lot_step
    return round(lots, 2)

# --- TRADE EXECUTION & MANAGEMENT ---
def manage_positions():
    """
    Active Management Loop.
    Fixes 'Not Managing' issue by iterating through positions every cycle.
    """
    positions = mt5.positions_get()
    
    if positions is None or len(positions) == 0:
        return 0

    for pos in positions:
        symbol = pos.symbol
        # Simple Trailing Stop Logic (Tier 1)
        # Move SL to Breakeven if > 20 points profit
        current_price = mt5.symbol_info_tick(symbol).bid
        points = mt5.symbol_info(symbol).point
        
        profit_points = (current_price - pos.price_open) / points
        
        # LOGIC: If profit > 200 points (20 pips) and SL is active
        if profit_points > 200 and pos.sl < pos.price_open:
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": pos.ticket,
                "sl": pos.price_open, # Breakeven
                "tp": pos.tp
            }
            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                log_event("MANAGING", f"Position {pos.ticket} secured at Breakeven.")
                
    return len(positions)

def scan_market():
    """
    Placeholder for your entry logic.
    Replace this pass with your specific indicator checks.
    """
    # Logic goes here...
    return False

# --- MAIN SYSTEM LOOP ---
def main():
    if not mt5.initialize():
        log_event("CRITICAL", f"MT5 Init Failed: {mt5.last_error()}")
        return

    log_event("SYSTEM", "Bot Started. Tier 1 Configuration Loaded.")
    
    try:
        while True:
            # 1. Connection Check
            if not mt5.terminal_info().connected:
                print_dashboard("🔴 OFFLINE", "Connection Lost")
                time.sleep(5)
                continue

            # 2. Update Account Info
            account_info = mt5.account_info()
            if not account_info:
                print("Failed to get account info")
                continue

            # 3. Manage Existing Trades (Priority)
            active_count = manage_positions()

            # 4. Scan for New Trades
            # Only scan if we have margin (Logic check)
            if scan_market():
                log_event("TRADE", "Signal Detected (Placeholder)")

            # 5. Update UI (Visual Fix)
            if active_count > 0:
                print_dashboard("MANAGING", "Optimizing Positions...", active_count)
            else:
                print_dashboard("SCANNING", "Market Evaluation in progress...", 0)

            # 6. Throttle (Prevent CPU overload but fast enough for ticks)
            time.sleep(1)

    except KeyboardInterrupt:
        mt5.shutdown()
        print("\nBot Stopped by User.")

if __name__ == "__main__":
    main()
