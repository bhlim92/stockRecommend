import requests

def test_auth():
    url = "https://stockrecommend.vercel.app/api/auth/config"
    print(f"GET {url}")
    try:
        r = requests.get(url, timeout=10)
        print("Status Code:", r.status_code)
        print("Response:", r.text)
    except Exception as e:
        print("Error:", str(e))

if __name__ == "__main__":
    test_auth()
