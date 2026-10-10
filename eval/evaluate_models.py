import pickle
from collections import Counter

import pandas as pd
from cassandra.cluster import Cluster


def load_test_sessions(min_len=3, limit=None):
    cluster = Cluster(["127.0.0.1"])
    session = cluster.connect("recsys")
    rows = session.execute("SELECT session_id, item_id, event_time FROM events")
    df = pd.DataFrame(list(rows))
    df = df.sort_values(["session_id", "event_time"])

    sessions = []
    for _, group in df.groupby("session_id"):
        items = group["item_id"].tolist()
        if len(items) >= min_len:
            sessions.append(items)
    return sessions[:limit] if limit else sessions


def hit_rate_at_k(model_predict_fn, test_sessions, k=5):
    hits = 0
    for session in test_sessions:
        history, true_next = session[:-1], session[-1]
        preds = model_predict_fn(history, k)
        if true_next in preds:
            hits += 1
    return hits / len(test_sessions)


def mrr(model_predict_fn, test_sessions, k=20):
    scores = []
    for session in test_sessions:
        history, true_next = session[:-1], session[-1]
        preds = model_predict_fn(history, k)
        rank = preds.index(true_next) + 1 if true_next in preds else 0
        scores.append(1 / rank if rank > 0 else 0)
    return sum(scores) / len(scores)


def predict_markov(history, k):
    with open("models/markov.pkl", "rb") as f:
        matrix = pickle.load(f)
    last_item = history[-1]
    if last_item not in matrix:
        return []
    ranked = sorted(matrix[last_item].items(), key=lambda kv: kv[1], reverse=True)
    return [item for item, _ in ranked[:k]]


def predict_most_popular(history, k, popularity_ranking):
    return popularity_ranking[:k]


def build_popularity_ranking(sessions):
    counter = Counter(item for session in sessions for item in session)
    return [item for item, _ in counter.most_common()]


def main():
    test_sessions = load_test_sessions()
    popularity_ranking = build_popularity_ranking(test_sessions)

    for k in (5, 10, 20):
        hr_markov = hit_rate_at_k(predict_markov, test_sessions, k)
        hr_popular = hit_rate_at_k(
            lambda h, kk: predict_most_popular(h, kk, popularity_ranking),
            test_sessions, k,
        )
        print(f"Hit Rate@{k} - Markov: {hr_markov:.4f} | Most Popular: {hr_popular:.4f}")

    mrr_markov = mrr(predict_markov, test_sessions)
    mrr_popular = mrr(
        lambda h, kk: predict_most_popular(h, kk, popularity_ranking),
        test_sessions,
    )
    print(f"MRR - Markov: {mrr_markov:.4f} | Most Popular: {mrr_popular:.4f}")

    # GRU4Rec can load rieng models/gru4rec.pt + item2idx.pkl, bo sung ham predict_gru
    # tuong tu predict_markov khi model da train xong


if __name__ == "__main__":
    main()
