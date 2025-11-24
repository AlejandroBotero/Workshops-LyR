import os

base_url = os.getenv('BASE_URL', 'http://127.0.0.1:8000')
url = f"{base_url}/news/submit/"
print(f"Checking {url}...")
# ... rest unchanged ...
    # Check root first
    print("Checking root / ...")
    response = requests.get("https://hashingworkshoplogica-gjc2bhe2e8fpa3g3.brazilsouth-01.azurewebsites.net/", timeout=30)
    print(f"Root GET Status Code: {response.status_code}")
except Exception as e:
    print(f"Root GET failed: {e}")

try:
    # Using GET first, expecting 405 or 200
    response = requests.get(url, timeout=30)
    print(f"GET Status Code: {response.status_code}")
    print(f"Response Headers: {response.headers}")
except Exception as e:
    print(f"GET failed: {e}")

try:
    # Using POST with empty data, expecting 400 or 200
    response = requests.post(url, json={}, timeout=30)
    print(f"POST Status Code: {response.status_code}")
    print(f"Response Text: {response.text[:100]}...")
except Exception as e:
    print(f"POST failed: {e}")
