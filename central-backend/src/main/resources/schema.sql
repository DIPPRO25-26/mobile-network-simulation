-- Mobile Network Simulation Database Schema

-- CDR (Call Detail Records) Table
CREATE TABLE IF NOT EXISTS cdr_records (
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

CREATE INDEX IF NOT EXISTS idx_cdr_imei ON cdr_records(imei);
CREATE INDEX IF NOT EXISTS idx_cdr_bts_id ON cdr_records(bts_id);
CREATE INDEX IF NOT EXISTS idx_cdr_timestamp ON cdr_records(timestamp_arrival);
-- change
CREATE INDEX IF NOT EXISTS idx_cdr_prev_bts ON cdr_records(previous_bts_id);
CREATE INDEX IF NOT EXISTS idx_cdr_imei_ts ON cdr_records(imei, timestamp_arrival);

-- Alerts Table (for anomaly detection)
CREATE TABLE IF NOT EXISTS alerts (
    id BIGSERIAL PRIMARY KEY,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    imei VARCHAR(15),
    bts_id VARCHAR(20),
    description TEXT,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_alert_type ON alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_alert_severity ON alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alert_detected_at ON alerts(detected_at);

-- User Activity Table (tracking active users)
CREATE TABLE IF NOT EXISTS user_activity (
    id BIGSERIAL PRIMARY KEY,
    imei VARCHAR(15) NOT NULL UNIQUE,
    current_bts_id VARCHAR(20) NOT NULL,
    current_lac VARCHAR(10) NOT NULL,
    last_seen TIMESTAMP NOT NULL,
    connection_count INTEGER DEFAULT 1,
    total_distance DECIMAL(12, 2) DEFAULT 0,
    average_speed DECIMAL(10, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_activity_imei ON user_activity(imei);
CREATE INDEX IF NOT EXISTS idx_user_activity_bts ON user_activity(current_bts_id);

-- BTS Registry Table
CREATE TABLE IF NOT EXISTS bts_registry (
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

CREATE INDEX IF NOT EXISTS idx_bts_registry_bts_id ON bts_registry(bts_id);
CREATE INDEX IF NOT EXISTS idx_bts_registry_lac ON bts_registry(lac);

-- Audit Log Table
CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    source VARCHAR(50) NOT NULL,
    imei VARCHAR(15),
    bts_id VARCHAR(20),
    request_data JSONB,
    response_data JSONB,
    status_code INTEGER,
    ip_address VARCHAR(45),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_log(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);

-- Comments explaining key fields:
COMMENT ON TABLE cdr_records IS 'Call Detail Records - stores user transitions between BTS stations';
COMMENT ON COLUMN cdr_records.imei IS 'International Mobile Equipment Identity - unique device identifier';
COMMENT ON COLUMN cdr_records.mcc IS 'Mobile Country Code (e.g., 219 for Croatia)';
COMMENT ON COLUMN cdr_records.mnc IS 'Mobile Network Code';
COMMENT ON COLUMN cdr_records.lac IS 'Location Area Code - groups multiple cells';
COMMENT ON COLUMN cdr_records.bts_id IS 'Base Transceiver Station identifier';

COMMENT ON TABLE alerts IS 'Anomaly detection alerts (flapping, overload, abnormal speed, etc.)';
COMMENT ON COLUMN alerts.alert_type IS 'Types: flapping, overload, abnormal_speed, suspicious_pattern';
COMMENT ON COLUMN alerts.severity IS 'Severity levels: low, medium, high, critical';

COMMENT ON TABLE user_activity IS 'Current state of active users in the network';
COMMENT ON TABLE bts_registry IS 'Registry of all BTS stations with their locations';
COMMENT ON TABLE audit_log IS 'Security audit trail for all API requests';


CREATE OR REPLACE VIEW view_users_by_bts AS
SELECT current_bts_id AS bts_id, COUNT(*) AS active_users
FROM user_activity
GROUP BY current_bts_id;

CREATE OR REPLACE VIEW view_handover_matrix AS
SELECT previous_bts_id AS from_bts, bts_id AS to_bts, COUNT(*) AS handovers
FROM cdr_records
WHERE previous_bts_id IS NOT NULL AND previous_bts_id <> bts_id
GROUP BY previous_bts_id, bts_id;

CREATE OR REPLACE VIEW view_lac_coverage AS
SELECT lac, COUNT(*) AS bts_count,
       MIN(location_x) AS min_x, MIN(location_y) AS min_y,
       MAX(location_x) AS max_x, MAX(location_y) AS max_y
FROM bts_registry
GROUP BY lac;

CREATE OR REPLACE VIEW view_avg_speed_per_bts AS
SELECT bts_id, AVG(speed) AS avg_speed
FROM cdr_records
WHERE speed IS NOT NULL
GROUP BY bts_id;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_handover_counts AS
SELECT previous_bts_id AS from_bts, bts_id AS to_bts, COUNT(*) AS handovers
FROM cdr_records
WHERE previous_bts_id IS NOT NULL AND previous_bts_id <> bts_id
GROUP BY previous_bts_id, bts_id
WITH NO DATA;

CREATE OR REPLACE FUNCTION fn_upsert_user_activity() RETURNS trigger AS $$
DECLARE
  ua RECORD;
  new_total_distance NUMERIC := COALESCE(NEW.distance, 0);
  new_avg_speed NUMERIC;
BEGIN
  SELECT * INTO ua FROM user_activity WHERE imei = NEW.imei FOR UPDATE;

  IF FOUND THEN
    new_total_distance := COALESCE(ua.total_distance,0) + COALESCE(NEW.distance,0);
    new_avg_speed := CASE WHEN ua.connection_count IS NULL OR ua.connection_count = 0
                         THEN COALESCE(NEW.speed,0)
                         ELSE ((COALESCE(ua.average_speed,0) * ua.connection_count) + COALESCE(NEW.speed,0)) / (ua.connection_count + 1)
                    END;
    UPDATE user_activity
    SET current_bts_id  = NEW.bts_id,
        current_lac     = NEW.lac,
        last_seen       = NEW.timestamp_arrival,
        connection_count= COALESCE(ua.connection_count,0) + 1,
        total_distance  = new_total_distance,
        average_speed   = new_avg_speed,
        updated_at      = NOW()
    WHERE imei = NEW.imei;
  ELSE
    INSERT INTO user_activity (imei, current_bts_id, current_lac, last_seen, connection_count, total_distance, average_speed, created_at, updated_at)
    VALUES (NEW.imei, NEW.bts_id, NEW.lac, NEW.timestamp_arrival, 1, COALESCE(NEW.distance,0), COALESCE(NEW.speed,0), NOW(), NOW());
  END IF;

  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_upsert_user_activity ON cdr_records;
CREATE TRIGGER trg_upsert_user_activity
AFTER INSERT ON cdr_records
FOR EACH ROW EXECUTE FUNCTION fn_upsert_user_activity();

-- Sample Data Insertion (for testing purposes)
-- INSERT INTO bts_registry (bts_id, lac, location_x, location_y, updated_at)
-- VALUES ('BTS001','1001',0,0,now()),('BTS002','1001',12,-5,now()),('BTS003','1002',100,100,now())
-- ON CONFLICT (bts_id) DO NOTHING;

-- INSERT INTO user_activity (imei, current_bts_id, current_lac, last_seen, connection_count, total_distance, average_speed)
-- VALUES ('123456789012345','BTS001','1001',now(),3,120.0,12.5)
-- ON CONFLICT (imei) DO UPDATE SET updated_at = NOW();

-- INSERT INTO cdr_records (imei, mcc, mnc, lac, bts_id, previous_bts_id, timestamp_arrival, user_location_x, user_location_y, speed, distance)
-- VALUES
-- ('123456789012345','219','01','1001','BTS001',NULL,now()-interval '10 minutes',0,0,10.0,30.0),
-- ('123456789012345','219','01','1001','BTS002','BTS001',now()-interval '5 minutes',12,-5,15.0,50.0),
-- ('987654321098765','219','01','1002','BTS003',NULL,now()-interval '3 minutes',100,100,0.0,0.0)
-- ON CONFLICT DO NOTHING;
