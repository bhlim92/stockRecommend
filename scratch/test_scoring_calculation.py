import yfinance as yf
import pandas as pd
import numpy as np

def calculate_technical_entry_score(df: pd.DataFrame) -> tuple:
    if len(df) < 200:
        return 0.0, 0, {}
        
    closes = df["Close"]
    opens = df["Open"]
    volumes = df["Volume"]
    
    # 1. S1: Moving Averages Alignment
    sma_5 = float(closes.rolling(5).mean().iloc[-1])
    sma_20 = float(closes.rolling(20).mean().iloc[-1])
    sma_200 = float(closes.rolling(200).mean().iloc[-1])
    
    if sma_5 > sma_20 > sma_200:
        s1 = 1.0
    elif sma_5 < sma_20 < sma_200:
        s1 = -1.0
    else:
        s1 = 0.0
        
    # 2. S2: MACD Crossover
    # MACD Line = 12 EMA - 26 EMA
    ema_12 = closes.ewm(span=12, adjust=False).mean()
    ema_26 = closes.ewm(span=26, adjust=False).mean()
    macd = ema_12 - ema_26
    signal = macd.ewm(span=9, adjust=False).mean()
    
    macd_today = float(macd.iloc[-1])
    signal_today = float(signal.iloc[-1])
    macd_yest = float(macd.iloc[-2]) if len(macd) >= 2 else macd_today
    signal_yest = float(signal.iloc[-2]) if len(signal) >= 2 else signal_today
    
    # Golden cross: MACD crosses above signal AND MACD > 0
    if macd_yest <= signal_yest and macd_today > signal_today and macd_today > 0:
        s2 = 1.0
    # Death cross: MACD crosses below signal
    elif macd_yest >= signal_yest and macd_today < signal_today:
        s2 = -1.0
    else:
        s2 = 0.0
        
    # 3. S3: Pullback RSI (14 days)
    delta = closes.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    rsi_today = float(rsi.iloc[-1])
    
    # Pullback condition: S1 == 1 (uptrend) and RSI in 40-50
    if s1 == 1.0 and 40.0 <= rsi_today <= 50.0:
        s3 = 1.0
    # Overbought condition: RSI > 80
    elif rsi_today > 80.0:
        s3 = -1.0
    else:
        s3 = 0.0
        
    # 4. S4: Volume (Supply)
    avg_vol_20 = float(volumes.rolling(20).mean().iloc[-1])
    current_vol = float(volumes.iloc[-1])
    current_close = float(closes.iloc[-1])
    current_open = float(opens.iloc[-1])
    
    # Volume >= 1.5x of 20-day average and green candle (Close > Open)
    if current_vol >= 1.5 * avg_vol_20 and current_close > current_open:
        s4 = 1.0
    else:
        s4 = 0.0
        
    # Final Score Calculation
    final_score = (0.4 * s1) + (0.3 * s2) + (0.2 * s3) + (0.1 * s4)
    mapped_score = int(round((final_score + 1.0) * 50))
    # Cap to 0-100
    mapped_score = max(0, min(100, mapped_score))
    
    metrics = {
        "s1": s1, "s2": s2, "s3": s3, "s4": s4,
        "sma_5": sma_5, "sma_20": sma_20, "sma_200": sma_200,
        "macd_today": macd_today, "signal_today": signal_today,
        "rsi_today": rsi_today, "vol_current": current_vol,
        "vol_avg_20": avg_vol_20
    }
    
    return final_score, mapped_score, metrics

def test():
    ticker = "AAPL"
    df = yf.download(ticker, period="1y", progress=False)
    if not df.empty:
        # yfinance output columns can be MultiIndex or simple Index depending on version
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
        final, mapped, details = calculate_technical_entry_score(df)
        print(f"=== {ticker} Technical Entry Score ===")
        print(f"Final Score (-1.0 to +1.0): {final:.2f}")
        print(f"Mapped Entry Score (0 to 100): {mapped}")
        print(f"Metrics: {details}")

if __name__ == "__main__":
    test()
