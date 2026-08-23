import sys
import os
import time
import base64
import hmac
import hashlib
from playwright.sync_api import sync_playwright

AUTH_SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "antigravity-quant-secret-2026-key")
AUTHORIZED_EMAIL = "bumhyun.lim@gmail.com"
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")

def create_session_token(email: str) -> str:
    expiry = int(time.time()) + (24 * 3600)
    payload = f"{email}:{expiry}"
    signature = hmac.new(AUTH_SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    token = f"{payload}:{signature}"
    return base64.b64encode(token.encode()).decode()

def main():
    out_dir = r"C:\Users\samsung\.gemini\antigravity\brain\a1fcc791-5aaa-493e-aefa-0b3c8e8d1237"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        
        token = create_session_token(AUTHORIZED_EMAIL)
        context.add_cookies([{
            "name": "auth_token",
            "value": token,
            "domain": "stockrecommend.vercel.app",
            "path": "/",
            "httpOnly": True,
            "secure": True,
            "sameSite": "Lax"
        }])
        
        page = context.new_page()
        
        page.on("console", lambda msg: print(f"CONSOLE: {msg.type}: {msg.text}"))
        page.on("pageerror", lambda err: print(f"ERROR: {err}"))
        
        print("Navigating to origin to set localStorage...")
        page.goto("https://stockrecommend.vercel.app/")
        page.evaluate(f"localStorage.setItem('gemini_api_key', '{GEMINI_KEY}');")
        
        print("Navigating to screener.html...")
        page.goto("https://stockrecommend.vercel.app/screener.html")
        page.wait_for_timeout(3000)
        
        print("Clicking KOSPI 200...")
        page.locator("button[data-market='kospi200']").click()
        page.wait_for_timeout(5000)
        
        print("Done")
        browser.close()

if __name__ == "__main__":
    main()
