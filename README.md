# Clickstream-based recommendation system

He thong goi y san pham thoi gian thuc tu du lieu clickstream. Chi tiet thiet ke va cac buoc trien khai nam trong `docs/SYSTEM_OVERVIEW.md`.

## Chay toan bo he thong

1. Tai dataset RetailRocket tu Kaggle, giai nen `events.csv` vao thu muc `data/`.
2. Build va chay toan bo service:
   ```bash
   docker compose up --build
   ```
3. Tao Kafka topic (chi can lam mot lan):
   ```bash
   docker exec -it <kafka_container> kafka-topics --create \
     --topic clickstream-events --bootstrap-server localhost:9092 \
     --partitions 3 --replication-factor 1
   ```
4. Tao schema va nap seed data vao Cassandra:
   ```bash
   docker exec -it <cassandra_container> cqlsh -f /seed/schema.cql
   python seed/load_retailrocket.py
   ```
5. Train model (chay local, can activate venv va cai `requirements.txt`):
   ```bash
   python models/train_markov.py
   python models/train_gru4rec.py
   ```
6. Mo website demo tai `http://localhost:3000`.

## Danh gia

```bash
python eval/evaluate_models.py
python eval/load_test.py
```
