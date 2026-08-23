import subprocess
import time
import socket

def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

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
    p = subprocess.Popen(args)
    
    # Wait and check port
    for _ in range(20):
        time.sleep(0.5)
        if is_port_open(9222):
            print("Chrome DevTools port 9222 is active and listening!")
            break
    else:
        print("Chrome DevTools port 9222 is not active yet.")
        
    print("Keeping Chrome alive... press Ctrl+C or kill task to stop.")
    try:
        while True:
            time.sleep(1)
            if p.poll() is not None:
                print(f"Chrome exited with code {p.poll()}")
                break
    except KeyboardInterrupt:
        print("Stopping Chrome...")
        p.terminate()

if __name__ == "__main__":
    main()
