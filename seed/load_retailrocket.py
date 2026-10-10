import pandas as pd
from cassandra.cluster import Cluster

df = pd.read_csv("data/events.csv")
cluster = Cluster(["127.0.0.1"])
session = cluster.connect("recsys")

insert_stmt = session.prepare(
    "INSERT INTO events (session_id, event_time, visitor_id, item_id, event_type) VALUES (?, ?, ?, ?, ?)"
)

for _, row in df.iterrows():
    session.execute(insert_stmt, (
        str(row["visitorid"]),       # dung visitorid lam session goc cho seed data
        pd.to_datetime(row["timestamp"], unit="ms"),
        str(row["visitorid"]),
        str(row["itemid"]),
        row["event"],
    ))

print("Done seeding", len(df), "events")
