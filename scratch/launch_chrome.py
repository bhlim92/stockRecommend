import subprocess
import time
import sys

def main():
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    args = [
        chrome_path,
        "--remote-debugging-port=9222",
        "--user-data-dir=C:\\Users\\samsung\\proj\\stockRecommend\\temp_chrome_profile",
        "--headless=new",
        "--disable-gpu",
        "--no-first-run"
    ]
    print("Launching Chrome...")
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Wait for up to 10 seconds or until process exits
    for i in range(20):
        time.sleep(0.5)
        poll = p.poll()
        if poll is not None:
            print(f"Chrome exited with code {poll}")
            stdout, stderr = p.communicate()
            print(f"Stdout:\n{stdout}")
            print(f"Stderr:\n{stderr}")
            return
            
    print("Chrome is still running (PID:", p.pid, ")")
    # Terminate it
    p.terminate()
    stdout, stderr = p.communicate()
    print(f"Stdout:\n{stdout}")
    print(f"Stderr:\n{stderr}")
        
if __name__ == "__main__":
    main()
