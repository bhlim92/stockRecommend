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
            "name": "auth_token", "value": token, "domain": "localhost", "path": "/", "httpOnly": True, "secure": False, "sameSite": "Lax"
        }])
        
        page = context.new_page()
        page.on("dialog", lambda dialog: dialog.accept())
        
        print("Navigating to origin to set localStorage...")
        page.goto('http://localhost:8001/')
        page.evaluate("localStorage.setItem('gemini_api_key', 'mock');")
        
        print("Navigating to screener.html...")
        page.goto("http://localhost:8001/screener.html")
        
        print("Waiting for page load...")
        page.wait_for_timeout(2000)
        
        print("Clicking 'Start Quant Scan' button...")
        # Make sure the KOSPI200 button is active just in case
        page.click(".market-tab[data-market='sp500']")
        page.wait_for_timeout(1000)
        page.click("#btn-start-scan")
        
        print("Waiting for scan to complete and hybrid sparklines to appear (up to 120s)...")
        # The svg is inside .sparkline-container
        try:
            page.wait_for_selector(".sparkline-container svg", state="visible", timeout=300000)
            print("Sparklines appeared! Taking a quick pause to let rendering settle...")
            page.wait_for_timeout(2000)
            
            screenshot_path = f"{out_dir}\\ui_hybrid_sparkline_final.png"
            page.screenshot(path=screenshot_path)
            print(f"Saved {screenshot_path}")
        except Exception as e:
            print(f"Failed or timed out: {e}")
            page.screenshot(path=f"{out_dir}\\ui_hybrid_error.png")
            
        browser.close()

if __name__ == "__main__":
    main()
