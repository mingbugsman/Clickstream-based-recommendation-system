import pandas as pd
from cassandra.cluster import Cluster
from collections import defaultdict
import pickle

cluster = Cluster(["127.0.0.1"])
session = cluster.connect("recsys")
rows = session.execute("SELECT session_id, item_id, event_time FROM events")
df = pd.DataFrame(list(rows))
df = df.sort_values(["session_id", "event_time"])

transitions = defaultdict(lambda: defaultdict(int))
for _, group in df.groupby("session_id"):
    items = group["item_id"].tolist()
    for a, b in zip(items[:-1], items[1:]):
        transitions[a][b] += 1

# chuan hoa thanh xac suat
matrix = {}
for item_i, next_counts in transitions.items():
    total = sum(next_counts.values())
    matrix[item_i] = {j: c / total for j, c in next_counts.items()}

with open("models/markov.pkl", "wb") as f:
    pickle.dump(matrix, f)

print("Markov matrix trained:", len(matrix), "items")
