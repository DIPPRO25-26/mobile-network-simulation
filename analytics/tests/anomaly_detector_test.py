import os
import sys
import datetime
import logging
import csv
import unittest

# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append("../")
from src.anomaly_detection.rules_based_anomaly_detector import *                

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

create_test_cdr_records_str = """
CREATE TABLE IF NOT EXISTS test_cdr_records (
    id BIGSERIAL PRIMARY KEY,
    imei VARCHAR(15) NOT NULL,
    mcc VARCHAR(3) NOT NULL,
    mnc VARCHAR(3) NOT NULL,
    lac VARCHAR(10) NOT NULL,
    bts_id VARCHAR(20) NOT NULL,
    previous_bts_id VARCHAR(20),
    timestamp_arrival TIMESTAMP NOT NULL,
    timestamp_departure TIMESTAMP,
    user_location_x DECIMAL(10, 2),
    user_location_y DECIMAL(10, 2),
    distance DECIMAL(10, 2),
    speed DECIMAL(10, 2),
    duration INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""
create_test_bts_registry_str="""
CREATE TABLE IF NOT EXISTS test_bts_registry (
    id BIGSERIAL PRIMARY KEY,
    bts_id VARCHAR(20) NOT NULL UNIQUE,
    lac VARCHAR(10) NOT NULL,
    location_x DECIMAL(10, 2) NOT NULL,
    location_y DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    max_capacity INTEGER DEFAULT 1000,
    current_load INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""
insert_into_cdr_records_str="""
INSERT INTO test_cdr_records (imei, mcc, mnc, lac, bts_id, previous_bts_id, timestamp_arrival, timestamp_departure, distance, duration, speed, created_at)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
"""
insert_into_bts_registry_str="""
INSERT INTO test_bts_registry (bts_id, lac, location_x, location_y, current_load, created_at, updated_at)
VALUES (%s, %s, %s, %s, %s, %s, %s);
"""
drop_test_tables_str="""
DROP TABLE IF EXISTS test_cdr_records, test_bts_registry;
"""
test_flapping_query="""
SELECT * FROM test_cdr_records WHERE timestamp_arrival >= '%s';
"""
test_speed_query = """
SELECT * FROM test_cdr_records WHERE created_at >= '%s' AND speed > 200;
"""
test_overload_query = """
SELECT * FROM test_bts_registry WHERE updated_at >= '%s' AND current_load > 50;
"""
get_alerts_query = """
SELECT * FROM alerts WHERE alert_type = '%s';
"""

def create_test_tables(cursor):
    cursor.execute(create_test_cdr_records_str)
    cursor.execute(create_test_bts_registry_str)
    logger.info("created two test tables")

def drop_test_tables(cursor):
    cursor.execute(drop_test_tables_str)
    logger.info("dropped the test tables")

def read_dummy_data(csv_name):
    rows = []
    csvheader = None
    with open(csv_name, newline='') as csvfile:
        datareader = csv.reader(csvfile, delimiter=',')
        csvheader = datareader.__next__()
        for row in datareader:
            rows.append(row)
    return csvheader, rows

def insert_test_data(test_header, test_rows, cursor, insert_str):
    data = []
    offset = 0
    for row in test_rows:
        if 'timestamp_arrival' and 'timestamp_departure' in test_header:
            now_minus_55min = datetime.datetime.now() - datetime.timedelta(minutes=55)
            row[test_header.index('timestamp_arrival')] = now_minus_55min + datetime.timedelta(seconds=offset)
            row[test_header.index('timestamp_departure')] = None
            row[test_header.index('duration')] = round(float(row[test_header.index('duration')]) * 60 * 60)
            offset+=5
        now_minus_10s = datetime.datetime.now() - datetime.timedelta(seconds=10)
        if 'updated_at' in test_header:
            row[test_header.index('updated_at')] = now_minus_10s
        if 'created_at' in test_header:
            row[test_header.index('created_at')] = now_minus_10s
        else:
            row.append(now_minus_10s)
        table_row = tuple(row)
        data.append(table_row)
    cursor.executemany(insert_str, data)
    logger.info(f"inserted {len(data)} rows into test table")

def get_table_names(cursor):
    q = """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema='public'
    AND table_type='BASE TABLE';
    """
    cursor.execute(q)
    data = cursor.fetchall()
    return data

class TestAnomalyDetection(unittest.TestCase):
    conn = None

    @classmethod
    def setUpClass(cls):
        connection_params = {
            "dbname": "mobile_network",
            "user": DB_USER,
            "password": DB_PASSWORD,
            "host": "localhost",
            "port": 5432
        }
        cls.conn, cls.cur = open_db_connection(connection_params)
        
        create_test_tables(cls.cur)
        #logger.debug(get_table_names(cls.cur))
                
        cls.cdr_records_col_names = fetch_column_names(cls.cur, col_names_query, 'test_cdr_records')
        cls.bts_registry_col_names = fetch_column_names(cls.cur, col_names_query, 'test_bts_registry')
        cls.alerts_col_names = fetch_column_names(cls.cur, col_names_query, 'alerts')
        
        test_cdr_records_header, test_cdr_records = read_dummy_data("./dummy_data/dummy_cdr_records.csv")
        test_bts_registry_header, test_bts_registry = read_dummy_data("./dummy_data/dummy_bts_registry.csv")

        insert_test_data(test_bts_registry_header, test_bts_registry, cls.cur, insert_into_bts_registry_str)
        insert_test_data(test_cdr_records_header, test_cdr_records, cls.cur, insert_into_cdr_records_str)

        cls.cur.execute("TRUNCATE TABLE alerts;")
 
    @classmethod
    def tearDownClass(cls):
        drop_test_tables(cls.cur)
        cls.cur.close()
        close_db_connection(cls.conn)
    
    def test_db_connection(self):
        self.assertTrue(self.conn.closed == 0)
    
    def test_flapping_alerts(self):
        flapping_alerts = check_flapping(self.cur, test_flapping_query, self.cdr_records_col_names, [])
        self.cur.executemany(alerts_insert, flapping_alerts)
        self.cur.execute(get_alerts_query % "flapping")
        flapping_data_from_table = self.cur.fetchall()

        # ocekujem 2 rezultata, IMEI 123455 i 123457
        expected_results = [
            {'imei': '123455',
             'bts_id': 'BTS4',
             'description': 'Flapping between BTS4 and BTS2 7 times'},
            {'imei': '123457',
             'bts_id': 'BTS2',
             'description': 'Flapping between BTS2 and BTS3 6 times'}, 
        ]
        for flapping_alert, expected_result in zip(flapping_data_from_table, expected_results):
            self.assertEqual(flapping_alert[self.alerts_col_names.index('imei')], expected_result["imei"])
            self.assertEqual(flapping_alert[self.alerts_col_names.index('bts_id')], expected_result["bts_id"])
            self.assertEqual(flapping_alert[self.alerts_col_names.index('description')], expected_result["description"])

    def test_speed_alerts(self):
        abnormal_speed_alerts = check_abnormal_speed(self.cur, test_speed_query, self.cdr_records_col_names)
        self.cur.executemany(alerts_insert, abnormal_speed_alerts)
        self.cur.execute(get_alerts_query % "abnormal_speed")
        speeding_from_table = self.cur.fetchall()

        # ocekujem 4 rezultata, svi s IMEI-om 123458
        expected_results = ['123458'] * 4
        for speeding_alert, expected_result in zip(speeding_from_table, expected_results):
            self.assertEqual(speeding_alert[self.alerts_col_names.index('imei')], expected_result)


    def test_overload_alerts(self):
        overload_alerts = check_overload(self.cur, test_overload_query, self.bts_registry_col_names)
        self.cur.executemany(alerts_insert, overload_alerts)
        self.cur.execute(get_alerts_query % "overload")
        overload_from_table = self.cur.fetchall()
        overload_alert = overload_from_table[0]

        #ocekujem 1 rezultat, bts_id=BTS3
        expected_result = 'BTS3'
        self.assertEqual(overload_alert[self.alerts_col_names.index('bts_id')], expected_result)

if __name__=="__main__":
    unittest.main(verbosity=2)