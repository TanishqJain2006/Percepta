from ultralytics import YOLO

model = YOLO("yolov8n.pt")  # lightweight & fast

ALLOWED_CLASSES = [
    "person", "car", "bus", "truck",
    "chair", "door", "stairs"
]

def detect_objects(frame):
    results = model(frame, verbose=False)[0]
    detections = []

    for box in results.boxes:
        cls_id = int(box.cls[0])
        label = model.names[cls_id]
        confidence = float(box.conf[0])

        if label in ALLOWED_CLASSES:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            detections.append({
                "label": label,
                "confidence": round(confidence, 2),
                "bbox": [x1, y1, x2, y2]
            })

    return detections
