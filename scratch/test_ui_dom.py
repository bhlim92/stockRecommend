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
            "name": "auth_token", "value": token, "domain": "stockrecommend.vercel.app", "path": "/", "httpOnly": True, "secure": True, "sameSite": "Lax"
        }])
        
        page = context.new_page()
        page.on("dialog", lambda dialog: print(f"DIALOG: {dialog.message}") or dialog.accept())
        
        print("Navigating to screener.html...")
        page.goto("https://stockrecommend.vercel.app/screener.html")
        page.wait_for_timeout(3000)
        
        print("Initial tabs:")
        for t in page.locator(".market-tab").all():
            print(t.get_attribute("data-market"), t.get_attribute("class"))
            
        print("Initial rows:")
        print(page.locator("#table-body tr").count())

        print("Clicking KOSPI 200...")
        page.locator("button[data-market='kospi200']").click()
        page.wait_for_timeout(5000)
        page.screenshot(path=f"{out_dir}\\ui_kospi200_5sec.png")
        
        print("After click tabs:")
        for t in page.locator(".market-tab").all():
            print(t.get_attribute("data-market"), t.get_attribute("class"))
            
        print("After click rows:")
        print(page.locator("#table-body tr").count())
        
        browser.close()

if __name__ == "__main__":
    main()
