from flask import Flask, request, jsonify
from flask_cors import CORS
from kafka import KafkaProducer
import json

app = Flask(__name__)
CORS(app)

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    key_serializer=lambda k: k.encode("utf-8"),
)


@app.route("/api/track", methods=["POST"])
def track():
    event = request.get_json()
    producer.send(
        "clickstream-events",
        key=event["session_id"],  # key = session_id -> dam bao cung phien vao cung partition
        value=event,
    )
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(port=5000, debug=True)
