import os
import sys
import hmac
import hashlib
import time
import base64

# Force TESTING = false to enable the authentication middleware
os.environ["TESTING"] = "false"

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.web_server import app, generate_session_token, AUTHORIZED_EMAIL, AUTH_SECRET_KEY

client = TestClient(app)

def test_auth_missing_cookie():
    print("[TEST] Requesting /api/portfolio without session cookie...")
    response = client.get("/api/portfolio")
    print(f"Response Status: {response.status_code}")
    print(f"Response JSON: {response.json()}")
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    assert "Access denied" in response.json().get("detail", ""), "Expected Access denied in details"
    print("[PASS] Missing session cookie successfully returns 401 Unauthorized.\n")

def test_auth_invalid_cookie():
    print("[TEST] Requesting /api/portfolio with invalid session cookie...")
    client.cookies.set("auth_token", "invalid_token_b64_string")
    response = client.get("/api/portfolio")
    print(f"Response Status: {response.status_code}")
    print(f"Response JSON: {response.json()}")
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    assert "Access denied" in response.json().get("detail", ""), "Expected Access denied in details"
    client.cookies.clear()
    print("[PASS] Invalid session cookie successfully returns 401 Unauthorized.\n")

def test_auth_expired_cookie():
    print("[TEST] Requesting /api/portfolio with expired session cookie...")
    # Generate an expired token (expiry in the past)
    expiry = int(time.time()) - 100
    payload = f"{AUTHORIZED_EMAIL}:{expiry}"
    signature = hmac.new(AUTH_SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    token = f"{payload}:{signature}"
    expired_token = base64.b64encode(token.encode()).decode()
    
    client.cookies.set("auth_token", expired_token)
    response = client.get("/api/portfolio")
    print(f"Response Status: {response.status_code}")
    print(f"Response JSON: {response.json()}")
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    assert "Access denied" in response.json().get("detail", ""), "Expected Access denied in details"
    client.cookies.clear()
    print("[PASS] Expired session cookie successfully returns 401 Unauthorized.\n")

def test_auth_valid_cookie():
    print("[TEST] Requesting /api/portfolio with a valid session cookie...")
    valid_token = generate_session_token(AUTHORIZED_EMAIL)
    client.cookies.set("auth_token", valid_token)
    response = client.get("/api/portfolio")
    print(f"Response Status: {response.status_code}")
    # Since portfolio.json exists and we are authorized, it should return 200 OK
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    print("[PASS] Valid session cookie successfully returns 200 OK and accesses the portfolio.\n")

if __name__ == "__main__":
    print("====================================================")
    print("Running QA Authentication Verification Tests")
    print("====================================================")
    try:
        test_auth_missing_cookie()
        test_auth_invalid_cookie()
        test_auth_expired_cookie()
        test_auth_valid_cookie()
        print("All authentication verification tests PASSED successfully!")
        sys.exit(0)
    except AssertionError as e:
        print(f"FAIL: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected exception during test execution: {e}")
        sys.exit(2)
