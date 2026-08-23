import pandas as pd
import numpy as np

def test_rsi():
    def calc_s1_s3(closes):
        closes = pd.Series(closes)
        sma_5 = float(closes.rolling(5).mean().iloc[-1])
        sma_20 = float(closes.rolling(20).mean().iloc[-1])
        sma_200 = float(closes.rolling(200).mean().iloc[-1])
        
        if sma_5 > sma_20 > sma_200:
            s1 = 1.0
        elif sma_5 < sma_20 < sma_200:
            s1 = -1.0
        else:
            s1 = 0.0
            
        delta = closes.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
        
        avg_gain_val = float(avg_gain.iloc[-1])
        avg_loss_val = float(avg_loss.iloc[-1])
        if avg_loss_val == 0:
            rsi_today = 100.0
        else:
            rs = avg_gain_val / avg_loss_val
            rsi_today = 100.0 - (100.0 / (1.0 + rs))
            
        if s1 == 1.0 and 40.0 <= rsi_today <= 50.0:
            s3 = 1.0
        elif rsi_today > 80.0:
            s3 = -1.0
        else:
            s3 = 0.0
            
        return s1, rsi_today, s3, sma_5, sma_20, sma_200

    # Let's search by varying:
    # 1. Base trend (100 to 200 over 230 days)
    # 2. Pullback days (e.g. 10 days of drops)
    # 3. Recovery days (e.g. 10 days of rising back to push sma_5 > sma_20)
    base = np.linspace(100, 200, 230).tolist()
    
    found = False
    for pull_drop in np.linspace(1, 5, 9):
        for pull_len in range(5, 15):
            for rec_rise in np.linspace(0.5, 3, 6):
                for rec_len in range(3, 10):
                    # Simulate pullback: e.g. from 200, drop by pull_drop each day
                    pullback = [200.0 - i * pull_drop for i in range(1, pull_len + 1)]
                    last_val = pullback[-1] if pullback else 200.0
                    # Simulate recovery: rise by rec_rise each day
                    recovery = [last_val + i * rec_rise for i in range(1, rec_len + 1)]
                    
                    closes = base + pullback + recovery
                    # Make sure it's 250 days or more
                    if len(closes) < 200:
                        continue
                    
                    s1, rsi, s3, s5, s20, s200 = calc_s1_s3(closes)
                    if s3 == 1.0:
                        print(f"SUCCESS: pull_drop={pull_drop}, pull_len={pull_len}, rec_rise={rec_rise}, rec_len={rec_len}")
                        print(f"S1={s1}, RSI={rsi:.2f}, SMA5={s5:.2f}, SMA20={s20:.2f}, SMA200={s200:.2f}")
                        print(f"Closes length: {len(closes)}")
                        print(f"Last few closes: {closes[-10:]}")
                        found = True
                        break
                if found: break
            if found: break
        if found: break

if __name__ == "__main__":
    test_rsi()
