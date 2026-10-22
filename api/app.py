from flask import Flask, request, jsonify
from flask_cors import CORS
from kafka import KafkaProducer
import json
import os
import redis

import catalog

app = Flask(__name__)
CORS(app)

KAFKA_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    key_serializer=lambda k: k.encode("utf-8"),
)

r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)


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


@app.route("/api/products", methods=["GET"])
def list_products():
    cursor = int(request.args.get("cursor", 0))
    limit = min(int(request.args.get("limit", 24)), 100)
    category_id = request.args.get("category")
    return jsonify(catalog.list_products(cursor=cursor, limit=limit, category_id=category_id))


@app.route("/api/products/<item_id>", methods=["GET"])
def get_product(item_id):
    product = catalog.get_product(item_id)
    if product is None:
        return jsonify({"error": "not_found"}), 404
    return jsonify(product)


@app.route("/api/products/batch", methods=["POST"])
def get_products_batch():
    item_ids = request.get_json().get("item_ids", [])
    return jsonify(catalog.get_products_batch(item_ids))


@app.route("/api/categories", methods=["GET"])
def list_categories():
    return jsonify(catalog.list_categories())


if __name__ == "__main__":
    catalog.load_catalog()
    app.run(host="0.0.0.0", port=5000, debug=True)
