import sys
import google.generativeai as genai

def test_key(key):
    print(f"Testing key: {key[:10]}...")
    genai.configure(api_key=key)
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content("Say hello in one word")
        print("[+] Success!")
        print("Response:", response.text.strip())
        return True
    except Exception as e:
        print("[x] Error testing key:")
        print(str(e))
        return False

if __name__ == "__main__":
    key = os.getenv("GEMINI_API_KEY", "")
    if len(sys.argv) > 1:
        key = sys.argv[1]
    test_key(key)
