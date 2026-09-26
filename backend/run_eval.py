import json
import httpx

response = httpx.post("http://localhost:8000/api/evaluations/run", timeout=60)
response.raise_for_status()
print(json.dumps(response.json(), indent=2))
