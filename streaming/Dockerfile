FROM bitnamilegacy/spark:3.5.6

USER root
WORKDIR /app

COPY streaming/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY streaming/ ./streaming/
COPY models/ ./models/

CMD ["spark-submit", \
     "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0", \
     "streaming/session_job.py"]
