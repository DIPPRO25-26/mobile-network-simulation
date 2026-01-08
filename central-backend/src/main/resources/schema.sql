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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_imei (imei),
    INDEX idx_bts_id (bts_id),
    INDEX idx_timestamp (timestamp_arrival)
);

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
    metadata JSONB,
    INDEX idx_alert_type (alert_type),
    INDEX idx_severity (severity),
    INDEX idx_detected_at (detected_at)
);

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
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_imei_activity (imei),
    INDEX idx_current_bts (current_bts_id)
);

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
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_bts_id_registry (bts_id),
    INDEX idx_lac (lac)
);

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
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_event_type (event_type),
    INDEX idx_timestamp_audit (timestamp)
);

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
