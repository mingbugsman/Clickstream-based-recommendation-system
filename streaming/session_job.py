import json
import pickle

import redis
from cassandra.cluster import Cluster
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StringType, LongType, ArrayType

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

raw = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "clickstream-events") \
    .option("startingOffsets", "latest") \
    .load()

events = raw.select(from_json(col("value").cast("string"), schema).alias("data")).select("data.*")

# tich luy danh sach item_id da xem trong phien hien tai bang groupByKey + flatMapGroupsWithState
# giu lai toi da 20 item gan nhat cho moi session
MAX_SESSION_ITEMS = 20


def update_session_state(session_id, rows, state):
    items = list(state.getOption()) if state.exists else []
    for row in rows:
        items.append(row.item_id)
    items = items[-MAX_SESSION_ITEMS:]
    state.update(items)
    return [(session_id, items[-1], items)]


state_schema = ArrayType(StringType())

sessions = events.groupBy("session_id").applyInPandasWithState(
    func=update_session_state,
    outputStructType="session_id string, last_item_id string, session_items array<string>",
    stateStructType=state_schema,
    outputMode="update",
    timeoutConf="NoTimeout",
)

# load model markov + gru4rec mot lan duy nhat khi worker khoi dong, khong load lai moi batch
load_models()

redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)
cassandra_session = Cluster(["127.0.0.1"]).connect("recsys")
save_reco_stmt = cassandra_session.prepare(
    "INSERT INTO recommendations (session_id, updated_at, markov, gru4rec) VALUES (?, toTimestamp(now()), ?, ?)"
)


def process_batch(batch_df, batch_id):
    rows = batch_df.collect()
    for row in rows:
        topk_markov = get_topk_markov(row.last_item_id, k=5)
        topk_gru = get_topk_gru(row.session_items, k=5)

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
    query = sessions.writeStream.foreachBatch(process_batch).start()
    query.awaitTermination()
