import pandas as pd
import numpy as np

def test_macd():
    def calc_s2(closes):
        closes = pd.Series(closes)
        ema_12 = closes.ewm(span=12, adjust=False).mean()
        ema_26 = closes.ewm(span=26, adjust=False).mean()
        macd = ema_12 - ema_26
        signal = macd.ewm(span=9, adjust=False).mean()
        
        macd_today = float(macd.iloc[-1])
        signal_today = float(signal.iloc[-1])
        macd_yest = float(macd.iloc[-2]) if len(macd) >= 2 else macd_today
        signal_yest = float(signal.iloc[-2]) if len(signal) >= 2 else signal_today
        
        print(f"Today MACD: {macd_today:.4f}, Signal: {signal_today:.4f}")
        print(f"Yest MACD: {macd_yest:.4f}, Signal: {signal_yest:.4f}")
        
        if macd_yest <= signal_yest and macd_today > signal_today and macd_today > 0:
            return 1.0
        elif macd_yest >= signal_yest and macd_today < signal_today:
            return -1.0
        else:
            return 0.0

    # 1. Golden Cross (s2 = 1.0):
    closes_golden = [100.0] * 230 + [98.0, 96.0, 94.0, 92.0, 90.0, 88.0, 86.0, 84.0, 82.0, 150.0]
    print("Golden Cross Test:")
    s2_g = calc_s2(closes_golden)
    print(f"Result S2: {s2_g}")
    
    # 2. Death Cross (s2 = -1.0):
    closes_death = [100.0] * 230 + [102.0, 104.0, 106.0, 108.0, 110.0, 112.0, 114.0, 116.0, 118.0, 90.0]
    print("\nDeath Cross Test:")
    s2_d = calc_s2(closes_death)
    print(f"Result S2: {s2_d}")

if __name__ == "__main__":
    test_macd()
