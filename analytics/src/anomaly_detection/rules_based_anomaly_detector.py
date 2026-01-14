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

# TODO: 
# nemoj dodavati alert vise puta za istu pojavu flappinga (isti imei, isti BTS-ovi)
# ostale provjere to izbjegnu jer nema preklapanja
# flapping: korisnik se prebacuje izmedju 2 BTS-a >5 puta/h
def check_flapping(cursor, column_names):
    alerts = []
    now_minus_1h = datetime.datetime.now() - datetime.timedelta(hours=1)
    cursor.execute(flapping_query % now_minus_1h)    
    data = cursor.fetchall()

    # grupiraj entryje po imei-ma
    imei_grouped_entries = {}
    for row in data:
        imei = row[column_names.index('imei')]
        bts_id = row[column_names.index('bts_id')]
        previous_bts_id = row[column_names.index('previous_bts_id')]
        if imei in imei_grouped_entries.keys():
            imei_grouped_entries[imei].append((previous_bts_id, bts_id)) # UZMI SAMO BTS_ID
        else:
            imei_grouped_entries[imei] = [(previous_bts_id, bts_id)]

    # testni dict
    # imei_grouped_entries = {'123456': [
    #     ('BTS6', 'BTS5'), 
    #     ('BTS5', 'BTS4'),
    #     ('BTS4', 'BTS5'),
    #     ('BTS5', 'BTS4'),
    #     ('BTS4', 'BTS5'),
    #     ('BTS5', 'BTS4'),
    #     ('BTS4', 'BTS5'),
    #     ('BTS5', 'BTS6'),
    #     ('BTS6', 'BTS5'),
    #     ('BTS5', 'BTS7'),
    # ]}
    
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
        
        # za pronadjene lance duljine >5 generiraj alerte
        prev_chain_longer = 0
        for chain in bts_chains_list:
            if len(chain) > 5:
                if not prev_chain_longer:
                    alerts.append(generate_alert('flapping', 'medium', imei, chain[0], 
                                                 f"Flapping between {chain[0]} and {chain[1]} {len(chain)} times"))
                prev_chain_longer = 1
            else:
                prev_chain_longer = 0
    return alerts

# abnormal speed: >200km/h
def check_abnormal_speed(cursor, column_names):
    alerts = []
    now_minus_poll_interval = datetime.datetime.now() - datetime.timedelta(seconds=POLL_INTERVAL)
    cursor.execute(speed_query % now_minus_poll_interval)
    data = cursor.fetchall()
    for row in data:
        imei = row[column_names.index('imei')]
        bts_id = row[column_names.index('bts_id')]
        alerts.append(generate_alert('abnormal speed', 'medium', imei, bts_id, "Speed above 200km/h"))
    return alerts

# overload: current load >50
def check_overload(cursor, column_names):
    alerts = []
    now_minus_poll_interval = datetime.datetime.now() - datetime.timedelta(seconds=POLL_INTERVAL)
    cursor.execute(overload_query % now_minus_poll_interval)
    data = cursor.fetchall()
    for row in data:
        bts_id = row[column_names.index('bts_id')]
        alerts.append(generate_alert('overload', 'medium', None, bts_id, "Current load above 50"))
    return alerts

def main():
    while True:
        try:
            conn = None
            connection_params = {
                "dbname": "mobile_network",
                "user": DB_USER,
                "password": DB_PASSWORD,
                "host": "localhost",
                "port": 5432
            }

            logger.info('Connecting to the PostgreSQL database...')
            conn = psycopg2.connect(**connection_params)
            cur = conn.cursor()

            cur.execute(col_names_query % 'cdr_records')
            data = cur.fetchall()
            cdr_records_col_names = list(sum(data, ())) # flattens data into 1d list
            cur.execute(col_names_query % 'bts_registry')
            data = cur.fetchall()
            bts_registry_col_names = list(sum(data, ())) # flattens data into 1d list
            
            alerts = [] 
            flapping_alerts = check_flapping(cur, cdr_records_col_names)
            alerts += flapping_alerts
            abnormal_speed_alerts = check_abnormal_speed(cur, cdr_records_col_names)
            alerts += abnormal_speed_alerts
            overload_alerts = check_overload(cur, bts_registry_col_names)
            alerts += overload_alerts
            if alerts:
                cur.executemany(alerts_insert, alerts)
                conn.commit()
                logger.info('Alerts table updated')
            
            cur.close()
            if conn is not None:
                conn.close()
                logger.info('Database connection closed.')
            time.sleep(POLL_INTERVAL)
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        except KeyboardInterrupt as ki:
            print(ki)
            sys.exit(0)
            
if __name__ == '__main__':
    main()

    

