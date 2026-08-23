import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    artifacts_dir = r"C:\Users\samsung\.gemini\antigravity\brain\a1fcc791-5aaa-493e-aefa-0b3c8e8d1237"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # 1. Visit screener.html (which will redirect to login)
        print("Navigating to https://stockrecommend.vercel.app/screener.html...")
        response = await page.goto("https://stockrecommend.vercel.app/screener.html")
        await page.wait_for_timeout(2000)
        
        title = await page.title()
        url = page.url
        print(f"Loaded URL: {url}")
        print(f"Page Title: {title}")
        
        # Take screenshot of login page
        screenshot_path = os.path.join(artifacts_dir, "deployed_login_page.png")
        await page.screenshot(path=screenshot_path)
        print(f"Screenshot saved to: {screenshot_path}")
        
        # Verify content
        content = await page.content()
        if "ANTIGRAVITY" in content:
            print("[Success] Page loaded successfully and contains 'ANTIGRAVITY'")
        else:
            print("[Failure] Could not verify page content")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
