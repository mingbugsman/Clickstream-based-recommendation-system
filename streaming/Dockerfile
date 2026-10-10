FROM bitnami/spark:3.5

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY streaming/ ./streaming/
COPY models/ ./models/

CMD ["spark-submit", \
     "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0", \
     "streaming/session_job.py"]
