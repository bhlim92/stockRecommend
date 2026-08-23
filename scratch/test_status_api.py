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

res = requests.get(f"https://stockrecommend.vercel.app/api/screener/status", cookies=cookies)
print(f"Status: {res.status_code}")
print(res.text)
