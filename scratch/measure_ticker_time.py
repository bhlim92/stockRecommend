import time
import yfinance as yf
from app.scoring import QuantScorer

def measure():
    ticker = "AAPL"
    print(f"[*] Preloading price history for {ticker}...")
    start_dl = time.time()
    df = yf.download(ticker, period="1y", progress=False)
    dl_time = time.time() - start_dl
    print(f"[+] Download completed in {dl_time:.3f} seconds.")

    if df.empty:
        print("[x] Error: Failed to preload data.")
        return

    scorer = QuantScorer()
    
    # Measure scoring calculation time
    print(f"[*] Running QuantScorer for {ticker}...")
    start_calc = time.time()
    res = scorer.calculate_scores([ticker], preloaded_prices={ticker: df})
    calc_time = time.time() - start_calc
    print(f"[+] QuantScorer execution completed.")
    print(f"    - Scoring Result: {res.get(ticker, {})}")
    print(f"    - Pure Calculation Time: {calc_time:.4f} seconds ({calc_time*1000:.1f} ms)")

if __name__ == "__main__":
    measure()
