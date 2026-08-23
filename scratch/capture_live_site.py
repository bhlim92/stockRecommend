from playwright.sync_api import sync_playwright
import os

def capture():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print("Navigating to https://stockrecommend.vercel.app/")
        try:
            page.goto("https://stockrecommend.vercel.app/")
            page.wait_for_timeout(3000)
        except Exception as e:
            print(f"Error navigating: {e}")
        
        # Save to artifact dir
        artifact_dir = r"C:\Users\samsung\.gemini\antigravity\brain\a1fcc791-5aaa-493e-aefa-0b3c8e8d1237"
        filepath = os.path.join(artifact_dir, "live_vercel_500.png")
        page.screenshot(path=filepath)
        print(f"Screenshot saved to {filepath}")
        
        # Print the text content of the page to know what it is
        content = page.content()
        if "500" in content or "Internal Server Error" in content:
            print("Confirmed: Page shows 500 Internal Server Error.")
        elif "ANTIGRAVITY" in content or "Login" in content:
            print("Confirmed: Page shows the application.")
            
        browser.close()

if __name__ == "__main__":
    capture()
