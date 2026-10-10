from flask import Flask, request, jsonify
from flask_cors import CORS
from kafka import KafkaProducer
import json
import redis

app = Flask(__name__)
CORS(app)

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    key_serializer=lambda k: k.encode("utf-8"),
)

r = redis.Redis(host="localhost", port=6379, decode_responses=True)


@app.route("/api/track", methods=["POST"])
def track():
    event = request.get_json()
    producer.send(
        "clickstream-events",
        key=event["session_id"],  # key = session_id -> dam bao cung phien vao cung partition
        value=event,
    )
    return jsonify({"status": "ok"}), 200


@app.route("/api/recommend/<session_id>", methods=["GET"])
def recommend(session_id):
    data = r.get(f"reco:{session_id}")
    return jsonify(json.loads(data)) if data else jsonify({"markov": [], "gru4rec": []})


if __name__ == "__main__":
    app.run(port=5000, debug=True)
