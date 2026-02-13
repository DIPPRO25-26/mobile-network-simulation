import psycopg2
import sys
import os
import logging
import time
import datetime

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "15"))
DB_HOST = os.getenv("DB_HOST", "admin")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "admin123")

flapping_query = """
SELECT * FROM cdr_records WHERE timestamp_arrival >= %s 
ORDER BY imei, timestamp_arrival ASC; 
"""
speed_query = """
SELECT * FROM cdr_records WHERE created_at >= '%s' AND speed > 200;
"""
overload_query = """
SELECT * FROM bts_registry WHERE updated_at >= '%s' AND current_load > 50;
"""
col_names_query = """
SELECT column_name
FROM information_schema.columns
WHERE table_name = '%s';
"""
alerts_insert = """
INSERT INTO alerts (alert_type, severity, imei, bts_id, description, detected_at)
VALUES (%s, %s, %s, %s, %s, %s);
"""

def generate_alert(alert_type, severity, imei, bts_id, description):
    alert = (alert_type, severity, imei, bts_id, description, datetime.datetime.now())
    logger.debug(f"alert generated: {alert}")
    return alert

def fetch_data(cursor, query, time_cutoff):
    cursor.execute(query % time_cutoff)
    data = cursor.fetchall()
    return data

def clear_old_flapping_alerts(recent_flapping):
    now_minus_1h = datetime.datetime.now() - datetime.timedelta(hours=1)
    culled_flapping_list = [x for x in recent_flapping if x["detected_at"] > now_minus_1h]
    return culled_flapping_list

# flapping: korisnik se prebacuje izmedju 2 BTS-a >5 puta/h
def check_flapping(cursor, flapping_query, column_names, recent_flapping):
    idx_imei = column_names.index('imei')
    idx_bts = column_names.index('bts_id')
    idx_prev_bts = column_names.index('previous_bts_id') 

    cursor.execute(flapping_query, (datetime.datetime.now() - datetime.timedelta(hours=1),))
    data = cursor.fetchall()

    imei_grouped_entries = {}
    
    for row in data:
        imei = row[idx_imei]
        bts_id = row[idx_bts]
        previous_bts_id = row[idx_prev_bts]
        if bts_id == previous_bts_id:
            continue
        if imei not in imei_grouped_entries:
            imei_grouped_entries[imei] = []
        imei_grouped_entries[imei].append((previous_bts_id, bts_id))
    
    new_flapping = []
    
    for imei, transitions in imei_grouped_entries.items():
        if len(transitions) <= 5:
            continue
            
        current_chain = []
        
        for i in range(len(transitions)):
            curr_prev, curr_curr = transitions[i]
            
            if not current_chain:
                current_chain.append(curr_prev)
                current_chain.append(curr_curr)
                continue
                
            last_bts = current_chain[-1]
            second_to_last = current_chain[-2]
            
            if curr_prev == last_bts and curr_curr == second_to_last:
                current_chain.append(curr_curr)
            else:
                if len(current_chain) > 6:
                    new_flapping.append((imei, tuple(current_chain)))
                current_chain = [curr_prev, curr_curr]

        if len(current_chain) > 6:
            new_flapping.append((imei, tuple(current_chain)))

    alerts = []
    recent_flapping_info = {x["info"] for x in recent_flapping}
    for flap in new_flapping:
        imei, chain = flap
        if flap not in recent_flapping_info:
            alert = generate_alert(
                'flapping', 'medium',
                imei, chain[0],
                f"Flapping between {chain[0]} and {chain[1]} {len(chain)-1} times"
            )
            recent_flapping.append({
                "info": flap, 
                "detected_at": datetime.datetime.now()
            })
            alerts.append(alert)
    return alerts

# abnormal speed: >200km/h
def check_abnormal_speed(cursor, speed_query, column_names):
    data = fetch_data(cursor, speed_query, datetime.datetime.now() - datetime.timedelta(seconds=POLL_INTERVAL))
    alerts = []
    for row in data:
        imei = row[column_names.index('imei')]
        bts_id = row[column_names.index('bts_id')]
        alerts.append(generate_alert('abnormal speed', 'low', imei, bts_id, "Speed above 200km/h"))
    return alerts

# overload: current load >50
def check_overload(cursor, overload_query, column_names):
    data = fetch_data(cursor, overload_query, datetime.datetime.now() - datetime.timedelta(seconds=POLL_INTERVAL))
    alerts = []
    for row in data:
        bts_id = row[column_names.index('bts_id')]
        alerts.append(generate_alert('overload', 'high', None, bts_id, "Current load above 50"))
    return alerts

def fetch_column_names(cursor, query, table_name):
    cursor.execute(query % table_name)
    data = cursor.fetchall()
    cdr_records_col_names = list(sum(data, ())) # flattens data into 1d list
    return cdr_records_col_names

def open_db_connection(connection_params):
    logger.info('Connecting to the PostgreSQL database...')
    conn = psycopg2.connect(**connection_params)
    cursor = conn.cursor()
    return conn, cursor

def close_db_connection(conn):
    if conn is not None:
        conn.close()
        logger.info('Database connection closed.')

def main():
    conn = None
    connection_params = {
        "dbname": "mobile_network",
        "user": DB_USER,
        "password": DB_PASSWORD,
        "host": DB_HOST,
        "port": DB_PORT
    }
    recent_flapping = []
    conn = None
    while True:
        try:
            if conn is None or conn.closed:
                conn, cur = open_db_connection(connection_params)
            starttime = time.monotonic()
            cdr_records_col_names = fetch_column_names(cur, col_names_query, 'cdr_records')
            bts_registry_col_names = fetch_column_names(cur, col_names_query, 'bts_registry')
            
            recent_flapping = clear_old_flapping_alerts(recent_flapping)
            flapping_alerts = check_flapping(cur, flapping_query, cdr_records_col_names, recent_flapping)
            abnormal_speed_alerts = check_abnormal_speed(cur, speed_query, cdr_records_col_names)
            overload_alerts = check_overload(cur, overload_query, bts_registry_col_names)

            alerts = flapping_alerts + abnormal_speed_alerts + overload_alerts
            if alerts:
                cur.executemany(alerts_insert, alerts)
                conn.commit()
                logger.info('Alerts table updated')
            
            elapsed = time.monotonic() - starttime
            time.sleep(POLL_INTERVAL - elapsed)
        except (psycopg2.OperationalError, psycopg2.InterfaceError) as error:
            logger.error(f"DB Connection lost: {error}")
            close_db_connection(conn)
            time.sleep(5)
        except Exception as error:
            logger.exception("Unexpected error")
            time.sleep(5)

if __name__ == '__main__':
    main()
