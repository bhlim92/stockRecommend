import os
import sys
import json
import time
import requests
import pandas as pd
import yfinance as yf
from io import StringIO

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.scoring import QuantScorer

def run_baseline_test():
    print("[*] Loading S&P 500 tickers from Wikipedia...")
    start_wiki = time.time()
    headers = {'User-Agent': 'Mozilla/5.0'}
    resp = requests.get('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies', headers=headers, timeout=10)
    df = pd.read_html(StringIO(resp.text))[0]
    tickers = [str(row['Symbol']).replace(".", "-") for _, row in df.iterrows()]
    wiki_time = time.time() - start_wiki
    print(f"[+] Loaded {len(tickers)} tickers in {wiki_time:.2f} seconds.")
    
    # Take a sample of 20 tickers for baseline testing
    sample_size = 20
    sample_tickers = tickers[:sample_size]
    print(f"[*] Testing with a sample of {sample_size} tickers: {sample_tickers}")
    
    # Measure Price Download time in batch
    print("[*] Downloading historical prices in batch...")
    start_price = time.time()
    df_batch = yf.download(sample_tickers, period="1y", group_by="ticker", progress=False, timeout=20)
    price_time = time.time() - start_price
    print(f"[+] Downloaded historical prices in {price_time:.2f} seconds.")
    
    # Parse preloaded prices
    preloaded_prices = {}
    for ticker in sample_tickers:
        if sample_size == 1:
            df_ticker = df_batch
        else:
            if ticker in df_batch.columns.levels[0]:
                df_ticker = df_batch[ticker]
            else:
                continue
        df_ticker = df_ticker.dropna(subset=["Close"])
        if not df_ticker.empty:
            preloaded_prices[ticker] = df_ticker
            
    # Measure Fundamental Fetching time sequentially (the current logic)
    print("[*] Fetching fundamentals sequentially...")
    scorer = QuantScorer()
    start_fund = time.time()
    
    fund_times = []
    results = {}
    for ticker in sample_tickers:
        ticker_start = time.time()
        # Simulate yf_ticker.info
        try:
            info = yf.Ticker(ticker).info
            current_price = scorer._extract_current_price(ticker, preloaded_prices)
            fundamentals = scorer._parse_fundamentals(info, current_price)
            eval_score = scorer._calc_fundamental_score(fundamentals, current_price)
            results[ticker] = {
                "name": info.get("shortName") or ticker,
                "current_price": current_price,
                "eval_score": eval_score
            }
        except Exception as e:
            print(f"[x] Error fetching {ticker}: {str(e)}")
        ticker_time = time.time() - ticker_start
        fund_times.append(ticker_time)
        print(f"    - {ticker}: {ticker_time:.2f}s")
        time.sleep(0.1) # Simulate the throttling sleep in ScreenerManager
        
    total_fund_time = time.time() - start_fund
    avg_fund_time = sum(fund_times) / len(fund_times) if fund_times else 0
    
    print("\n" + "="*50)
    print("=== BASELINE RESULTS (SEQUENTIAL) ===")
    print(f"Sample Tickers Count: {sample_size}")
    print(f"Total Fundamental Fetching Time: {total_fund_time:.2f} seconds")
    print(f"Average Time per Ticker: {avg_fund_time:.2f} seconds (including 0.1s throttle sleep)")
    
    # Extrapolate for 500 stocks
    extrapolated_time_500 = avg_fund_time * 500
    print(f"Extrapolated Time for 500 stocks: {extrapolated_time_500:.2f} seconds ({extrapolated_time_500/60:.2f} minutes)")
    print("="*50 + "\n")
    
    # Save statistics
    stats = {
        "wiki_time": wiki_time,
        "ticker_count": len(tickers),
        "price_time": price_time,
        "sample_size": sample_size,
        "total_fund_time": total_fund_time,
        "avg_fund_time": avg_fund_time,
        "extrapolated_time_500": extrapolated_time_500,
        "tickers_tested": sample_tickers,
        "results": results
    }
    
    os.makedirs("reports", exist_ok=True)
    with open("reports/baseline_stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=4)
    print("[+] Saved baseline stats to reports/baseline_stats.json")

if __name__ == "__main__":
    run_baseline_test()
