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
