import requests
import json

try:
    response = requests.post(
        "http://127.0.0.1:8000/api/v1/login",
        json={"email": "test@example.com", "password": "password"},
        timeout=10
    )
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {response.headers}")
    print(f"Body: {response.text}")
except Exception as e:
    print(f"Request failed: {e}")
