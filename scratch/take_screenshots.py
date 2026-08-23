import sys
from playwright.sync_api import sync_playwright

def main():
    out_dir = r"C:\Users\samsung\.gemini\antigravity\brain\a1fcc791-5aaa-493e-aefa-0b3c8e8d1237"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Capture index.html
        print("Navigating to index.html...")
        page.goto("https://stockrecommend.vercel.app/index.html")
        page.wait_for_timeout(3000)
        page.screenshot(path=f"{out_dir}\\screenshot_index.png")
        print("Captured index.html")
        
        # Capture screener.html
        print("Navigating to screener.html...")
        page.goto("https://stockrecommend.vercel.app/screener.html")
        page.wait_for_timeout(3000)
        page.screenshot(path=f"{out_dir}\\screenshot_screener.png")
        print("Captured screener.html")
        
        browser.close()

if __name__ == "__main__":
    main()
