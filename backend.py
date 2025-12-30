from flask import Flask, request, jsonify
import time

app = Flask(__name__)

# ---------------- PRIORITY & TEMPLATES ----------------

PRIORITY = {
    "stairs": 1,
    "vehicle": 2,
    "person": 3,
    "door": 4,
    "chair": 5
}

TEMPLATES = {
    "stairs": "Stairs ahead. Please step carefully.",
    "vehicle": "Vehicle approaching. Move with caution.",
    "person": "A person is in front of you.",
    "door": "A door is ahead.",
    "chair": "There is a chair nearby."
}

CONFIDENCE_THRESHOLD = 0.6
DISTANCE_THRESHOLD = 3.0
SPEAK_COOLDOWN = 3  # seconds

last_spoken_text = ""
last_spoken_time = 0

# ---------------- ROUTES ----------------

@app.route("/", methods=["GET"])
def home():
    return "Percepta backend alive", 200


@app.route("/vision-data", methods=["POST"])
def vision_data():
    global last_spoken_text, last_spoken_time

    data = request.get_json(force=True)
    detections = data.get("detections", [])

    # -------- FILTER DETECTIONS --------
    valid = []
    for d in detections:
        if (
            d.get("confidence", 0) >= CONFIDENCE_THRESHOLD
            and d.get("distance", 99) <= DISTANCE_THRESHOLD
        ):
            valid.append(d)

    if not valid:
        return jsonify({"narration": ""}), 200

    # -------- PRIORITY SORT --------
    valid.sort(
        key=lambda d: (
            PRIORITY.get(d.get("label"), 99),
            d.get("distance")
        )
    )

    top = valid[0]
    narration = TEMPLATES.get(top["label"], "")

    # -------- SPEECH CONTROL --------
    now = time.time()

    if narration == last_spoken_text and (now - last_spoken_time) < SPEAK_COOLDOWN:
        narration = ""
    else:
        last_spoken_text = narration
        last_spoken_time = now

    return jsonify({
        "narration": narration,
        "object": top["label"]
    }), 200


# ---------------- MAIN ----------------

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
