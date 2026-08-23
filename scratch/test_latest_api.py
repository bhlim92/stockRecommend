import requests
import os
import time
import base64
import hmac
import hashlib

AUTH_SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "antigravity-quant-secret-2026-key")
AUTHORIZED_EMAIL = "bumhyun.lim@gmail.com"

def create_session_token(email: str) -> str:
    expiry = int(time.time()) + (24 * 3600)
    payload = f"{email}:{expiry}"
    signature = hmac.new(AUTH_SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    token = f"{payload}:{signature}"
    return base64.b64encode(token.encode()).decode()

token = create_session_token(AUTHORIZED_EMAIL)
cookies = {"auth_token": token}

for market in ["sp500", "kospi200", "kosdaq"]:
    print(f"--- Fetching latest for {market} ---")
    res = requests.get(f"https://stockrecommend.vercel.app/api/screener/latest?market={market}", cookies=cookies)
    print(f"Status: {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        results = data.get("results", [])
        print(f"Records returned: {len(results)}")
        if len(results) > 0:
            print(f"First record: {results[0]}")
    else:
        print(res.text)
