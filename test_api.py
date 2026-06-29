import requests

BASE_URL = "http://127.0.0.1:5000"

def run_tests():
    print("🚀 STARTING BACKEND API VERIFICATION TESTS...\n")

    # ---------------------------------------------------------
    # TEST 1: POST /auth/login (Invalid Credentials)
    # ---------------------------------------------------------
    print("❌ TEST 1: Testing Login with Invalid Credentials...")
    login_data_fail = {
        "username": "wrong_user",
        "password": "wrong_password"
    }
    r1 = requests.post(f"{BASE_URL}/auth/login", json=login_data_fail)
    print(f"Status Code: {r1.status_code} (Expected: 401)")
    print(f"Response: {r1.text}\n")


    # ---------------------------------------------------------
    # TEST 2: POST /auth/login (Valid Credentials)
    # ---------------------------------------------------------
    print("✅ TEST 2: Testing Login with Valid Credentials...")
    # NOTE: Adjust these credentials to match a user you seeded in your DB (e.g. admin)
    login_data_success = {
        "username": "admin", 
        "password": "adminpassword" 
    }
    r2 = requests.post(f"{BASE_URL}/auth/login", json=login_data_success)
    print(f"Status Code: {r2.status_code} (Expected: 200)")
    print(f"Response: {r2.text}")
    
    token = None
    if r2.status_code == 200:
        res_json = r2.json()
        token = res_json.get("token")
    print(f"Extracted Token: {token[:20] if token else 'None'}...\n")


    # ---------------------------------------------------------
    # TEST 3: GET /auth/me (Missing Token Header)
    # ---------------------------------------------------------
    print("❌ TEST 3: Testing Protected Route Profile without Token...")
    r3 = requests.get(f"{BASE_URL}/auth/me")
    print(f"Status Code: {r3.status_code} (Expected: 401)")
    print(f"Response: {r3.text}\n")


    # ---------------------------------------------------------
    # TEST 4: GET /auth/me (With Valid Token Header)
    # ---------------------------------------------------------
    if not token:
        print("⚠️ Skipping remaining tests because no token was generated. Verify your seed credentials.")
        return

    print("✅ TEST 4: Testing Protected Route Profile with Token...")
    headers = {
        "Authorization": f"Bearer {token}"
    }
    r4 = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    print(f"Status Code: {r4.status_code} (Expected: 200)")
    print(f"Response: {r4.text}\n")


    # ---------------------------------------------------------
    # TEST 5: GET /products (Protected Inventory List)
    # ---------------------------------------------------------
    print("✅ TEST 5: Testing Get Inventory list...")
    r5 = requests.get(f"{BASE_URL}/products", headers=headers)
    print(f"Status Code: {r5.status_code} (Expected: 200)")
    print(f"Response: {r5.text}\n")

if __name__ == "__main__":
    try:
        run_tests()
    except requests.exceptions.ConnectionError:
        print("🚨 CONNECTION ERROR: Is your Flask server running? Make sure to run 'python main.py' first!")