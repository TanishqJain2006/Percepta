from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "Backend alive", 200

@app.route("/vision-data", methods=["POST"])
def vision_data():
    data = request.get_json(force=True)
    print("VISION DATA RECEIVED:", data)
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
