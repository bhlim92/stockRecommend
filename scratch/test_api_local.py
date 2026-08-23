import sys
sys.path.append(r"c:\Users\samsung\proj\stockRecommend")

from app.web_server import get_screener_history
import json

try:
    resp = get_screener_history("005930.KS", "1y")
    data = json.loads(resp.body.decode('utf-8'))
    print("Keys:", data.keys())
    
    if "dates" in data:
        # Check if there are null values that might break JSON or JS
        print("MA5 nulls:", sum(1 for x in data["ma5"] if x is None))
        print("MA20 nulls:", sum(1 for x in data["ma20"] if x is None))
        print("MA200 nulls:", sum(1 for x in data["ma200"] if x is None))
        print("Sample MA200 values:", data["ma200"][195:205])
except Exception as e:
    import traceback
    traceback.print_exc()
