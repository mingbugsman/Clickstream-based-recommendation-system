import time
import uuid
import random
import threading

import requests
import redis

API_URL = "http://localhost:5000/api/track"
NUM_SESSIONS = 20
EVENTS_PER_SESSION = 10
SAMPLE_ITEM_IDS = [str(i) for i in range(1000, 1050)]

r = redis.Redis(host="localhost", port=6379, decode_responses=True)
latencies = []
lock = threading.Lock()


def run_session():
    session_id = str(uuid.uuid4())
    for _ in range(EVENTS_PER_SESSION):
        item_id = random.choice(SAMPLE_ITEM_IDS)
        sent_at = time.time()

        requests.post(API_URL, json={
            "session_id": session_id,
            "item_id": item_id,
            "event_type": "view",
            "timestamp": int(sent_at * 1000),
        })

        # cho spark job xu ly va ghi ket qua vao redis, poll toi da 5s
        deadline = sent_at + 5
        while time.time() < deadline:
            if r.get(f"reco:{session_id}"):
                with lock:
                    latencies.append(time.time() - sent_at)
                break
            time.sleep(0.1)


def main():
    start = time.time()
    threads = [threading.Thread(target=run_session) for _ in range(NUM_SESSIONS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    duration = time.time() - start

    total_events = NUM_SESSIONS * EVENTS_PER_SESSION
    print(f"Tong so event gui: {total_events}")
    print(f"Thoi gian chay: {duration:.2f}s")
    print(f"Throughput: {total_events / duration:.2f} event/s")

    if latencies:
        avg_latency = sum(latencies) / len(latencies)
        print(f"So event co ket qua goi y: {len(latencies)}/{total_events}")
        print(f"Latency trung binh: {avg_latency * 1000:.0f}ms")
    else:
        print("Khong ghi nhan duoc latency nao, kiem tra lai pipeline Spark job.")


if __name__ == "__main__":
    main()
