from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StringType, LongType

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

# TODO Phase 8: tich luy item_id theo session (mapGroupsWithState) truoc khi goi inference

if __name__ == "__main__":
    query = events.writeStream.format("console").outputMode("append").start()
    query.awaitTermination()
