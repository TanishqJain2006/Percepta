import requests

BACKEND_URL = "http://127.0.0.1:5000/update"

def send_to_backend(payload):
    try:
        requests.post(BACKEND_URL, json=payload, timeout=0.5)
    except requests.exceptions.ConnectionError:
        # Backend not running – ignore during local testing
        pass
    except Exception as e:
        print("[WARN] Backend error:", e)
