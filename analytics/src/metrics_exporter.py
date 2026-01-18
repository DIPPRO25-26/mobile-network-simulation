import os
import time
import logging
import psycopg2
from prometheus_client import start_http_server, Gauge

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("exporter")

DB_HOST = os.getenv("DB_HOST", "postgres")
DB_NAME = os.getenv("DB_NAME", "mobile_network")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "admin123")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "15"))
METRICS_PORT = int(os.getenv("METRICS_PORT", "9187"))

USERS_BY_BTS = Gauge("mobile_users_by_bts", "Active users per BTS", ["bts"])
HANDOVER_TOTAL = Gauge("mobile_handover_total", "Cumulative handover count", ["from_bts", "to_bts"])
ALERTS_TOTAL = Gauge("mobile_alerts_total", "Total alerts", ["alert_type", "severity", "bts"])
ALERT_LAST_TS = Gauge("mobile_alert_last_timestamp_seconds", "Last alert timestamp (unix seconds)", ["alert_type", "severity", "bts"])
POS_X = Gauge("mobile_user_pos_x", "User X coordinate", ["imei", "bts"])
POS_Y = Gauge("mobile_user_pos_y", "User Y coordinate", ["imei", "bts"])

def db_conn():
    return psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)

def collect():
    try:
        conn = db_conn()
        cur = conn.cursor()

        cur.execute("SELECT current_bts_id, COUNT(*) FROM user_activity GROUP BY current_bts_id;")
        for bts, cnt in cur.fetchall():
            USERS_BY_BTS.labels(bts=(bts or "unknown")).set(int(cnt or 0))

        cur.execute("""
            SELECT previous_bts_id, bts_id, COUNT(*) FROM cdr_records
            WHERE previous_bts_id IS NOT NULL AND previous_bts_id <> bts_id
            GROUP BY previous_bts_id, bts_id;
        """)
        for prev_bts, to_bts, cnt in cur.fetchall():
            HANDOVER_TOTAL.labels(from_bts=(prev_bts or "unknown"), to_bts=(to_bts or "unknown")).set(int(cnt or 0))

        cur.execute("""
            SELECT alert_type, severity, bts_id, COUNT(*), MAX(EXTRACT(EPOCH FROM detected_at))
            FROM alerts GROUP BY alert_type, severity, bts_id;
        """)
        for alert_type, severity, bts, cnt, last_ts in cur.fetchall():
            ALERTS_TOTAL.labels(alert_type=(alert_type or "unknown"),
                                severity=(severity or "unknown"),
                                bts=(bts or "unknown")).set(int(cnt or 0))
            if last_ts:
                ALERT_LAST_TS.labels(alert_type=(alert_type or "unknown"),
                                     severity=(severity or "unknown"),
                                     bts=(bts or "unknown")).set(float(last_ts))

        cur.execute("""
            SELECT imei, bts_id, user_location_x, user_location_y
            FROM (
              SELECT DISTINCT ON (imei) imei, bts_id, user_location_x, user_location_y, timestamp_arrival
              FROM cdr_records
              WHERE user_location_x IS NOT NULL AND user_location_y IS NOT NULL
              ORDER BY imei, timestamp_arrival DESC
            ) s;
        """)
        for imei, bts, x, y in cur.fetchall():
            POS_X.labels(imei=(imei or "unknown"), bts=(bts or "unknown")).set(float(x or 0))
            POS_Y.labels(imei=(imei or "unknown"), bts=(bts or "unknown")).set(float(y or 0))

        cur.close()
        conn.close()
        logger.info("Collected metrics")
    except Exception:
        logger.exception("Error collecting metrics")

if __name__ == "__main__":
    start_http_server(METRICS_PORT)
    logger.info("Exporter started on port %d", METRICS_PORT)
    while True:
        collect()
        time.sleep(POLL_INTERVAL)