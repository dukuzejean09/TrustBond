-- ============================================================================
-- TrustBond Database Schema v2.0
-- Privacy-Preserving Anonymous Community Incident Reporting System
-- ============================================================================
-- 16 Tables Total:
-- Core (6): devices, locations, incident_types, unified_cases, incident_reports, report_evidence
-- ML (3): ml_models, ml_predictions, ml_training_data
-- Police (2): police_users, notifications
-- Analytics (2): hotspots, daily_statistics
-- Public (1): public_safety_zones
-- System (2): system_settings, activity_logs
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Drop existing tables if they exist (in reverse dependency order)
DROP TABLE IF EXISTS activity_logs CASCADE;
DROP TABLE IF EXISTS system_settings CASCADE;
DROP TABLE IF EXISTS public_safety_zones CASCADE;
DROP TABLE IF EXISTS daily_statistics CASCADE;
DROP TABLE IF EXISTS hotspots CASCADE;
DROP TABLE IF EXISTS notifications CASCADE;
DROP TABLE IF EXISTS ml_training_data CASCADE;
DROP TABLE IF EXISTS ml_predictions CASCADE;
DROP TABLE IF EXISTS ml_models CASCADE;
DROP TABLE IF EXISTS report_evidence CASCADE;
DROP TABLE IF EXISTS incident_reports CASCADE;
DROP TABLE IF EXISTS unified_cases CASCADE;
DROP TABLE IF EXISTS incident_types CASCADE;
DROP TABLE IF EXISTS locations CASCADE;
DROP TABLE IF EXISTS police_users CASCADE;
DROP TABLE IF EXISTS devices CASCADE;

-- ============================================================================
-- TABLE 1: devices
-- Anonymous Reporter Devices - No personal data stored
-- ============================================================================
CREATE TABLE devices (
    device_id CHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::TEXT,
    device_fingerprint VARCHAR(255) UNIQUE NOT NULL,
    platform VARCHAR(10) NOT NULL CHECK (platform IN ('android', 'ios')),
    app_version VARCHAR(20),
    os_version VARCHAR(30),
    device_language VARCHAR(10) DEFAULT 'en',
    current_trust_score DECIMAL(5, 2) DEFAULT 50.00 CHECK (current_trust_score >= 0 AND current_trust_score <= 100),
    total_reports INTEGER DEFAULT 0,
    verified_reports INTEGER DEFAULT 0,
    false_reports INTEGER DEFAULT 0,
    is_blocked BOOLEAN DEFAULT FALSE,
    block_reason VARCHAR(255),
    blocked_at TIMESTAMP,
    blocked_by INTEGER,
    push_token VARCHAR(500),
    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_devices_trust_score ON devices(current_trust_score);
CREATE INDEX idx_devices_is_blocked ON devices(is_blocked);
CREATE INDEX idx_devices_last_active ON devices(last_active_at);

COMMENT ON TABLE devices IS 'Anonymous reporter devices with trust scores - no personal data stored';

-- ============================================================================
-- TABLE 2: locations
-- Rwanda Administrative Geography (Hierarchical: Province→District→Sector→Cell→Village)
-- ============================================================================
CREATE TABLE locations (
    location_id SERIAL PRIMARY KEY,
    parent_id INTEGER REFERENCES locations(location_id) ON DELETE CASCADE,
    location_type VARCHAR(20) NOT NULL CHECK (location_type IN ('province', 'district', 'sector', 'cell', 'village')),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(40) UNIQUE NOT NULL,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    boundary_geojson JSON,
    population INTEGER,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_locations_parent ON locations(parent_id);
CREATE INDEX idx_locations_type ON locations(location_type);
CREATE INDEX idx_locations_coords ON locations(latitude, longitude);

COMMENT ON TABLE locations IS 'Rwanda geography hierarchy - Province→District→Sector→Cell→Village';

-- ============================================================================
-- TABLE 3: incident_types
-- Incident Taxonomy (Categories + Types Combined) - Hierarchical
-- ============================================================================
CREATE TABLE incident_types (
    type_id SMALLSERIAL PRIMARY KEY,
    parent_id SMALLINT REFERENCES incident_types(type_id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon_name VARCHAR(50),
    color_hex CHAR(7) DEFAULT '#1976D2',
    severity_level SMALLINT CHECK (severity_level IS NULL OR (severity_level >= 1 AND severity_level <= 5)),
    display_order SMALLINT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_incident_types_parent ON incident_types(parent_id);
CREATE INDEX idx_incident_types_active_order ON incident_types(is_active, display_order);

COMMENT ON TABLE incident_types IS 'Hierarchical incident classification - categories have parent_id=NULL, types have parent_id=category';

-- ============================================================================
-- TABLE 10: police_users (Created early due to FK dependencies)
-- Police Authentication and Roles
-- ============================================================================
CREATE TABLE police_users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    badge_number VARCHAR(50) UNIQUE,
    phone_number VARCHAR(20),
    role VARCHAR(20) NOT NULL DEFAULT 'officer' CHECK (role IN ('super_admin', 'admin', 'commander', 'officer', 'analyst', 'viewer')),
    permissions JSON,
    assigned_location_id INTEGER REFERENCES locations(location_id),
    can_access_all_locations BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    two_factor_enabled BOOLEAN DEFAULT FALSE,
    two_factor_secret VARCHAR(100),
    password_changed_at TIMESTAMP,
    failed_login_attempts SMALLINT DEFAULT 0,
    locked_until TIMESTAMP,
    last_login_at TIMESTAMP,
    last_login_ip VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES police_users(user_id),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_police_users_role ON police_users(role);
CREATE INDEX idx_police_users_location ON police_users(assigned_location_id);
CREATE INDEX idx_police_users_active ON police_users(is_active);

COMMENT ON TABLE police_users IS 'Police authentication with role-based access control';

-- Add foreign key for devices.blocked_by
ALTER TABLE devices ADD CONSTRAINT fk_devices_blocked_by FOREIGN KEY (blocked_by) REFERENCES police_users(user_id);

-- ============================================================================
-- TABLE 7: ml_models (Created early due to FK dependencies)
-- Machine Learning Models for Verification
-- ============================================================================
CREATE TABLE ml_models (
    model_id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_type VARCHAR(30) NOT NULL CHECK (model_type IN ('trust_scoring', 'anomaly_detection', 'clustering', 'priority_prediction')),
    model_version VARCHAR(20) NOT NULL,
    description TEXT,
    algorithm VARCHAR(50),
    input_features JSON,
    output_format JSON,
    training_data_count INTEGER DEFAULT 0,
    training_accuracy DECIMAL(5, 4),
    validation_accuracy DECIMAL(5, 4),
    model_file_path VARCHAR(500),
    model_file_hash CHAR(64),
    is_active BOOLEAN DEFAULT FALSE,
    activated_at TIMESTAMP,
    activated_by INTEGER REFERENCES police_users(user_id),
    trained_at TIMESTAMP,
    trained_by INTEGER REFERENCES police_users(user_id),
    last_retrained_at TIMESTAMP,
    performance_metrics JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ml_models_type_active ON ml_models(model_type, is_active);
CREATE INDEX idx_ml_models_trained_at ON ml_models(trained_at);

COMMENT ON TABLE ml_models IS 'Trained ML models for verification enhancement - trust scoring, anomaly detection, clustering, priority prediction';

-- ============================================================================
-- TABLE 12: hotspots (Created early due to FK dependencies)
-- Crime Cluster Detection
-- ============================================================================
CREATE TABLE hotspots (
    hotspot_id SERIAL PRIMARY KEY,
    hotspot_name VARCHAR(100),
    location_id INTEGER REFERENCES locations(location_id),
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    radius_meters DECIMAL(10, 2) DEFAULT 500,
    boundary_geojson JSON,
    case_count INTEGER DEFAULT 0,
    total_reports INTEGER DEFAULT 0,
    avg_trust_score DECIMAL(5, 2),
    avg_ml_confidence DECIMAL(5, 4),
    dominant_incident_type_id SMALLINT REFERENCES incident_types(type_id),
    dominant_type_percentage DECIMAL(5, 2),
    risk_level VARCHAR(10) DEFAULT 'medium' CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    priority_score DECIMAL(5, 2) DEFAULT 0 CHECK (priority_score >= 0 AND priority_score <= 100),
    first_incident_at TIMESTAMP,
    last_incident_at TIMESTAMP,
    peak_hour SMALLINT CHECK (peak_hour IS NULL OR (peak_hour >= 0 AND peak_hour <= 23)),
    peak_day_of_week SMALLINT CHECK (peak_day_of_week IS NULL OR (peak_day_of_week >= 0 AND peak_day_of_week <= 6)),
    status VARCHAR(15) DEFAULT 'active' CHECK (status IN ('active', 'monitoring', 'addressed', 'resolved')),
    assigned_officer_id INTEGER REFERENCES police_users(user_id),
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_hotspots_location ON hotspots(location_id);
CREATE INDEX idx_hotspots_coords ON hotspots(latitude, longitude);
CREATE INDEX idx_hotspots_status_risk ON hotspots(status, risk_level);
CREATE INDEX idx_hotspots_priority ON hotspots(priority_score DESC);

COMMENT ON TABLE hotspots IS 'Detected incident clusters - can contain multiple crime types in same area';

-- ============================================================================
-- TABLE 4: unified_cases
-- Grouped Incident Cases for Law Enforcement
-- ============================================================================
CREATE TABLE unified_cases (
    case_id CHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::TEXT,
    case_number VARCHAR(30) UNIQUE NOT NULL,
    incident_type_id SMALLINT REFERENCES incident_types(type_id),
    location_id INTEGER REFERENCES locations(location_id),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    radius_meters DECIMAL(8, 2) DEFAULT 0,
    address_description VARCHAR(255),
    incident_date DATE,
    incident_time_start TIME,
    incident_time_end TIME,
    report_count INTEGER DEFAULT 1,
    evidence_count INTEGER DEFAULT 0,
    reporter_count INTEGER DEFAULT 1,
    combined_trust_score DECIMAL(5, 2) DEFAULT 50.00,
    ml_priority_score DECIMAL(5, 2) DEFAULT 50.00,
    ml_confidence DECIMAL(5, 4) DEFAULT 0.5000,
    verification_status VARCHAR(15) DEFAULT 'pending' CHECK (verification_status IN ('pending', 'verified', 'suspicious', 'false')),
    location_verified BOOLEAN DEFAULT FALSE,
    motion_verified BOOLEAN DEFAULT FALSE,
    duplicate_checked BOOLEAN DEFAULT FALSE,
    case_status VARCHAR(15) DEFAULT 'new' CHECK (case_status IN ('new', 'reviewing', 'investigating', 'resolved', 'closed')),
    priority VARCHAR(10) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    assigned_officer_id INTEGER REFERENCES police_users(user_id),
    assigned_at TIMESTAMP,
    hotspot_id INTEGER REFERENCES hotspots(hotspot_id),
    resolution_type VARCHAR(15) CHECK (resolution_type IN ('confirmed', 'false_report', 'duplicate', 'no_action', 'referred')),
    resolution_notes TEXT,
    resolved_at TIMESTAMP,
    resolved_by INTEGER REFERENCES police_users(user_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_unified_cases_number ON unified_cases(case_number);
CREATE INDEX idx_unified_cases_type ON unified_cases(incident_type_id);
CREATE INDEX idx_unified_cases_location ON unified_cases(location_id);
CREATE INDEX idx_unified_cases_coords ON unified_cases(latitude, longitude);
CREATE INDEX idx_unified_cases_date ON unified_cases(incident_date);
CREATE INDEX idx_unified_cases_status_priority ON unified_cases(case_status, priority);
CREATE INDEX idx_unified_cases_ml_priority ON unified_cases(ml_priority_score DESC);
CREATE INDEX idx_unified_cases_assigned ON unified_cases(assigned_officer_id);
CREATE INDEX idx_unified_cases_hotspot ON unified_cases(hotspot_id);

COMMENT ON TABLE unified_cases IS 'Grouped incidents for police - multiple reports of same incident become one case';

-- ============================================================================
-- TABLE 5: incident_reports
-- Individual Citizen Report Submissions
-- ============================================================================
CREATE TABLE incident_reports (
    report_id CHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::TEXT,
    device_id CHAR(36) NOT NULL REFERENCES devices(device_id),
    case_id CHAR(36) REFERENCES unified_cases(case_id),
    incident_type_id SMALLINT REFERENCES incident_types(type_id),
    title VARCHAR(200),
    description TEXT,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    location_accuracy_meters DECIMAL(8, 2),
    location_source VARCHAR(10) DEFAULT 'gps' CHECK (location_source IN ('gps', 'network', 'manual')),
    location_id INTEGER REFERENCES locations(location_id),
    reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    incident_occurred_at TIMESTAMP,
    time_approximate BOOLEAN DEFAULT FALSE,
    accelerometer_data JSON,
    gyroscope_data JSON,
    motion_score DECIMAL(5, 2) CHECK (motion_score IS NULL OR (motion_score >= 0 AND motion_score <= 100)),
    device_orientation VARCHAR(20),
    battery_level SMALLINT CHECK (battery_level IS NULL OR (battery_level >= 0 AND battery_level <= 100)),
    network_type VARCHAR(20),
    location_check_passed BOOLEAN,
    motion_check_passed BOOLEAN,
    is_duplicate BOOLEAN DEFAULT FALSE,
    duplicate_of_report_id CHAR(36) REFERENCES incident_reports(report_id),
    is_grouped BOOLEAN DEFAULT FALSE,
    report_status VARCHAR(15) DEFAULT 'submitted' CHECK (report_status IN ('submitted', 'processing', 'verified', 'rejected')),
    rejection_reason VARCHAR(255),
    citizen_notified BOOLEAN DEFAULT FALSE,
    app_version VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_incident_reports_device ON incident_reports(device_id);
CREATE INDEX idx_incident_reports_case ON incident_reports(case_id);
CREATE INDEX idx_incident_reports_type ON incident_reports(incident_type_id);
CREATE INDEX idx_incident_reports_coords ON incident_reports(latitude, longitude);
CREATE INDEX idx_incident_reports_location ON incident_reports(location_id);
CREATE INDEX idx_incident_reports_reported_at ON incident_reports(reported_at);
CREATE INDEX idx_incident_reports_status ON incident_reports(report_status);

COMMENT ON TABLE incident_reports IS 'Individual citizen submissions - multiple reports can link to one unified_case';

-- ============================================================================
-- TABLE 6: report_evidence
-- Evidence Files (Photos, Videos, Audio)
-- ============================================================================
CREATE TABLE report_evidence (
    evidence_id CHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::TEXT,
    report_id CHAR(36) NOT NULL REFERENCES incident_reports(report_id) ON DELETE CASCADE,
    case_id CHAR(36) REFERENCES unified_cases(case_id),
    evidence_type VARCHAR(10) NOT NULL CHECK (evidence_type IN ('photo', 'video', 'audio')),
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size_bytes INTEGER,
    mime_type VARCHAR(100),
    duration_seconds SMALLINT,
    width_pixels SMALLINT,
    height_pixels SMALLINT,
    file_hash CHAR(64),
    captured_at TIMESTAMP,
    capture_latitude DECIMAL(10, 8),
    capture_longitude DECIMAL(11, 8),
    is_valid BOOLEAN DEFAULT TRUE,
    quality_score DECIMAL(5, 2),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_report_evidence_report ON report_evidence(report_id);
CREATE INDEX idx_report_evidence_case ON report_evidence(case_id);
CREATE INDEX idx_report_evidence_type ON report_evidence(evidence_type);

COMMENT ON TABLE report_evidence IS 'Evidence metadata - actual files stored in encrypted cloud storage';

-- ============================================================================
-- TABLE 8: ml_predictions
-- ML Analysis Results Per Report
-- ============================================================================
CREATE TABLE ml_predictions (
    prediction_id CHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::TEXT,
    report_id CHAR(36) NOT NULL REFERENCES incident_reports(report_id) ON DELETE CASCADE,
    case_id CHAR(36) REFERENCES unified_cases(case_id),
    model_id INTEGER REFERENCES ml_models(model_id),
    ml_trust_score DECIMAL(5, 4) CHECK (ml_trust_score >= 0 AND ml_trust_score <= 1),
    ml_confidence DECIMAL(5, 4) CHECK (ml_confidence >= 0 AND ml_confidence <= 1),
    predicted_priority VARCHAR(10) CHECK (predicted_priority IN ('low', 'medium', 'high', 'critical')),
    predicted_validity VARCHAR(15) CHECK (predicted_validity IN ('likely_genuine', 'uncertain', 'likely_false')),
    anomaly_score DECIMAL(5, 4) CHECK (anomaly_score >= 0 AND anomaly_score <= 1),
    anomaly_flags JSON,
    cluster_confidence DECIMAL(5, 4),
    location_pattern_score DECIMAL(5, 4),
    motion_pattern_score DECIMAL(5, 4),
    time_pattern_score DECIMAL(5, 4),
    feature_importance JSON,
    raw_model_output JSON,
    prediction_time_ms INTEGER,
    predicted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ml_predictions_report ON ml_predictions(report_id);
CREATE INDEX idx_ml_predictions_case ON ml_predictions(case_id);
CREATE INDEX idx_ml_predictions_model ON ml_predictions(model_id);
CREATE INDEX idx_ml_predictions_trust ON ml_predictions(ml_trust_score);
CREATE INDEX idx_ml_predictions_priority ON ml_predictions(predicted_priority);
CREATE INDEX idx_ml_predictions_anomaly ON ml_predictions(anomaly_score);

COMMENT ON TABLE ml_predictions IS 'ML analysis results for each report - trust scores, anomaly detection, priority prediction';

-- ============================================================================
-- TABLE 9: ml_training_data
-- Verified Reports for ML Model Retraining
-- ============================================================================
CREATE TABLE ml_training_data (
    training_id CHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::TEXT,
    report_id CHAR(36) NOT NULL REFERENCES incident_reports(report_id),
    case_id CHAR(36) REFERENCES unified_cases(case_id),
    verified_label VARCHAR(15) NOT NULL CHECK (verified_label IN ('genuine', 'false', 'suspicious')),
    confidence_label VARCHAR(10) DEFAULT 'medium' CHECK (confidence_label IN ('high', 'medium', 'low')),
    verified_by INTEGER REFERENCES police_users(user_id),
    verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verification_notes TEXT,
    location_data JSON,
    motion_data JSON,
    time_features JSON,
    device_features JSON,
    original_ml_prediction DECIMAL(5, 4),
    prediction_was_correct BOOLEAN,
    used_in_training BOOLEAN DEFAULT FALSE,
    trained_model_id INTEGER REFERENCES ml_models(model_id),
    trained_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    deactivated_reason VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ml_training_report ON ml_training_data(report_id);
CREATE INDEX idx_ml_training_case ON ml_training_data(case_id);
CREATE INDEX idx_ml_training_label ON ml_training_data(verified_label);
CREATE INDEX idx_ml_training_used ON ml_training_data(used_in_training);
CREATE INDEX idx_ml_training_verified_at ON ml_training_data(verified_at);
CREATE INDEX idx_ml_training_model ON ml_training_data(trained_model_id);

COMMENT ON TABLE ml_training_data IS 'Police-verified reports used as labeled data for ML model retraining';

-- ============================================================================
-- TABLE 11: notifications
-- Police Alerts and Notifications
-- ============================================================================
CREATE TABLE notifications (
    notification_id CHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::TEXT,
    user_id INTEGER NOT NULL REFERENCES police_users(user_id) ON DELETE CASCADE,
    notification_type VARCHAR(15) NOT NULL CHECK (notification_type IN ('new_case', 'urgent_case', 'case_update', 'hotspot_alert', 'assignment', 'ml_alert', 'system')),
    title VARCHAR(200) NOT NULL,
    message TEXT,
    case_id CHAR(36) REFERENCES unified_cases(case_id),
    hotspot_id INTEGER REFERENCES hotspots(hotspot_id),
    priority VARCHAR(10) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,
    is_dismissed BOOLEAN DEFAULT FALSE,
    action_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE INDEX idx_notifications_user_read ON notifications(user_id, is_read);
CREATE INDEX idx_notifications_type ON notifications(notification_type);
CREATE INDEX idx_notifications_created ON notifications(created_at);

COMMENT ON TABLE notifications IS 'Alerts sent to police officers about cases, hotspots, and system events';

-- ============================================================================
-- TABLE 13: daily_statistics
-- Pre-Aggregated Analytics
-- ============================================================================
CREATE TABLE daily_statistics (
    stat_id SERIAL PRIMARY KEY,
    stat_date DATE NOT NULL,
    location_id INTEGER REFERENCES locations(location_id),
    total_reports INTEGER DEFAULT 0,
    verified_reports INTEGER DEFAULT 0,
    rejected_reports INTEGER DEFAULT 0,
    new_cases INTEGER DEFAULT 0,
    resolved_cases INTEGER DEFAULT 0,
    active_hotspots INTEGER DEFAULT 0,
    avg_ml_trust_score DECIMAL(5, 4),
    avg_response_time_hours DECIMAL(5, 2),
    ml_accuracy_rate DECIMAL(5, 4),
    top_incident_types JSON,
    hourly_distribution JSON,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stat_date, location_id)
);

CREATE INDEX idx_daily_statistics_date ON daily_statistics(stat_date);
CREATE INDEX idx_daily_statistics_location ON daily_statistics(location_id);

COMMENT ON TABLE daily_statistics IS 'Pre-calculated daily statistics for fast dashboard loading';

-- ============================================================================
-- TABLE 14: public_safety_zones
-- Anonymized Public Safety Map
-- ============================================================================
CREATE TABLE public_safety_zones (
    zone_id SERIAL PRIMARY KEY,
    location_id INTEGER REFERENCES locations(location_id),
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    radius_meters INTEGER DEFAULT 500,
    safety_level VARCHAR(10) DEFAULT 'safe' CHECK (safety_level IN ('safe', 'caution', 'alert', 'danger')),
    safety_score DECIMAL(5, 2) DEFAULT 100 CHECK (safety_score >= 0 AND safety_score <= 100),
    incident_count_7d INTEGER DEFAULT 0,
    incident_count_30d INTEGER DEFAULT 0,
    trend VARCHAR(12) DEFAULT 'stable' CHECK (trend IN ('improving', 'stable', 'worsening')),
    dominant_category VARCHAR(100),
    peak_risk_hours JSON,
    tips JSON,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_visible BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_public_safety_zones_location ON public_safety_zones(location_id);
CREATE INDEX idx_public_safety_zones_coords ON public_safety_zones(latitude, longitude);
CREATE INDEX idx_public_safety_zones_level ON public_safety_zones(safety_level);

COMMENT ON TABLE public_safety_zones IS 'Anonymized safety data for public community map - no case details exposed';

-- ============================================================================
-- TABLE 15: system_settings
-- Application Configuration
-- ============================================================================
CREATE TABLE system_settings (
    setting_id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    value_type VARCHAR(10) DEFAULT 'string' CHECK (value_type IN ('string', 'number', 'boolean', 'json')),
    category VARCHAR(50),
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    requires_restart BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER REFERENCES police_users(user_id)
);

CREATE INDEX idx_system_settings_category ON system_settings(category);

COMMENT ON TABLE system_settings IS 'Centralized system configuration including ML and verification settings';

-- ============================================================================
-- TABLE 16: activity_logs
-- Complete Audit Trail
-- ============================================================================
CREATE TABLE activity_logs (
    log_id BIGSERIAL PRIMARY KEY,
    actor_type VARCHAR(15) NOT NULL CHECK (actor_type IN ('system', 'device', 'police_user', 'ml_model')),
    actor_id VARCHAR(50),
    action_type VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id VARCHAR(50),
    action_details JSON,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    request_id CHAR(36),
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_activity_logs_actor ON activity_logs(actor_type, actor_id);
CREATE INDEX idx_activity_logs_action ON activity_logs(action_type);
CREATE INDEX idx_activity_logs_entity ON activity_logs(entity_type, entity_id);
CREATE INDEX idx_activity_logs_created ON activity_logs(created_at);

COMMENT ON TABLE activity_logs IS 'Complete audit trail for security and compliance';

-- ============================================================================
-- DEFAULT SYSTEM SETTINGS
-- ============================================================================
INSERT INTO system_settings (setting_key, setting_value, value_type, category, description, is_public) VALUES
-- Verification Rules
('location_accuracy_threshold', '100', 'number', 'verification', 'Maximum GPS accuracy in meters for location check (Rule 1)', FALSE),
('motion_score_threshold', '30', 'number', 'verification', 'Minimum motion score for motion check (Rule 2)', FALSE),
('duplicate_radius_meters', '200', 'number', 'verification', 'Radius for duplicate detection (Rule 3)', FALSE),
('duplicate_time_window_hours', '24', 'number', 'verification', 'Time window for duplicate detection (Rule 3)', FALSE),
-- ML Settings
('ml_enabled', 'true', 'boolean', 'ml', 'Enable ML enhancement for verification', FALSE),
('ml_trust_threshold', '0.3', 'number', 'ml', 'Minimum ML trust score for auto-verification', FALSE),
('ml_auto_reject_threshold', '0.1', 'number', 'ml', 'Auto-reject reports below this ML trust score', FALSE),
('ml_retrain_frequency_days', '7', 'number', 'ml', 'How often to retrain ML models (days)', FALSE),
-- Rwanda Boundaries (for location verification)
('rwanda_lat_min', '-2.84', 'number', 'geography', 'Rwanda minimum latitude', FALSE),
('rwanda_lat_max', '-1.04', 'number', 'geography', 'Rwanda maximum latitude', FALSE),
('rwanda_lng_min', '28.86', 'number', 'geography', 'Rwanda minimum longitude', FALSE),
('rwanda_lng_max', '30.90', 'number', 'geography', 'Rwanda maximum longitude', FALSE),
-- App Settings
('app_name', 'TrustBond', 'string', 'app', 'Application name', TRUE),
('app_version', '2.0.0', 'string', 'app', 'Current application version', TRUE),
('maintenance_mode', 'false', 'boolean', 'app', 'Enable maintenance mode', TRUE),
('max_evidence_files', '5', 'number', 'app', 'Maximum evidence files per report', TRUE),
('max_file_size_mb', '50', 'number', 'app', 'Maximum file size in MB', TRUE);

-- ============================================================================
-- DEFAULT INCIDENT TYPES (Categories and Sub-types)
-- ============================================================================

-- Categories (parent_id = NULL)
INSERT INTO incident_types (name, description, icon_name, color_hex, severity_level, display_order, is_active) VALUES
('Theft', 'Property theft incidents', 'shopping_bag', '#F44336', NULL, 1, TRUE),
('Violence', 'Violent incidents and assaults', 'warning', '#E91E63', NULL, 2, TRUE),
('Traffic', 'Traffic-related incidents', 'directions_car', '#FF9800', NULL, 3, TRUE),
('Vandalism', 'Property damage and vandalism', 'broken_image', '#9C27B0', NULL, 4, TRUE),
('Fraud', 'Fraud and scam incidents', 'account_balance', '#3F51B5', NULL, 5, TRUE),
('Drugs', 'Drug-related incidents', 'medication', '#795548', NULL, 6, TRUE),
('Public Order', 'Public disturbance and disorder', 'groups', '#607D8B', NULL, 7, TRUE),
('Emergency', 'General emergencies', 'emergency', '#FF5722', NULL, 8, TRUE);

-- Sub-types for Theft (parent_id = 1)
INSERT INTO incident_types (parent_id, name, description, icon_name, color_hex, severity_level, display_order, is_active) VALUES
(1, 'Pickpocketing', 'Theft of personal items from person', 'back_hand', '#F44336', 2, 1, TRUE),
(1, 'Vehicle Break-in', 'Theft from vehicles', 'car_crash', '#F44336', 4, 2, TRUE),
(1, 'Home Burglary', 'Breaking and entering homes', 'home', '#F44336', 5, 3, TRUE),
(1, 'Phone Snatching', 'Mobile phone theft', 'smartphone', '#F44336', 3, 4, TRUE),
(1, 'Shoplifting', 'Theft from stores', 'store', '#F44336', 2, 5, TRUE);

-- Sub-types for Violence (parent_id = 2)
INSERT INTO incident_types (parent_id, name, description, icon_name, color_hex, severity_level, display_order, is_active) VALUES
(2, 'Assault', 'Physical attack on person', 'sports_mma', '#E91E63', 5, 1, TRUE),
(2, 'Domestic Violence', 'Violence in domestic setting', 'family_restroom', '#E91E63', 5, 2, TRUE),
(2, 'Armed Robbery', 'Robbery with weapons', 'gavel', '#E91E63', 5, 3, TRUE),
(2, 'Harassment', 'Intimidation or harassment', 'record_voice_over', '#E91E63', 3, 4, TRUE),
(2, 'Threats', 'Verbal or written threats', 'campaign', '#E91E63', 3, 5, TRUE);

-- Sub-types for Traffic (parent_id = 3)
INSERT INTO incident_types (parent_id, name, description, icon_name, color_hex, severity_level, display_order, is_active) VALUES
(3, 'Accident with Injuries', 'Traffic accident with injuries', 'personal_injury', '#FF9800', 5, 1, TRUE),
(3, 'Minor Accident', 'Traffic accident without injuries', 'minor_crash', '#FF9800', 2, 2, TRUE),
(3, 'Hit and Run', 'Driver fled accident scene', 'directions_run', '#FF9800', 4, 3, TRUE),
(3, 'Reckless Driving', 'Dangerous driving behavior', 'speed', '#FF9800', 3, 4, TRUE),
(3, 'DUI Suspected', 'Suspected drunk driving', 'local_bar', '#FF9800', 4, 5, TRUE);

-- Sub-types for Vandalism (parent_id = 4)
INSERT INTO incident_types (parent_id, name, description, icon_name, color_hex, severity_level, display_order, is_active) VALUES
(4, 'Property Damage', 'Intentional damage to property', 'dangerous', '#9C27B0', 3, 1, TRUE),
(4, 'Graffiti', 'Unauthorized graffiti', 'format_paint', '#9C27B0', 2, 2, TRUE),
(4, 'Vehicle Damage', 'Damage to vehicles', 'car_repair', '#9C27B0', 3, 3, TRUE),
(4, 'Public Property', 'Damage to public infrastructure', 'domain', '#9C27B0', 3, 4, TRUE);

-- Sub-types for Fraud (parent_id = 5)
INSERT INTO incident_types (parent_id, name, description, icon_name, color_hex, severity_level, display_order, is_active) VALUES
(5, 'Mobile Money Scam', 'Mobile money fraud', 'phone_android', '#3F51B5', 4, 1, TRUE),
(5, 'Identity Theft', 'Identity fraud', 'badge', '#3F51B5', 4, 2, TRUE),
(5, 'Online Fraud', 'Internet-based scams', 'computer', '#3F51B5', 3, 3, TRUE),
(5, 'Business Fraud', 'Commercial fraud', 'business', '#3F51B5', 4, 4, TRUE);

-- Sub-types for Drugs (parent_id = 6)
INSERT INTO incident_types (parent_id, name, description, icon_name, color_hex, severity_level, display_order, is_active) VALUES
(6, 'Drug Dealing', 'Drug sales activity', 'local_pharmacy', '#795548', 5, 1, TRUE),
(6, 'Drug Use', 'Public drug use', 'smoke_free', '#795548', 3, 2, TRUE),
(6, 'Drug Production', 'Drug manufacturing', 'science', '#795548', 5, 3, TRUE);

-- Sub-types for Public Order (parent_id = 7)
INSERT INTO incident_types (parent_id, name, description, icon_name, color_hex, severity_level, display_order, is_active) VALUES
(7, 'Noise Disturbance', 'Excessive noise complaints', 'volume_up', '#607D8B', 2, 1, TRUE),
(7, 'Public Intoxication', 'Drunk and disorderly', 'liquor', '#607D8B', 2, 2, TRUE),
(7, 'Illegal Gathering', 'Unauthorized public gathering', 'groups', '#607D8B', 3, 3, TRUE),
(7, 'Suspicious Activity', 'General suspicious behavior', 'visibility', '#607D8B', 2, 4, TRUE);

-- Sub-types for Emergency (parent_id = 8)
INSERT INTO incident_types (parent_id, name, description, icon_name, color_hex, severity_level, display_order, is_active) VALUES
(8, 'Fire', 'Fire emergency', 'local_fire_department', '#FF5722', 5, 1, TRUE),
(8, 'Medical Emergency', 'Medical assistance needed', 'medical_services', '#FF5722', 5, 2, TRUE),
(8, 'Missing Person', 'Person reported missing', 'person_search', '#FF5722', 4, 3, TRUE),
(8, 'Natural Disaster', 'Flood, earthquake, etc.', 'flood', '#FF5722', 5, 4, TRUE);

-- ============================================================================
-- FUNCTIONS FOR AUTO-UPDATING TIMESTAMPS
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to tables with updated_at column
CREATE TRIGGER update_police_users_updated_at BEFORE UPDATE ON police_users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_unified_cases_updated_at BEFORE UPDATE ON unified_cases FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_hotspots_updated_at BEFORE UPDATE ON hotspots FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_system_settings_updated_at BEFORE UPDATE ON system_settings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- FUNCTION: Generate Case Number
-- ============================================================================
CREATE OR REPLACE FUNCTION generate_case_number()
RETURNS TRIGGER AS $$
DECLARE
    daily_count INTEGER;
    date_part VARCHAR(10);
BEGIN
    date_part := TO_CHAR(CURRENT_DATE, 'YYYY-MMDD');
    SELECT COUNT(*) + 1 INTO daily_count FROM unified_cases WHERE DATE(created_at) = CURRENT_DATE;
    NEW.case_number := 'CASE-' || date_part || '-' || LPAD(daily_count::TEXT, 3, '0');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_generate_case_number
    BEFORE INSERT ON unified_cases
    FOR EACH ROW
    WHEN (NEW.case_number IS NULL)
    EXECUTE FUNCTION generate_case_number();

-- ============================================================================
-- VIEW: Case Summary for Dashboard
-- ============================================================================
CREATE OR REPLACE VIEW v_case_summary AS
SELECT 
    uc.case_id,
    uc.case_number,
    uc.incident_date,
    uc.case_status,
    uc.priority,
    uc.verification_status,
    uc.ml_priority_score,
    uc.ml_confidence,
    uc.report_count,
    uc.evidence_count,
    uc.combined_trust_score,
    it.name AS incident_type,
    pit.name AS incident_category,
    l.name AS location_name,
    l.location_type,
    pu.full_name AS assigned_officer,
    uc.created_at,
    uc.updated_at
FROM unified_cases uc
LEFT JOIN incident_types it ON uc.incident_type_id = it.type_id
LEFT JOIN incident_types pit ON it.parent_id = pit.type_id
LEFT JOIN locations l ON uc.location_id = l.location_id
LEFT JOIN police_users pu ON uc.assigned_officer_id = pu.user_id
ORDER BY 
    CASE uc.priority 
        WHEN 'urgent' THEN 1 
        WHEN 'high' THEN 2 
        WHEN 'normal' THEN 3 
        WHEN 'low' THEN 4 
    END,
    uc.ml_priority_score DESC,
    uc.created_at DESC;

-- ============================================================================
-- VIEW: Report Details with ML Predictions
-- ============================================================================
CREATE OR REPLACE VIEW v_report_details AS
SELECT 
    ir.report_id,
    ir.case_id,
    ir.device_id,
    ir.title,
    ir.description,
    ir.latitude,
    ir.longitude,
    ir.report_status,
    ir.location_check_passed,
    ir.motion_check_passed,
    ir.motion_score,
    ir.is_duplicate,
    ir.is_grouped,
    ir.reported_at,
    ir.incident_occurred_at,
    it.name AS incident_type,
    d.current_trust_score AS device_trust_score,
    d.total_reports AS device_total_reports,
    d.verified_reports AS device_verified_reports,
    mp.ml_trust_score,
    mp.ml_confidence,
    mp.predicted_priority,
    mp.predicted_validity,
    mp.anomaly_score,
    mp.anomaly_flags
FROM incident_reports ir
LEFT JOIN incident_types it ON ir.incident_type_id = it.type_id
LEFT JOIN devices d ON ir.device_id = d.device_id
LEFT JOIN ml_predictions mp ON ir.report_id = mp.report_id;

-- ============================================================================
-- VIEW: Hotspot Analytics
-- ============================================================================
CREATE OR REPLACE VIEW v_hotspot_analytics AS
SELECT 
    h.hotspot_id,
    h.hotspot_name,
    h.latitude,
    h.longitude,
    h.radius_meters,
    h.case_count,
    h.total_reports,
    h.risk_level,
    h.priority_score,
    h.status,
    h.peak_hour,
    h.peak_day_of_week,
    it.name AS dominant_incident_type,
    h.dominant_type_percentage,
    l.name AS location_name,
    l.location_type,
    pu.full_name AS assigned_officer,
    h.first_incident_at,
    h.last_incident_at,
    h.detected_at
FROM hotspots h
LEFT JOIN incident_types it ON h.dominant_incident_type_id = it.type_id
LEFT JOIN locations l ON h.location_id = l.location_id
LEFT JOIN police_users pu ON h.assigned_officer_id = pu.user_id;

-- ============================================================================
-- SCHEMA COMPLETE - 16 Tables Created
-- ============================================================================

-- Summary of tables created:
-- 1. devices - Anonymous reporter devices
-- 2. locations - Rwanda geography hierarchy
-- 3. incident_types - Incident taxonomy
-- 4. unified_cases - Grouped cases for police
-- 5. incident_reports - Individual citizen reports
-- 6. report_evidence - Evidence files
-- 7. ml_models - ML models for verification
-- 8. ml_predictions - ML analysis results
-- 9. ml_training_data - Verified reports for training
-- 10. police_users - Police authentication
-- 11. notifications - Police alerts
-- 12. hotspots - Crime clusters
-- 13. daily_statistics - Pre-aggregated analytics
-- 14. public_safety_zones - Public safety map
-- 15. system_settings - Configuration
-- 16. activity_logs - Audit trail
