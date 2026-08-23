import sys
import os
import time
import base64
import hmac
import hashlib
from playwright.sync_api import sync_playwright

AUTH_SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "antigravity-quant-secret-2026-key")
AUTHORIZED_EMAIL = "bumhyun.lim@gmail.com"

def create_session_token(email: str) -> str:
    expiry = int(time.time()) + (24 * 3600)  # 24 hours
    payload = f"{email}:{expiry}"
    signature = hmac.new(AUTH_SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    token = f"{payload}:{signature}"
    return base64.b64encode(token.encode()).decode()

def main():
    out_dir = r"C:\Users\samsung\.gemini\antigravity\brain\a1fcc791-5aaa-493e-aefa-0b3c8e8d1237"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        
        # Inject auth cookie
        token = create_session_token(AUTHORIZED_EMAIL)
        context.add_cookies([{
            "name": "auth_token",
            "value": token,
            "domain": "127.0.0.1",
            "path": "/",
            "httpOnly": True,
            "secure": False,
            "sameSite": "Lax"
        }])
        
        page = context.new_page()
        
        # Capture screener.html
        print("Navigating to screener.html with auth cookie on localhost...")
        page.goto("http://127.0.0.1:8005/screener.html")
        page.wait_for_timeout(4000) # Wait for JS and API fetching
        page.screenshot(path=f"{out_dir}\\ui_final_ver34.png")
        print("Captured screener.html")
        
        browser.close()

if __name__ == "__main__":
    main()
