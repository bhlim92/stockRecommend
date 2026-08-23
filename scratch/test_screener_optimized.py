import os
import sys
import time

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.screener import ScreenerManager

def monitor_screener():
    manager = ScreenerManager()
    
    # Clean/init status
    manager._init_screener()
    
    market = "sp500"
    print(f"[*] Starting optimized parallel scan for market: {market.upper()}")
    start_time = time.time()
    
    # We will temporarily limit the number of tickers to 50 for this integration test run,
    # so we don't fetch 500 tickers unnecessarily during validation, but it's enough to measure speed and ETA.
    # To do this, we can patch self.state["results"] or we can modify the tickers in load_tickers.
    # Let's mock _load_tickers to return only the first 50 S&P 500 stocks.
    original_load_tickers = manager._load_tickers
    
    def mock_load_tickers(m, force_refresh=False):
        all_tickers = original_load_tickers(m, force_refresh)
        print(f"[*] Mocking load: restricting from {len(all_tickers)} to 40 tickers for speed validation.")
        return all_tickers[:40]
        
    manager._load_tickers = mock_load_tickers

    # Start scan
    success = manager.start_scan(market)
    if not success:
        print("[x] Failed to start scan.")
        return
        
    print("[*] Monitoring progress in real-time...")
    last_printed_progress = -1
    
    while True:
        status = manager.get_status()
        current_status = status.get("status")
        progress = status.get("progress", 0)
        current_num = status.get("current", 0)
        total_num = status.get("total", 0)
        current_ticker = status.get("current_ticker", "")
        
        if progress != last_printed_progress:
            print(f"    [PROGRESS] Status: {current_status} | {progress}% ({current_num}/{total_num}) | Current: {current_ticker}")
            last_printed_progress = progress
            
        if current_status in ["done", "failed"]:
            print(f"\n[+] Scan finished with status: {current_status}")
            break
            
        time.sleep(0.5)
        
    total_elapsed = time.time() - start_time
    print(f"\n[+] Optimized parallel scan finished in {total_elapsed:.2f} seconds.")
    print("=== Last 10 Screener Logs ===")
    for log in status.get("logs", [])[-10:]:
        print(log)
        
    # Write optimized run summary to reports
    reports_dir = "reports"
    os.makedirs(reports_dir, exist_ok=True)
    summary_path = os.path.join(reports_dir, "optimized_run_summary.json")
    
    # Save statistics
    import json
    stats = {
        "market": market,
        "elapsed_time": total_elapsed,
        "ticker_count": total_num,
        "status": current_status,
        "rate": total_num / total_elapsed if total_elapsed > 0 else 0
    }
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=4)
    print(f"\n[+] Saved optimized summary to {summary_path}")

if __name__ == "__main__":
    monitor_screener()
