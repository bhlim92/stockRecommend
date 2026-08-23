import requests

url = "https://stockrecommend.vercel.app/api/screener/history/005930.KS?period=1y"
resp = requests.get(url)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print("Keys:", data.keys())
    if "dates" in data:
        print("Dates length:", len(data["dates"]))
        print("Prices length:", len(data["prices"]))
        print("MA5 length:", len(data["ma5"]))
        print("MA20 length:", len(data["ma20"]))
        print("MA200 length:", len(data["ma200"]))
        # check if they have valid values
        print("Sample dates:", data["dates"][:5])
        print("Sample prices:", data["prices"][:5])
        print("Sample MA200:", data["ma200"][:5])
else:
    print(resp.text)
