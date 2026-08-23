import requests
import time

def test_screener():
    url_start = "http://127.0.0.1:8000/api/screener/start"
    url_status = "http://127.0.0.1:8000/api/screener/status"
    
    # 1. Trigger scan
    print("[*] Triggering screener scan...")
    try:
        res = requests.post(url_start, json={
            "market": "sp500",
            "api_key": "fake_key",
            "model": "gemini-2.5-flash"
        }, timeout=10)
        print(f"Start Response: {res.status_code} - {res.json()}")
    except Exception as e:
        print(f"[x] Start request failed: {e}")
        return

    # 2. Poll status a few times
    for i in range(10):
        time.sleep(1.5)
        try:
            res_status = requests.get(url_status, timeout=10)
            data = res_status.json()
            print(f"\n--- Poll {i+1} ---")
            print(f"Status: {data.get('status')}")
            print(f"Progress: {data.get('progress')}% ({data.get('current')}/{data.get('total')})")
            print(f"Last Log Lines:")
            logs = data.get("logs", [])
            for line in logs[-5:]:
                print(f"  {line}")
        except Exception as e:
            print(f"[x] Status poll failed: {e}")
            break

if __name__ == "__main__":
    test_screener()
