import requests 

API_URL = "https://cu-grant-analyzis-project.onrender.com"


def api_health() -> bool:
    try:
        r = requests.get(f"{API_URL}/health", timeout=10)
        return r.status_code == 200
    except Exception:
        return False

print(api_health())