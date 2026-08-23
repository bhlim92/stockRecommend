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
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        token = create_session_token(AUTHORIZED_EMAIL)
        context.add_cookies([{
            "name": "auth_token", "value": token, "domain": "stockrecommend.vercel.app", "path": "/", "httpOnly": True, "secure": True, "sameSite": "Lax"
        }])
        
        page = context.new_page()
        page.on("dialog", lambda dialog: dialog.accept())
        
        print("Navigating to origin to set localStorage...")
        page.goto("https://stockrecommend.vercel.app/")
        
        print("Navigating to screener.html...")
        page.goto("https://stockrecommend.vercel.app/screener.html")
        
        print("Waiting for initial data to load and trend buttons to appear...")
        try:
            page.wait_for_selector(".trend-btn", timeout=15000)
            
            print("Clicking the first Trend button...")
            trend_btns = page.locator(".trend-btn")
            trend_btns.first.click()
            
            print("Waiting for sparkline to render...")
            page.wait_for_selector(".sparkline-container svg", timeout=10000)
            
            print("Clicking the sparkline to open modal...")
            page.locator(".sparkline-container").first.click()
            
            print("Waiting 3s for Yahoo Finance to fetch 1y data & render Chart.js...")
            # Wait for canvas to be visible
            page.wait_for_selector("#detailChart", state="visible", timeout=10000)
            page.wait_for_timeout(3000) # give it time to animate
            
            page.screenshot(path=f"{out_dir}\\ui_modal_chart_final.png")
            print("Saved ui_modal_chart_final.png")
            
        except Exception as e:
            print(f"Error during test: {e}")
            page.screenshot(path=f"{out_dir}\\ui_modal_error.png")
            
        browser.close()

if __name__ == "__main__":
    main()
