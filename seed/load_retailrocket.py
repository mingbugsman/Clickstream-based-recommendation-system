import os

import pandas as pd
from cassandra.cluster import Cluster
from cassandra.concurrent import execute_concurrent_with_args

CASSANDRA_HOST = os.environ.get("CASSANDRA_HOST", "127.0.0.1")
BATCH_SIZE = 2000

df = pd.read_csv("data/events.csv")
cluster = Cluster([CASSANDRA_HOST])
session = cluster.connect("recsys")

insert_stmt = session.prepare(
    "INSERT INTO events (session_id, event_time, visitor_id, item_id, event_type) VALUES (?, ?, ?, ?, ?)"
)

params = [
    (
        str(row.visitorid),  # dung visitorid lam session goc cho seed data
        pd.to_datetime(row.timestamp, unit="ms"),
        str(row.visitorid),
        str(row.itemid),
        row.event,
    )
    for row in df.itertuples()
]

total = len(params)
for start in range(0, total, BATCH_SIZE):
    chunk = params[start:start + BATCH_SIZE]
    execute_concurrent_with_args(session, insert_stmt, chunk, concurrency=20)
    print(f"seeded {min(start + BATCH_SIZE, total)}/{total}", flush=True)

print("Done seeding", total, "events")
