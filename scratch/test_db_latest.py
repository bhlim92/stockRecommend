import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_top_screener_results

res_sp500 = get_top_screener_results(limit=5, market='sp500')
res_kospi = get_top_screener_results(limit=5, market='kospi200')
res_kosdaq = get_top_screener_results(limit=5, market='kosdaq')

print("SP500 Latest Count:", len(res_sp500))
print("KOSPI200 Latest Count:", len(res_kospi))
print("KOSDAQ Latest Count:", len(res_kosdaq))
