import requests

BACKEND_URL = "http://127.0.0.1:5000/vision-data"

def send_to_backend(payload):
    try:
        r = requests.post(BACKEND_URL, json=payload, timeout=3)
        print("Sent →", r.status_code)
    except Exception as e:
        print("Send skipped:", repr(e))
