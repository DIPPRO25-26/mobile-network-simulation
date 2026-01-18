import psycopg2
import sys
import os
import logging
import time
import datetime

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "15"))
DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "admin123")

flapping_query = """
SELECT * FROM cdr_records WHERE timestamp_arrival >= '%s';
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
    data = fetch_data(cursor, flapping_query, datetime.datetime.now() - datetime.timedelta(hours=1))
    # grupiraj entryje po imei-ma
    imei_grouped_entries = {}
    for row in data:
        imei = row[column_names.index('imei')]
        bts_id = row[column_names.index('bts_id')]
        previous_bts_id = row[column_names.index('previous_bts_id')]
        if imei in imei_grouped_entries.keys():
            imei_grouped_entries[imei].append((previous_bts_id, bts_id))
        else:
            imei_grouped_entries[imei] = [(previous_bts_id, bts_id)]
    
    new_flapping = []
    for imei in imei_grouped_entries:
        bts_pairs = imei_grouped_entries[imei] # bts_pairs je lista 2-tupleova
        num_transitions = len(bts_pairs)
        if num_transitions <= 5: # preskacem IMEI-e koji imaju manje od 5 prijelaza uopce
            continue
        bts_chains_list = [None] * num_transitions # bit ce lista listi
        
        for i in range(0, num_transitions):
            bts_a, bts_b = bts_pairs[i]
            bts_chains_list[i] = [bts_a, bts_b]
            for j in range(i+1, num_transitions):
                previous_bts, current_bts = bts_pairs[j]
                if previous_bts == bts_b and current_bts == bts_a:
                    bts_chains_list[i].append(current_bts)
                    bts_a, bts_b = previous_bts, current_bts
                else:
                    break
        
        # za pronadjene lance duljine >6 zabiljezi flapping [broj prijelaza = duljina lanca - 1]
        prev_chain_longer = 0
        for chain in bts_chains_list:
            if len(chain) > 6: 
                if not prev_chain_longer:
                    flap = (imei, chain)
                    new_flapping.append(flap)
                prev_chain_longer = 1
            else:
                prev_chain_longer = 0

    alerts = []
    recent_flapping_info = [x["info"] for x in recent_flapping]
    for flap in new_flapping:
        if flap not in recent_flapping_info:
            imei, chain = flap
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
        "host": "localhost",
        "port": 5432
    }
    recent_flapping = []
    while True:
        try:
            starttime = time.monotonic()
            conn, cur = open_db_connection(connection_params)

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
            
            cur.close()        
            close_db_connection(conn)  
            time.sleep(POLL_INTERVAL - (time.monotonic() - starttime))
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            close_db_connection(conn) 
            sys.exit(0) 

if __name__ == '__main__':
    main()
