import os
import google.generativeai as genai
from PIL import Image

api_key = os.getenv("GEMINI_API_KEY", "")
genai.configure(api_key=api_key)

model = genai.GenerativeModel('gemini-1.5-flash')

out_dir = r"C:\Users\samsung\.gemini\antigravity\brain\a1fcc791-5aaa-493e-aefa-0b3c8e8d1237"
images = ["ui_sp500.png", "ui_kospi200.png", "ui_kosdaq.png", "ui_scan_start.png"]

for img_name in images:
    img_path = os.path.join(out_dir, img_name)
    if os.path.exists(img_path):
        img = Image.open(img_path)
        response = model.generate_content([
            "Describe this screenshot in detail. Specifically, what market tab is highlighted in green (active)? Is there a table with data, or is it empty? Does the 'Start Scan' button look clicked, and is there a progress bar?", 
            img
        ])
        print(f"--- {img_name} ---")
        print(response.text)
        print()
    else:
        print(f"Image not found: {img_path}")
