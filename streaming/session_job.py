import json
import os

import redis
from cassandra.cluster import Cluster
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StringType, LongType

from inference import get_topk_markov, get_topk_gru, load_models

spark = SparkSession.builder \
    .appName("ClickstreamSessionProcessor") \
    .config("spark.jars.packages",
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
    .getOrCreate()

schema = StructType() \
    .add("session_id", StringType()) \
    .add("item_id", StringType()) \
    .add("event_type", StringType()) \
    .add("timestamp", LongType())

KAFKA_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
CASSANDRA_HOST = os.environ.get("CASSANDRA_HOST", "127.0.0.1")
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")

raw = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP) \
    .option("subscribe", "clickstream-events") \
    .option("startingOffsets", "latest") \
    .load()

events = raw.select(from_json(col("value").cast("string"), schema).alias("data")).select("data.*")

# giu lai toi da 20 item gan nhat cho moi session, luu truc tiep trong Redis
# (Redis da la state store cua he thong nen khong can mapGroupsWithState rieng)
MAX_SESSION_ITEMS = 20

# load model markov + gru4rec mot lan duy nhat khi worker khoi dong, khong load lai moi batch
load_models()

redis_client = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)
cassandra_session = Cluster([CASSANDRA_HOST]).connect("recsys")
save_reco_stmt = cassandra_session.prepare(
    "INSERT INTO recommendations (session_id, updated_at, markov, gru4rec) VALUES (?, toTimestamp(now()), ?, ?)"
)


def process_batch(batch_df, batch_id):
    rows = batch_df.collect()
    for row in rows:
        session_key = f"session_items:{row.session_id}"
        redis_client.rpush(session_key, row.item_id)
        redis_client.ltrim(session_key, -MAX_SESSION_ITEMS, -1)
        redis_client.expire(session_key, 1800)
        session_items = redis_client.lrange(session_key, 0, -1)

        topk_markov = get_topk_markov(row.item_id, k=5)
        topk_gru = get_topk_gru(session_items, k=5)

        redis_client.set(
            f"reco:{row.session_id}",
            json.dumps({"markov": topk_markov, "gru4rec": topk_gru}),
            ex=1800,  # TTL 30 phut
        )

        cassandra_session.execute(save_reco_stmt, (
            row.session_id,
            json.dumps(topk_markov),
            json.dumps(topk_gru),
        ))


if __name__ == "__main__":
    query = events.writeStream.foreachBatch(process_batch).start()
    query.awaitTermination()
