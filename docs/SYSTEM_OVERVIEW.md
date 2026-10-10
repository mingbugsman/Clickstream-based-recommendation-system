# HƯỚNG DẪN XÂY DỰNG HỆ THỐNG GỢI Ý SẢN PHẨM THÔNG MINH THỜI GIAN THỰC TỪ BIG DATA
### (Step-by-step triển khai: Kafka – Spark Streaming – Markov Chain / GRU4Rec – Redis – Cassandra – React)

> Tài liệu này hướng dẫn **từng bước thực thi** để dựng được toàn bộ hệ thống từ con số 0 đến khi có demo chạy real-time. Thực hiện theo đúng thứ tự các Phase — mỗi Phase đều có mục tiêu, việc cần làm, lệnh/code mẫu, và cách kiểm tra kết quả trước khi qua Phase tiếp theo.

---

## MỤC LỤC

- [Phase 0 — Chuẩn bị môi trường](#phase-0--chuẩn-bị-môi-trường)
- [Phase 1 — Dựng hạ tầng Big Data bằng Docker Compose](#phase-1--dựng-hạ-tầng-big-data-bằng-docker-compose)
- [Phase 2 — Nạp dữ liệu nền RetailRocket vào Cassandra](#phase-2--nạp-dữ-liệu-nền-retailrocket-vào-cassandra)
- [Phase 3 — Xây website demo + client-side event tracking](#phase-3--xây-website-demo--client-side-event-tracking)
- [Phase 4 — API Endpoint nhận sự kiện và đẩy vào Kafka](#phase-4--api-endpoint-nhận-sự-kiện-và-đẩy-vào-kafka)
- [Phase 5 — Spark Structured Streaming: xử lý luồng theo phiên](#phase-5--spark-structured-streaming-xử-lý-luồng-theo-phiên)
- [Phase 6 — Huấn luyện mô hình Markov Chain](#phase-6--huấn-luyện-mô-hình-markov-chain)
- [Phase 7 — Huấn luyện mô hình GRU4Rec](#phase-7--huấn-luyện-mô-hình-gru4rec)
- [Phase 8 — Tích hợp inference vào Spark job + lưu kết quả](#phase-8--tích-hợp-inference-vào-spark-job--lưu-kết-quả)
- [Phase 9 — Hiển thị gợi ý real-time trên giao diện React](#phase-9--hiển-thị-gợi-ý-real-time-trên-giao-diện-react)
- [Phase 10 — Kiểm thử & đánh giá hệ thống](#phase-10--kiểm-thử--đánh-giá-hệ-thống)
- [Phase 11 — Đóng gói & triển khai toàn bộ hệ thống](#phase-11--đóng-gói--triển-khai-toàn-bộ-hệ-thống)
- [Checklist tổng hợp](#checklist-tổng-hợp)

---

## Phase 0 — Chuẩn bị môi trường

**Mục tiêu:** Có đủ công cụ trên máy để chạy toàn bộ pipeline (Docker, Python, Node.js).

**Việc cần làm:**

1. Cài **Docker Desktop** (bao gồm Docker Compose) — dùng để chạy Kafka, Spark, Redis, Cassandra dưới dạng container, không cần cài tay từng service.
2. Cài **Python 3.10+** và tạo virtual environment riêng cho project:
   ```bash
   python -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   pip install pyspark==3.5.0 kafka-python cassandra-driver redis pandas numpy scikit-learn torch flask flask-cors
   ```
3. Cài **Node.js 18+** (cho phần frontend React).
4. Tạo cấu trúc thư mục project:
   ```
   recsys-project/
   ├── docker-compose.yml
   ├── data/                  # chứa RetailRocket CSV
   ├── seed/                  # script nạp seed data
   ├── streaming/             # Spark Structured Streaming job
   ├── models/                # script train Markov Chain & GRU4Rec
   ├── api/                   # API Endpoint (Flask)
   ├── frontend/              # website demo React
   └── eval/                  # script đánh giá Hit Rate@K, MRR
   ```
5. Tải dataset **RetailRocket E-commerce Dataset** từ Kaggle, giải nén vào `data/` (gồm `events.csv`, `item_properties.csv`, `category_tree.csv`).

**Kiểm tra:** `docker --version`, `python --version`, `node --version` chạy được không lỗi.

---

## Phase 1 — Dựng hạ tầng Big Data bằng Docker Compose

**Mục tiêu:** Có Kafka, Spark, Redis, Cassandra chạy sẵn trong container, giao tiếp được với nhau.

**Việc cần làm:**

1. Tạo `docker-compose.yml` ở gốc project:

```yaml
version: "3.8"
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    depends_on: [zookeeper]
    ports: ["9092:9092"]
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1

  cassandra:
    image: cassandra:4.1
    ports: ["9042:9042"]
    environment:
      CASSANDRA_CLUSTER_NAME: recsys_cluster

  redis:
    image: redis:7
    ports: ["6379:6379"]

  spark-master:
    image: bitnami/spark:3.5
    environment:
      - SPARK_MODE=master
    ports: ["8080:8080", "7077:7077"]

  spark-worker:
    image: bitnami/spark:3.5
    depends_on: [spark-master]
    environment:
      - SPARK_MODE=worker
      - SPARK_MASTER_URL=spark://spark-master:7077
```

2. Khởi động toàn bộ:
   ```bash
   docker compose up -d
   docker compose ps          # kiểm tra tất cả container đang "healthy"/"running"
   ```
3. Tạo Kafka topic `clickstream-events` với partition theo `session_id`:
   ```bash
   docker exec -it <kafka_container> kafka-topics --create \
     --topic clickstream-events --bootstrap-server localhost:9092 \
     --partitions 3 --replication-factor 1
   ```
4. Kiểm tra Cassandra kết nối được:
   ```bash
   docker exec -it <cassandra_container> cqlsh
   ```

**Kiểm tra:** `docker compose ps` toàn bộ `Up`; Spark UI mở được tại `http://localhost:8080`; `cqlsh` vào được Cassandra.

---

## Phase 2 — Nạp dữ liệu nền RetailRocket vào Cassandra

**Mục tiêu:** Có dữ liệu lịch sử (seed data) trong Cassandra để Markov Chain/GRU4Rec có dữ liệu train ban đầu, đúng tinh thần "Big Data" (có khối lượng dữ liệu từ trước khi hệ thống thật sự vận hành).

**Việc cần làm:**

1. Tạo keyspace + table trong Cassandra (`seed/schema.cql`):
   ```sql
   CREATE KEYSPACE IF NOT EXISTS recsys
     WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

   CREATE TABLE IF NOT EXISTS recsys.events (
     session_id   text,
     event_time   timestamp,
     visitor_id   text,
     item_id      text,
     event_type   text,
     PRIMARY KEY (session_id, event_time)
   );
   ```
   Chạy: `cqlsh -f seed/schema.cql`

2. Viết script Python nạp `events.csv` của RetailRocket vào bảng trên (`seed/load_retailrocket.py`):
   ```python
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
           str(row["visitorid"]),           # dùng visitorid làm session gốc cho seed data
           pd.to_datetime(row["timestamp"], unit="ms"),
           str(row["visitorid"]),
           str(row["itemid"]),
           row["event"],
       ))
   print("Done seeding", len(df), "events")
   ```
   Chạy: `python seed/load_retailrocket.py`

**Kiểm tra:** `SELECT COUNT(*) FROM recsys.events;` trong `cqlsh` trả về số dòng gần bằng số dòng của `events.csv`.

---

## Phase 3 — Xây website demo + client-side event tracking

**Mục tiêu:** Có một website demo tối giản (danh sách sản phẩm, trang chi tiết, nút "Thêm vào giỏ") để người dùng thật tương tác, và mọi tương tác đó được ghi lại thành sự kiện gửi lên hệ thống.

**Việc cần làm:**

1. Khởi tạo project React:
   ```bash
   npx create-react-app frontend
   cd frontend
   npm install axios uuid
   ```
2. Tạo `session_id` khi người dùng vào web (lưu `localStorage`), viết hàm `trackEvent()` dùng chung:
   ```javascript
   // src/tracking.js
   import { v4 as uuidv4 } from "uuid";
   import axios from "axios";

   function getSessionId() {
     let sid = localStorage.getItem("session_id");
     if (!sid) {
       sid = uuidv4();
       localStorage.setItem("session_id", sid);
     }
     return sid;
   }

   export function trackEvent(itemId, eventType) {
     const payload = {
       session_id: getSessionId(),
       item_id: itemId,
       event_type: eventType,      // "view" | "addtocart"
       timestamp: Date.now(),
     };
     axios.post("http://localhost:5000/api/track", payload).catch(() => {});
   }
   ```
3. Gọi `trackEvent()` ở các điểm tương tác: khi mở trang chi tiết sản phẩm (`view`), khi bấm "Thêm vào giỏ" (`addtocart`).
4. Tạo component hiển thị danh sách gợi ý (sẽ nối API ở Phase 9), đặt sẵn khung UI (ví dụ `<RecommendationPanel sessionId={...} />`).

**Kiểm tra:** Mở DevTools → tab Network, thao tác trên web thấy các request `POST /api/track` được gửi đi (API chưa chạy sẽ lỗi — là bình thường ở bước này).

---

## Phase 4 — API Endpoint nhận sự kiện và đẩy vào Kafka

**Mục tiêu:** Có một dịch vụ trung gian nhận sự kiện HTTP từ website rồi đẩy vào Kafka topic `clickstream-events`.

**Việc cần làm:**

1. Viết API bằng Flask (`api/app.py`):
   ```python
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
           key=event["session_id"],     # key = session_id → đảm bảo cùng phiên vào cùng partition
           value=event,
       )
       return jsonify({"status": "ok"}), 200

   if __name__ == "__main__":
       app.run(port=5000, debug=True)
   ```
2. Chạy API: `python api/app.py`
3. Quay lại Phase 3, thao tác trên website demo.

**Kiểm tra:** Dùng Kafka console consumer để xem sự kiện có chảy vào topic không:
```bash
docker exec -it <kafka_container> kafka-console-consumer \
  --topic clickstream-events --bootstrap-server localhost:9092 --from-beginning
```
Thấy JSON sự kiện hiện ra mỗi khi click trên web → Phase 4 thành công.

---

## Phase 5 — Spark Structured Streaming: xử lý luồng theo phiên

**Mục tiêu:** Đọc liên tục từ Kafka, nhóm sự kiện theo `session_id`, duy trì trạng thái phiên qua nhiều micro-batch, trích xuất đặc trưng hành vi.

**Việc cần làm:**

1. Viết job Spark (`streaming/session_job.py`):
   ```python
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
   ```
2. Dùng `mapGroupsWithState` (qua `applyInPandasWithState` hoặc Scala API) để tích lũy danh sách `item_id` đã xem trong phiên hiện tại, cập nhật mỗi khi có event mới — đây là bước trích xuất "ngữ cảnh phiên" dùng cho cả Markov Chain và GRU4Rec ở Phase 8.
3. Ghi tạm kết quả ra console để kiểm tra luồng chạy đúng trước khi nối model:
   ```python
   query = events.writeStream.format("console").outputMode("append").start()
   query.awaitTermination()
   ```
4. Chạy job: `spark-submit streaming/session_job.py`

**Kiểm tra:** Thao tác trên website, thấy console của Spark job in ra từng sự kiện gần như ngay lập tức (độ trễ vài giây theo micro-batch).

---

## Phase 6 — Huấn luyện mô hình Markov Chain

**Mục tiêu:** Có mô hình baseline, suy luận cực nhanh (tra bảng), dùng ma trận xác suất chuyển tiếp giữa các sản phẩm.

**Việc cần làm:**

1. Viết script train (`models/train_markov.py`) đọc toàn bộ lịch sử từ Cassandra, xây ma trận chuyển tiếp P(item_j | item_i):
   ```python
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

   # Chuẩn hóa thành xác suất
   matrix = {}
   for item_i, next_counts in transitions.items():
       total = sum(next_counts.values())
       matrix[item_i] = {j: c / total for j, c in next_counts.items()}

   with open("models/markov.pkl", "wb") as f:
       pickle.dump(matrix, f)
   print("Markov matrix trained:", len(matrix), "items")
   ```
2. Chạy: `python models/train_markov.py`

**Kiểm tra:** File `models/markov.pkl` được tạo; thử tra `matrix["<item_id>"]` trả về danh sách item kế tiếp kèm xác suất, sắp theo top-K.

---

## Phase 7 — Huấn luyện mô hình GRU4Rec

**Mục tiêu:** Có mô hình nâng cao, ghi nhớ ngữ cảnh toàn phiên (không chỉ 1 bước gần nhất như Markov Chain), dùng mạng GRU.

**Việc cần làm:**

1. Chuẩn bị dữ liệu dạng chuỗi session từ Cassandra (giống bước 1 Phase 6, nhưng giữ nguyên dạng sequence, không rút gọn thành transition).
2. Viết model GRU4Rec bằng PyTorch (`models/gru4rec.py`):
   ```python
   import torch
   import torch.nn as nn

   class GRU4Rec(nn.Module):
       def __init__(self, n_items, embed_dim=64, hidden_dim=100):
           super().__init__()
           self.embedding = nn.Embedding(n_items, embed_dim, padding_idx=0)
           self.gru = nn.GRU(embed_dim, hidden_dim, batch_first=True)
           self.output = nn.Linear(hidden_dim, n_items)

       def forward(self, item_seq):
           x = self.embedding(item_seq)
           _, h = self.gru(x)
           return self.output(h.squeeze(0))
   ```
3. Viết training loop (`models/train_gru4rec.py`): chuyển item_id → index, pad sequence theo session, train bằng cross-entropy loss (dự đoán item tiếp theo), nên chạy trên **Google Colab (GPU)** nếu máy cá nhân không có GPU.
4. Lưu model: `torch.save(model.state_dict(), "models/gru4rec.pt")`, đồng thời lưu `item2idx.pkl` để ánh xạ ngược khi inference.

**Kiểm tra:** Loss giảm dần qua các epoch; thử inference thủ công trên một chuỗi session mẫu, xem top-K sản phẩm được dự đoán có hợp lý không (so với dữ liệu thật).

---

## Phase 8 — Tích hợp inference vào Spark job + lưu kết quả

**Mục tiêu:** Mỗi khi có sự kiện mới, Spark job gọi cả 2 mô hình (đã train offline) để suy luận top-K gợi ý, rồi lưu kết quả vào Redis (tạm thời, phục vụ hiển thị real-time) và Cassandra (lâu dài, phục vụ retrain/đánh giá).

**Việc cần làm:**

1. Trong `streaming/session_job.py`, load 2 model đã train (`markov.pkl`, `gru4rec.pt`) **một lần** khi khởi động job (không load lại mỗi batch).
2. Sau bước trích xuất ngữ cảnh phiên (Phase 5), thêm hàm inference chạy trên mỗi micro-batch (dùng `foreachBatch`):
   ```python
   import redis
   r = redis.Redis(host="localhost", port=6379, decode_responses=True)

   def process_batch(batch_df, batch_id):
       rows = batch_df.collect()
       for row in rows:
           last_item = row["last_item_id"]
           topk_markov = get_topk_markov(last_item, k=5)       # tra bảng từ markov.pkl
           topk_gru = get_topk_gru(row["session_items"], k=5)  # inference GRU4Rec
           r.set(f"reco:{row['session_id']}", json.dumps({
               "markov": topk_markov, "gru4rec": topk_gru
           }), ex=1800)  # TTL 30 phút
           save_to_cassandra(row["session_id"], topk_markov, topk_gru)

   events.writeStream.foreachBatch(process_batch).start().awaitTermination()
   ```
3. Viết `save_to_cassandra()` ghi kết quả gợi ý vào bảng `recsys.recommendations` (tạo thêm bảng này trong `seed/schema.cql`).

**Kiểm tra:** Thao tác trên website, dùng `redis-cli GET reco:<session_id>` thấy JSON kết quả gợi ý cập nhật theo thời gian thực.

---

## Phase 9 — Hiển thị gợi ý real-time trên giao diện React

**Mục tiêu:** Người dùng thấy danh sách gợi ý cập nhật ngay trên demo site sau mỗi hành động.

**Việc cần làm:**

1. Thêm API đọc Redis (`api/app.py`):
   ```python
   @app.route("/api/recommend/<session_id>", methods=["GET"])
   def recommend(session_id):
       data = r.get(f"reco:{session_id}")
       return jsonify(json.loads(data)) if data else jsonify({"markov": [], "gru4rec": []})
   ```
2. Trong component `RecommendationPanel`, poll API mỗi 2–3 giây (hoặc nối WebSocket nếu muốn nâng cao hơn):
   ```javascript
   useEffect(() => {
     const interval = setInterval(async () => {
       const res = await axios.get(`http://localhost:5000/api/recommend/${sessionId}`);
       setRecommendations(res.data);
     }, 2000);
     return () => clearInterval(interval);
   }, [sessionId]);
   ```
3. Cho phép người dùng demo chọn xem gợi ý từ Markov Chain hay GRU4Rec để so sánh trực tiếp (dropdown hoặc tab).

**Kiểm tra:** Click xem vài sản phẩm liên tiếp trên demo site → panel gợi ý tự cập nhật sau 1–2 giây, không cần tải lại trang.

---

## Phase 10 — Kiểm thử & đánh giá hệ thống

**Mục tiêu:** Có số liệu định lượng để so sánh 2 mô hình và chứng minh hệ thống đáp ứng yêu cầu real-time.

**Việc cần làm:**

1. **Đánh giá chất lượng mô hình** (`eval/evaluate_models.py`): dùng kỹ thuật "last-item masking" — với mỗi session test, ẩn item cuối cùng, cho model dự đoán, kiểm tra item thật có nằm trong top-K không:
   ```python
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
   ```
2. So sánh **Markov Chain vs GRU4Rec vs baseline "Most Popular"** trên cùng tập test, ghi kết quả thành bảng/biểu đồ.
3. **Đo hiệu năng hệ thống**: viết script bắn tải (giả lập nhiều session gửi event liên tục, ví dụ dùng `locust` hoặc script Python đa luồng) để đo:
   - **Latency**: thời gian từ lúc event được gửi đến lúc Redis có kết quả gợi ý.
   - **Throughput**: số event/giây hệ thống xử lý được trước khi bắt đầu tích tụ trễ (consumer lag tăng).
4. Tổ chức **nhóm người dùng thử nghiệm thật** (khoảng 20–50 người quen, dùng ẩn danh, chỉ lưu `session_id` ngẫu nhiên, không thu thập thông tin cá nhân) dùng demo site trong 1–2 tuần để sinh dữ liệu hành vi thật, bổ sung cho seed data RetailRocket.

**Kiểm tra:** Có bảng số liệu Hit Rate@K / MRR cho cả 3 phương pháp; có số liệu latency (ms) và throughput (events/s) ghi nhận được từ script bắn tải.

---

## Phase 11 — Đóng gói & triển khai toàn bộ hệ thống

**Mục tiêu:** Toàn bộ hệ thống (Kafka, Spark, Redis, Cassandra, API, frontend) chạy được bằng một lệnh duy nhất, dễ demo trước hội đồng.

**Việc cần làm:**

1. Viết `Dockerfile` cho `api/` và `frontend/`.
2. Bổ sung 2 service này vào `docker-compose.yml` chung (API nối tới Kafka/Redis/Cassandra qua tên service nội bộ, ví dụ `kafka:29092` thay vì `localhost:9092`).
3. Thêm service chạy Spark job dưới dạng container riêng, submit job tự động khi container start (`spark-submit` trong `CMD` của Dockerfile).
4. Kiểm tra toàn bộ hệ thống khởi động sạch từ đầu:
   ```bash
   docker compose down -v      # xoá toàn bộ dữ liệu cũ, test từ trạng thái sạch
   docker compose up --build
   ```
5. Viết lại `seed/load_retailrocket.py` thành bước chạy tự động (hoặc ghi rõ trong README) để người chấm có thể tái lập toàn bộ pipeline từ đầu.

**Kiểm tra:** Chạy `docker compose up --build` trên máy khác (hoặc máy sạch) → toàn bộ hệ thống lên được, website demo truy cập được, gợi ý hiển thị đúng như khi chạy thủ công.

---

## Checklist tổng hợp

| Phase | Nội dung | Trạng thái |
|-------|----------|------------|
| 0 | Cài Docker, Python, Node.js, tạo cấu trúc project | ☐ |
| 1 | Docker Compose: Kafka, Zookeeper, Spark, Redis, Cassandra | ☐ |
| 2 | Nạp RetailRocket seed data vào Cassandra | ☐ |
| 3 | Website demo React + client-side tracking | ☐ |
| 4 | API Endpoint nhận sự kiện → Kafka | ☐ |
| 5 | Spark Structured Streaming xử lý theo session | ☐ |
| 6 | Train Markov Chain | ☐ |
| 7 | Train GRU4Rec | ☐ |
| 8 | Tích hợp inference + lưu Redis/Cassandra | ☐ |
| 9 | Hiển thị gợi ý real-time trên React | ☐ |
| 10 | Đánh giá Hit Rate@K, MRR, latency, throughput | ☐ |
| 11 | Đóng gói Docker Compose, triển khai hoàn chỉnh | ☐ |

---

*Tài liệu hướng dẫn triển khai — Đề tài: Xây dựng hệ thống gợi ý sản phẩm thông minh thời gian thực từ Big Data*
