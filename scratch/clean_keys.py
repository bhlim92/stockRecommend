import os
import glob

scratch_dir = r"c:\Users\samsung\proj\stockRecommend\scratch"
key_str = os.getenv("GEMINI_API_KEY", "")

for fpath in glob.glob(os.path.join(scratch_dir, "*.py")):
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        if key_str in content:
            new_content = content.replace(f'"{key_str}"', 'os.getenv("GEMINI_API_KEY", "")')
            new_content = new_content.replace(key_str, "")
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(new_content)
            print("Cleaned key in:", os.path.basename(fpath))
    except Exception as e:
        print("Error:", e)
