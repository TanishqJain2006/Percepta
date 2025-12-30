import requests

test_data = {
    "detections": [
        {"label": "chair", "confidence": 0.8, "distance": 1.2},
        {"label": "person", "confidence": 0.85, "distance": 2.0},
        {"label": "stairs", "confidence": 0.92, "distance": 1.5}
    ]
}

res = requests.post(
    "http://127.0.0.1:5000/vision-data",
    json=test_data
)

print(res.json())
