import time
import yfinance as yf
from app.config import AppConfig

# Get first 50 tickers from KOSPI 200 dynamically or via fallback
try:
    import FinanceDataReader as fdr
    df = fdr.StockListing("KOSPI")
    df_sorted = df.sort_values(by="Marcap", ascending=False).head(50)
    tickers = [f"{row['Code']}.KS" for _, row in df_sorted.iterrows()]
except Exception:
    tickers = [
        "005930.KS", "000660.KS", "373220.KS", "207940.KS", "005380.KS", 
        "005490.KS", "051910.KS", "000270.KS", "035420.KS", "006400.KS",
        "051900.KS", "003550.KS", "035720.KS", "012330.KS", "066570.KS",
        "096770.KS", "032830.KS", "000810.KS", "033780.KS", "086790.KS",
        "009150.KS", "015760.KS", "018261.KS", "017670.KS", "011200.KS",
        "009830.KS", "055550.KS", "105560.KS", "005935.KS", "323410.KS",
        "000080.KS", "000100.KS", "000120.KS", "000150.KS", "000210.KS",
        "000240.KS", "000300.KS", "000370.KS", "000390.KS", "000670.KS",
        "000720.KS", "000880.KS", "000990.KS", "001040.KS", "001120.KS",
        "001230.KS", "001430.KS", "001450.KS", "001520.KS", "001740.KS"
    ]

print(f"Testing batch download of {len(tickers)} tickers...")
start_time = time.time()
df = yf.download(tickers, period="1mo", interval="1d", group_by="ticker", threads=True, progress=False)
elapsed = time.time() - start_time

print(f"Time taken for {len(tickers)} tickers: {elapsed:.2f} seconds")
print(f"Estimated for 200 tickers (KOSPI 200): {elapsed * (200/len(tickers)):.2f} seconds")
print(f"Estimated for 500 tickers (S&P 500): {elapsed * (500/len(tickers)):.2f} seconds")
