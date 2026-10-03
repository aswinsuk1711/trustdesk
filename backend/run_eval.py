import json
import os
import httpx

BASE = "http://localhost:8000/api"

username = os.getenv("EVAL_USER", "testuser")
password = os.getenv("EVAL_PASS", "Test@1234")

login = httpx.post(f"{BASE}/auth/login", json={"username": username, "password": password})
login.raise_for_status()
token = login.json()["access_token"]

headers = {"Authorization": f"Bearer {token}"}
response = httpx.post(f"{BASE}/evaluations/run", headers=headers, timeout=60)
response.raise_for_status()
print(json.dumps(response.json(), indent=2))
