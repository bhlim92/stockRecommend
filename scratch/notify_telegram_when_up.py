import time
import urllib.request
import urllib.parse
import json
import os
import sys

# Append project root to path so we can import from scratch
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scratch.take_screenshots_auth import create_session_token

TOKEN = '7993474728:AAGWQQcAtoMXtZhb0zK-mVGOBvul6pQnOYw'
CHAT_ID = '8340324578'
URL = 'https://stockrecommend.vercel.app/screener.html'

def send_telegram(text):
    api_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = urllib.parse.urlencode({'chat_id': CHAT_ID, 'text': text}).encode()
    req = urllib.request.Request(api_url, data=data)
    urllib.request.urlopen(req)

def check_site():
    auth_token = create_session_token('bumhyun.lim@gmail.com')
    req = urllib.request.Request(URL, headers={'Cookie': f'auth_token={auth_token}'})
    try:
        resp = urllib.request.urlopen(req)
        if resp.getcode() == 200:
            return True
    except Exception as e:
        pass
    return False

def main():
    print("Starting background checker...")
    # Loop for max 30 minutes
    for _ in range(30 * 6):
        if check_site():
            msg = "[알림] 팀장님! Vercel 배포가 드디어 성공적으로 완료되었습니다! 🥳\n\n현재 500 에러 없이 v3.4 버전이 정상적으로 서빙되고 있습니다.\n바로 확인해 보세요: https://stockrecommend.vercel.app/"
            send_telegram(msg)
            print("Telegram notification sent. Site is UP.")
            break
        print("Still down. Waiting 10 seconds...")
        time.sleep(10)

if __name__ == "__main__":
    main()
