import requests
import time

start = time.time()
try:
    print("Sending POST request to /api/v1/login...")
    response = requests.post(
        "http://127.0.0.1:8000/api/v1/login",
        json={"email": "test@example.com", "password": "password"},
    )
    print(f"Time taken: {time.time() - start:.2f} seconds")
    print(f"Status Code: {response.status_code}")
    print(f"Body: {response.text}")
except Exception as e:
    print(f"Time taken: {time.time() - start:.2f} seconds")
    print(f"Request failed: {e}")
