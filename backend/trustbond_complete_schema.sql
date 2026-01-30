-- TrustBond Complete Database Schema
-- Generated from comprehensive database design specification
-- All 33 tables with complete relationships and constraints

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- SECTION 1: CORE DEVICE MANAGEMENT
-- ============================================================================

-- Devices table
CREATE TABLE IF NOT EXISTS devices (
    device_id CHAR(36) PRIMARY KEY,
    device_fingerprint VARCHAR(255) UNIQUE NOT NULL,
    platform VARCHAR(20) NOT NULL CHECK (platform IN ('android', 'ios')),
    app_version VARCHAR(20),
    os_version VARCHAR(30),
    device_language VARCHAR(10) DEFAULT 'en',
    current_trust_score DECIMAL(5, 2) DEFAULT 50.00,
    total_reports INTEGER DEFAULT 0,
    trusted_reports INTEGER DEFAULT 0,
    suspicious_reports INTEGER DEFAULT 0,
    false_reports INTEGER DEFAULT 0,
    is_blocked BOOLEAN DEFAULT FALSE,
    block_reason TEXT,
    blocked_at TIMESTAMP,
    blocked_by INTEGER,
    push_token_encrypted VARCHAR(500),
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active_at TIMESTAMP,
    last_report_at TIMESTAMP
);

CREATE INDEX idx_device_fingerprint ON devices(device_fingerprint);
CREATE INDEX idx_device_registered_at ON devices(registered_at);

-- Device trust history
CREATE TABLE IF NOT EXISTS device_trust_history (
    history_id SERIAL PRIMARY KEY,
    device_id CHAR(36) NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
    trust_score DECIMAL(5, 2) NOT NULL,
    total_reports INTEGER,
    trusted_reports INTEGER,
    suspicious_reports INTEGER,
    false_reports INTEGER,
    score_change DECIMAL(5, 2),
    change_reason VARCHAR(100),
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_device_trust_history_device_id ON device_trust_history(device_id);
CREATE INDEX idx_device_trust_history_calculated_at ON device_trust_history(calculated_at);

-- ============================================================================
-- SECTION 2: RWANDA ADMINISTRATIVE GEOGRAPHY
-- ============================================================================

-- Provinces
CREATE TABLE IF NOT EXISTS provinces (
    province_id SMALLINT PRIMARY KEY,
    province_name VARCHAR(50) UNIQUE NOT NULL,
    province_code CHAR(2) UNIQUE NOT NULL,
    boundary_geojson JSON,
    centroid_latitude DECIMAL(10, 8),
    centroid_longitude DECIMAL(11, 8),
    population INTEGER,
    area_sq_km DECIMAL(10, 2),
    district_count TINYINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Districts
CREATE TABLE IF NOT EXISTS districts (
    district_id SMALLINT PRIMARY KEY,
    province_id SMALLINT NOT NULL REFERENCES provinces(province_id),
    district_name VARCHAR(100) UNIQUE NOT NULL,
    district_code VARCHAR(10) UNIQUE NOT NULL,
    boundary_geojson JSON,
    centroid_latitude DECIMAL(10, 8),
    centroid_longitude DECIMAL(11, 8),
    population INTEGER,
    area_sq_km DECIMAL(10, 2),
    sector_count TINYINT DEFAULT 0,
    is_pilot_area BOOLEAN DEFAULT FALSE,
    pilot_start_date DATE,
    pilot_end_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_district_province_id ON districts(province_id);
CREATE INDEX idx_district_code ON districts(district_code);

-- Sectors
CREATE TABLE IF NOT EXISTS sectors (
    sector_id SMALLINT PRIMARY KEY,
    district_id SMALLINT NOT NULL REFERENCES districts(district_id),
    sector_name VARCHAR(100) NOT NULL,
    sector_code VARCHAR(20) UNIQUE NOT NULL,
    boundary_geojson JSON,
    centroid_latitude DECIMAL(10, 8),
    centroid_longitude DECIMAL(11, 8),
    population INTEGER,
    area_sq_km DECIMAL(10, 2),
    cell_count TINYINT DEFAULT 0,
    police_station_name VARCHAR(100),
    police_station_contact VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sector_district_id ON sectors(district_id);
CREATE INDEX idx_sector_code ON sectors(sector_code);

-- Cells
CREATE TABLE IF NOT EXISTS cells (
    cell_id SMALLINT PRIMARY KEY,
    sector_id SMALLINT NOT NULL REFERENCES sectors(sector_id),
    cell_name VARCHAR(100) NOT NULL,
    cell_code VARCHAR(30) UNIQUE NOT NULL,
    boundary_geojson JSON,
    centroid_latitude DECIMAL(10, 8),
    centroid_longitude DECIMAL(11, 8),
    population INTEGER,
    area_sq_km DECIMAL(8, 2),
    cell_leader_title VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cell_sector_id ON cells(sector_id);
CREATE INDEX idx_cell_code ON cells(cell_code);

-- Villages
CREATE TABLE IF NOT EXISTS villages (
    village_id SERIAL PRIMARY KEY,
    cell_id SMALLINT NOT NULL REFERENCES cells(cell_id),
    village_name VARCHAR(100) NOT NULL,
    village_code VARCHAR(40) UNIQUE NOT NULL,
    centroid_latitude DECIMAL(10, 8),
    centroid_longitude DECIMAL(11, 8),
    population INTEGER,
    household_count INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_village_cell_id ON villages(cell_id);
CREATE INDEX idx_village_code ON villages(village_code);

-- ============================================================================
-- SECTION 3: POLICE USER MANAGEMENT (must be created before referencing)
-- ============================================================================

CREATE TABLE IF NOT EXISTS police_users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    badge_number VARCHAR(50) UNIQUE,
    rank VARCHAR(50),
    phone_number VARCHAR(20),
    profile_photo_path VARCHAR(500),
    role VARCHAR(20) DEFAULT 'officer' CHECK (role IN ('super_admin', 'admin', 'commander', 'officer', 'analyst', 'viewer')),
    permissions JSON,
    assigned_district_id SMALLINT REFERENCES districts(district_id),
    assigned_sector_id SMALLINT REFERENCES sectors(sector_id),
    assigned_unit VARCHAR(100),
    jurisdiction_district_ids JSON,
    can_access_all_districts BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMP,
    verified_by INTEGER,
    two_factor_enabled BOOLEAN DEFAULT FALSE,
    two_factor_secret VARCHAR(100),
    two_factor_backup_codes JSON,
    password_changed_at TIMESTAMP,
    must_change_password BOOLEAN DEFAULT FALSE,
    failed_login_attempts TINYINT DEFAULT 0,
    account_locked_until TIMESTAMP,
    last_failed_login_at TIMESTAMP,
    last_login_at TIMESTAMP,
    last_login_ip VARCHAR(45),
    login_count INTEGER DEFAULT 0,
    preferred_language VARCHAR(10) DEFAULT 'en',
    notification_preferences JSON,
    dashboard_settings JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES police_users(user_id)
);

CREATE INDEX idx_police_user_username ON police_users(username);
CREATE INDEX idx_police_user_email ON police_users(email);
CREATE INDEX idx_police_user_assigned_district_id ON police_users(assigned_district_id);

-- Add foreign key for blocked_by in devices
ALTER TABLE devices ADD CONSTRAINT fk_devices_blocked_by 
    FOREIGN KEY (blocked_by) REFERENCES police_users(user_id);

-- Police sessions
CREATE TABLE IF NOT EXISTS police_sessions (
    session_id CHAR(36) PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES police_users(user_id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    refresh_token_hash VARCHAR(255),
    ip_address VARCHAR(45),
    user_agent TEXT,
    device_info JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    revoked_at TIMESTAMP,
    revoked_reason VARCHAR(100)
);

CREATE INDEX idx_session_user_id ON police_sessions(user_id);

-- ============================================================================
-- SECTION 4: INCIDENT TAXONOMY
-- ============================================================================

-- Incident categories
CREATE TABLE IF NOT EXISTS incident_categories (
    category_id SMALLINT PRIMARY KEY,
    category_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    icon_name VARCHAR(50),
    color_hex VARCHAR(7),
    display_order TINYINT,
    is_active BOOLEAN DEFAULT TRUE,
    requires_evidence BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Incident types
CREATE TABLE IF NOT EXISTS incident_types (
    type_id SMALLINT PRIMARY KEY,
    category_id SMALLINT NOT NULL REFERENCES incident_categories(category_id),
    type_name VARCHAR(100) NOT NULL,
    description TEXT,
    severity_level TINYINT,
    response_priority VARCHAR(20) DEFAULT 'normal' CHECK (response_priority IN ('low', 'normal', 'high', 'urgent')),
    requires_photo BOOLEAN DEFAULT FALSE,
    requires_video BOOLEAN DEFAULT FALSE,
    min_description_length INTEGER DEFAULT 20,
    icon_name VARCHAR(50),
    display_order TINYINT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_incident_type_category_id ON incident_types(category_id);

-- ============================================================================
-- SECTION 5: MACHINE LEARNING SYSTEM
-- ============================================================================

-- ML Models
CREATE TABLE IF NOT EXISTS ml_models (
    model_id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(20) NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    model_file_path VARCHAR(500),
    model_file_hash VARCHAR(64),
    model_size_kb INTEGER,
    trained_at TIMESTAMP,
    training_dataset_size INTEGER,
    training_duration_seconds INTEGER,
    accuracy DECIMAL(5, 4),
    precision_score DECIMAL(5, 4),
    recall_score DECIMAL(5, 4),
    f1_score DECIMAL(5, 4),
    auc_roc DECIMAL(5, 4),
    metrics_by_class JSON,
    confusion_matrix JSON,
    feature_names JSON,
    feature_importance JSON,
    threshold_trusted DECIMAL(5, 2) DEFAULT 70,
    threshold_suspicious DECIMAL(5, 2) DEFAULT 40,
    is_active BOOLEAN DEFAULT TRUE,
    is_champion BOOLEAN DEFAULT FALSE,
    deployed_at TIMESTAMP,
    deprecated_at TIMESTAMP,
    deprecation_reason VARCHAR(255),
    total_predictions INTEGER DEFAULT 0,
    correct_predictions INTEGER DEFAULT 0,
    avg_inference_time_ms DECIMAL(8, 2),
    training_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES police_users(user_id)
);

-- ============================================================================
-- SECTION 6: HOTSPOT DETECTION & CLUSTERING
-- ============================================================================

-- Clustering runs
CREATE TABLE IF NOT EXISTS clustering_runs (
    run_id CHAR(36) PRIMARY KEY,
    district_id SMALLINT REFERENCES districts(district_id),
    epsilon_meters DECIMAL(10, 2) NOT NULL,
    min_samples INTEGER NOT NULL,
    trust_weight_enabled BOOLEAN DEFAULT FALSE,
    min_trust_score_threshold DECIMAL(5, 2),
    total_reports_processed INTEGER,
    reports_after_filtering INTEGER,
    date_range_start TIMESTAMP,
    date_range_end TIMESTAMP,
    clusters_found INTEGER,
    noise_points INTEGER,
    avg_cluster_size DECIMAL(8, 2),
    execution_time_seconds DECIMAL(10, 2),
    status VARCHAR(20) DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed')),
    error_message TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    triggered_by INTEGER REFERENCES police_users(user_id)
);

CREATE INDEX idx_clustering_run_district_id ON clustering_runs(district_id);

-- Hotspots
CREATE TABLE IF NOT EXISTS hotspots (
    hotspot_id SERIAL PRIMARY KEY,
    cluster_label INTEGER NOT NULL,
    cluster_run_id CHAR(36) REFERENCES clustering_runs(run_id),
    centroid_latitude DECIMAL(10, 8) NOT NULL,
    centroid_longitude DECIMAL(11, 8) NOT NULL,
    boundary_geojson JSON,
    radius_meters DECIMAL(10, 2),
    area_sq_meters DECIMAL(12, 2),
    district_id SMALLINT REFERENCES districts(district_id),
    sector_id SMALLINT REFERENCES sectors(sector_id),
    cell_id SMALLINT REFERENCES cells(cell_id),
    village_id INTEGER REFERENCES villages(village_id),
    report_count INTEGER DEFAULT 0,
    unique_devices INTEGER DEFAULT 0,
    avg_trust_score DECIMAL(5, 2),
    min_trust_score DECIMAL(5, 2),
    max_trust_score DECIMAL(5, 2),
    std_trust_score DECIMAL(5, 2),
    weighted_trust_density DECIMAL(10, 4),
    trusted_report_count INTEGER DEFAULT 0,
    suspicious_report_count INTEGER DEFAULT 0,
    false_report_count INTEGER DEFAULT 0,
    police_verified_count INTEGER DEFAULT 0,
    earliest_incident_at TIMESTAMP,
    latest_incident_at TIMESTAMP,
    time_span_hours INTEGER,
    peak_hour TINYINT,
    peak_day_of_week TINYINT,
    incident_type_distribution JSON,
    dominant_incident_type_id SMALLINT REFERENCES incident_types(type_id),
    dominant_incident_pct DECIMAL(5, 2),
    risk_level VARCHAR(20) DEFAULT 'low' CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    priority_score DECIMAL(5, 2),
    risk_factors JSON,
    dbscan_epsilon_meters DECIMAL(10, 2),
    dbscan_min_samples INTEGER,
    trust_weight_enabled BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    status VARCHAR(20) DEFAULT 'new' CHECK (status IN ('new', 'monitoring', 'responding', 'addressed', 'recurring')),
    is_assigned BOOLEAN DEFAULT FALSE,
    assigned_to_officer_id INTEGER REFERENCES police_users(user_id),
    assigned_to_unit VARCHAR(100),
    assigned_at TIMESTAMP,
    is_addressed BOOLEAN DEFAULT FALSE,
    addressed_at TIMESTAMP,
    addressed_by INTEGER REFERENCES police_users(user_id),
    resolution_notes TEXT,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_report_added_at TIMESTAMP
);

CREATE INDEX idx_hotspot_district_id ON hotspots(district_id);
CREATE INDEX idx_hotspot_status ON hotspots(status);
CREATE INDEX idx_hotspot_risk_level ON hotspots(risk_level);

-- Hotspot history
CREATE TABLE IF NOT EXISTS hotspot_history (
    history_id SERIAL PRIMARY KEY,
    hotspot_id INTEGER NOT NULL REFERENCES hotspots(hotspot_id) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL,
    report_count INTEGER,
    avg_trust_score DECIMAL(5, 2),
    risk_level VARCHAR(20) CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    priority_score DECIMAL(5, 2),
    report_count_change INTEGER,
    trust_score_change DECIMAL(5, 2),
    risk_level_changed BOOLEAN,
    trend_direction VARCHAR(20) CHECK (trend_direction IN ('improving', 'stable', 'worsening')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_hotspot_history_hotspot_id ON hotspot_history(hotspot_id);

-- ============================================================================
-- SECTION 7: INCIDENT REPORTS (MAIN TRANSACTION TABLE)
-- ============================================================================

CREATE TABLE IF NOT EXISTS incident_reports (
    report_id CHAR(36) PRIMARY KEY,
    device_id CHAR(36) NOT NULL REFERENCES devices(device_id),
    incident_type_id SMALLINT NOT NULL REFERENCES incident_types(type_id),
    title VARCHAR(200),
    description TEXT NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    location_accuracy_meters DECIMAL(8, 2),
    altitude_meters DECIMAL(8, 2),
    location_source VARCHAR(20) DEFAULT 'gps' CHECK (location_source IN ('gps', 'network', 'manual')),
    district_id SMALLINT REFERENCES districts(district_id),
    sector_id SMALLINT REFERENCES sectors(sector_id),
    cell_id SMALLINT REFERENCES cells(cell_id),
    village_id INTEGER REFERENCES villages(village_id),
    address_description VARCHAR(255),
    reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    incident_occurred_at TIMESTAMP NOT NULL,
    incident_time_approximate BOOLEAN DEFAULT FALSE,
    photo_count INTEGER DEFAULT 0,
    video_count INTEGER DEFAULT 0,
    audio_count INTEGER DEFAULT 0,
    total_evidence_size_kb INTEGER DEFAULT 0,
    accelerometer_data JSON,
    gyroscope_data JSON,
    magnetometer_data JSON,
    device_motion_score DECIMAL(5, 2),
    device_orientation VARCHAR(20),
    battery_level TINYINT,
    network_type VARCHAR(20),
    rule_check_status VARCHAR(20) DEFAULT 'pending' CHECK (rule_check_status IN ('pending', 'passed', 'failed', 'partial')),
    rule_check_completed_at TIMESTAMP,
    rules_passed INTEGER DEFAULT 0,
    rules_failed INTEGER DEFAULT 0,
    rules_total INTEGER DEFAULT 0,
    rule_failure_reasons JSON,
    is_auto_rejected BOOLEAN DEFAULT FALSE,
    ml_model_id INTEGER REFERENCES ml_models(model_id),
    ml_trust_score DECIMAL(5, 2),
    ml_confidence DECIMAL(5, 4),
    ml_feature_vector JSON,
    ml_scored_at TIMESTAMP,
    trust_classification VARCHAR(20) DEFAULT 'Pending' CHECK (trust_classification IN ('Trusted', 'Suspicious', 'False', 'Pending')),
    classification_reason VARCHAR(255),
    police_verified BOOLEAN DEFAULT FALSE,
    police_verified_at TIMESTAMP,
    police_verified_by INTEGER REFERENCES police_users(user_id),
    police_verification_status VARCHAR(30) DEFAULT 'pending' CHECK (police_verification_status IN ('pending', 'confirmed', 'false', 'duplicate', 'insufficient_info')),
    police_verification_notes TEXT,
    police_priority VARCHAR(20) CHECK (police_priority IN ('low', 'normal', 'high', 'urgent')),
    report_status VARCHAR(30) DEFAULT 'submitted' CHECK (report_status IN ('submitted', 'rule_checking', 'ml_scoring', 'pending_review', 'investigating', 'resolved', 'rejected')),
    processing_stage VARCHAR(30) DEFAULT 'received' CHECK (processing_stage IN ('received', 'rule_validation', 'ml_scoring', 'clustering', 'ready_for_review', 'in_review', 'completed')),
    is_duplicate BOOLEAN DEFAULT FALSE,
    duplicate_of_report_id CHAR(36) REFERENCES incident_reports(report_id),
    duplicate_confidence DECIMAL(5, 2),
    assigned_officer_id INTEGER REFERENCES police_users(user_id),
    assigned_unit VARCHAR(100),
    assigned_at TIMESTAMP,
    resolved_at TIMESTAMP,
    resolution_type VARCHAR(30) CHECK (resolution_type IN ('action_taken', 'no_action_needed', 'referred', 'false_report', 'duplicate')),
    resolution_notes TEXT,
    hotspot_id INTEGER REFERENCES hotspots(hotspot_id),
    added_to_hotspot_at TIMESTAMP,
    app_version VARCHAR(20),
    submission_ip_hash VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_report_device_id ON incident_reports(device_id);
CREATE INDEX idx_report_incident_type_id ON incident_reports(incident_type_id);
CREATE INDEX idx_report_district_id ON incident_reports(district_id);
CREATE INDEX idx_report_reported_at ON incident_reports(reported_at);
CREATE INDEX idx_report_status ON incident_reports(report_status);
CREATE INDEX idx_report_trust_classification ON incident_reports(trust_classification);

-- ============================================================================
-- SECTION 8: EVIDENCE MANAGEMENT
-- ============================================================================

CREATE TABLE IF NOT EXISTS report_evidence (
    evidence_id CHAR(36) PRIMARY KEY,
    report_id CHAR(36) NOT NULL REFERENCES incident_reports(report_id) ON DELETE CASCADE,
    evidence_type VARCHAR(20) NOT NULL CHECK (evidence_type IN ('photo', 'video', 'audio')),
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size_bytes INTEGER,
    mime_type VARCHAR(100),
    duration_seconds INTEGER,
    width_pixels INTEGER,
    height_pixels INTEGER,
    file_hash_sha256 VARCHAR(64) UNIQUE,
    file_hash_perceptual VARCHAR(64),
    captured_at TIMESTAMP,
    capture_latitude DECIMAL(10, 8),
    capture_longitude DECIMAL(11, 8),
    camera_metadata JSON,
    blur_score DECIMAL(5, 2),
    brightness_score DECIMAL(5, 2),
    is_low_quality BOOLEAN DEFAULT FALSE,
    quality_issues JSON,
    content_moderation_status VARCHAR(20) DEFAULT 'pending' CHECK (content_moderation_status IN ('pending', 'approved', 'flagged', 'rejected')),
    has_inappropriate_content BOOLEAN DEFAULT FALSE,
    moderation_flags JSON,
    moderated_at TIMESTAMP,
    moderated_by INTEGER REFERENCES police_users(user_id),
    is_processed BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP,
    deletion_reason VARCHAR(100),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_evidence_report_id ON report_evidence(report_id);
CREATE INDEX idx_evidence_evidence_type ON report_evidence(evidence_type);

-- ============================================================================
-- SECTION 9: VERIFICATION RULES ENGINE
-- ============================================================================

CREATE TABLE IF NOT EXISTS verification_rules (
    rule_id SERIAL PRIMARY KEY,
    rule_name VARCHAR(100) UNIQUE NOT NULL,
    rule_code VARCHAR(50) UNIQUE NOT NULL,
    rule_description TEXT,
    rule_category VARCHAR(20) NOT NULL CHECK (rule_category IN ('spatial', 'temporal', 'motion', 'evidence', 'device', 'content')),
    rule_parameters JSON,
    severity VARCHAR(20) DEFAULT 'low' CHECK (severity IN ('info', 'low', 'medium', 'high', 'critical')),
    is_blocking BOOLEAN DEFAULT FALSE,
    failure_score_penalty DECIMAL(5, 2) DEFAULT 0,
    execution_order SMALLINT,
    is_active BOOLEAN DEFAULT TRUE,
    applies_to_categories JSON,
    applies_to_districts JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES police_users(user_id)
);

CREATE TABLE IF NOT EXISTS rule_execution_logs (
    execution_id SERIAL PRIMARY KEY,
    report_id CHAR(36) NOT NULL REFERENCES incident_reports(report_id) ON DELETE CASCADE,
    rule_id INTEGER NOT NULL REFERENCES verification_rules(rule_id),
    passed BOOLEAN NOT NULL,
    input_values JSON,
    threshold_values JSON,
    failure_reason TEXT,
    execution_time_ms DECIMAL(8, 2),
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rule_execution_report_id ON rule_execution_logs(report_id);
CREATE INDEX idx_rule_execution_rule_id ON rule_execution_logs(rule_id);

-- ============================================================================
-- SECTION 10: ML PREDICTIONS & TRAINING DATA
-- ============================================================================

CREATE TABLE IF NOT EXISTS ml_predictions (
    prediction_id CHAR(36) PRIMARY KEY,
    report_id CHAR(36) NOT NULL UNIQUE REFERENCES incident_reports(report_id) ON DELETE CASCADE,
    model_id INTEGER NOT NULL REFERENCES ml_models(model_id),
    feature_vector JSON,
    predicted_score DECIMAL(5, 2) NOT NULL,
    predicted_class VARCHAR(20) NOT NULL CHECK (predicted_class IN ('Trusted', 'Suspicious', 'False')),
    confidence DECIMAL(5, 4),
    class_probabilities JSON,
    actual_class VARCHAR(20) CHECK (actual_class IN ('Trusted', 'Suspicious', 'False')),
    is_correct BOOLEAN,
    inference_time_ms DECIMAL(8, 2),
    predicted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified_at TIMESTAMP
);

CREATE INDEX idx_prediction_report_id ON ml_predictions(report_id);
CREATE INDEX idx_prediction_model_id ON ml_predictions(model_id);

CREATE TABLE IF NOT EXISTS ml_training_data (
    training_id SERIAL PRIMARY KEY,
    report_id CHAR(36) NOT NULL REFERENCES incident_reports(report_id),
    feature_vector JSON,
    label VARCHAR(20) NOT NULL CHECK (label IN ('Trusted', 'Suspicious', 'False')),
    label_confidence DECIMAL(5, 2),
    labeled_by INTEGER REFERENCES police_users(user_id),
    labeled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    label_source VARCHAR(30) DEFAULT 'police_verification' CHECK (label_source IN ('police_verification', 'expert_review', 'consensus', 'auto')),
    dataset_split VARCHAR(20) CHECK (dataset_split IN ('train', 'validation', 'test', 'holdout')),
    assigned_to_split_at TIMESTAMP,
    used_in_model_version VARCHAR(20),
    used_at TIMESTAMP,
    is_high_quality BOOLEAN DEFAULT TRUE,
    quality_issues JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_training_data_report_id ON ml_training_data(report_id);
CREATE INDEX idx_training_data_dataset_split ON ml_training_data(dataset_split);

-- ============================================================================
-- SECTION 11: HOTSPOT REPORTS BRIDGE TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS hotspot_reports (
    hotspot_id INTEGER NOT NULL REFERENCES hotspots(hotspot_id) ON DELETE CASCADE,
    report_id CHAR(36) NOT NULL REFERENCES incident_reports(report_id) ON DELETE CASCADE,
    trust_weight DECIMAL(5, 4),
    distance_to_centroid_meters DECIMAL(10, 2),
    is_core_point BOOLEAN DEFAULT FALSE,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (hotspot_id, report_id)
);

CREATE INDEX idx_hotspot_report_hotspot_id ON hotspot_reports(hotspot_id);

-- ============================================================================
-- SECTION 12: NOTIFICATIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS notifications (
    notification_id SERIAL PRIMARY KEY,
    recipient_user_id INTEGER NOT NULL REFERENCES police_users(user_id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL CHECK (notification_type IN ('new_report', 'high_trust_report', 'suspicious_report', 'hotspot_detected', 'hotspot_escalated', 'assignment', 'verification_needed', 'system_alert', 'model_update', 'weekly_summary')),
    title VARCHAR(200) NOT NULL,
    message TEXT,
    report_id CHAR(36) REFERENCES incident_reports(report_id),
    hotspot_id INTEGER REFERENCES hotspots(hotspot_id),
    priority VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    delivery_channels JSON,
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,
    is_dismissed BOOLEAN DEFAULT FALSE,
    dismissed_at TIMESTAMP,
    action_taken VARCHAR(100),
    action_taken_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE INDEX idx_notification_recipient_user_id ON notifications(recipient_user_id);
CREATE INDEX idx_notification_created_at ON notifications(created_at);

-- ============================================================================
-- SECTION 13: ANALYTICS & STATISTICS
-- ============================================================================

CREATE TABLE IF NOT EXISTS daily_statistics (
    stat_id SERIAL PRIMARY KEY,
    stat_date DATE NOT NULL,
    district_id SMALLINT REFERENCES districts(district_id),
    sector_id SMALLINT REFERENCES sectors(sector_id),
    total_reports INTEGER DEFAULT 0,
    trusted_reports INTEGER DEFAULT 0,
    suspicious_reports INTEGER DEFAULT 0,
    false_reports INTEGER DEFAULT 0,
    pending_reports INTEGER DEFAULT 0,
    avg_trust_score DECIMAL(5, 2),
    median_trust_score DECIMAL(5, 2),
    reports_with_photo INTEGER DEFAULT 0,
    reports_with_video INTEGER DEFAULT 0,
    reports_police_verified INTEGER DEFAULT 0,
    reports_confirmed INTEGER DEFAULT 0,
    reports_rejected INTEGER DEFAULT 0,
    verification_rate DECIMAL(5, 2),
    avg_verification_time_hours DECIMAL(8, 2),
    active_hotspots INTEGER DEFAULT 0,
    new_hotspots INTEGER DEFAULT 0,
    resolved_hotspots INTEGER DEFAULT 0,
    critical_hotspots INTEGER DEFAULT 0,
    unique_reporting_devices INTEGER DEFAULT 0,
    new_devices INTEGER DEFAULT 0,
    blocked_devices INTEGER DEFAULT 0,
    avg_device_trust_score DECIMAL(5, 2),
    reports_assigned INTEGER DEFAULT 0,
    reports_resolved INTEGER DEFAULT 0,
    avg_resolution_time_hours DECIMAL(8, 2),
    incident_type_counts JSON,
    top_incident_type_id SMALLINT REFERENCES incident_types(type_id),
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_daily_stat_stat_date ON daily_statistics(stat_date);
CREATE INDEX idx_daily_stat_district_id ON daily_statistics(district_id);

CREATE TABLE IF NOT EXISTS incident_type_trends (
    trend_id SERIAL PRIMARY KEY,
    incident_type_id SMALLINT NOT NULL REFERENCES incident_types(type_id),
    district_id SMALLINT REFERENCES districts(district_id),
    week_start_date DATE NOT NULL,
    week_end_date DATE NOT NULL,
    year_week VARCHAR(7) NOT NULL,
    report_count INTEGER,
    trusted_count INTEGER,
    suspicious_count INTEGER,
    false_count INTEGER,
    avg_trust_score DECIMAL(5, 2),
    police_verified_count INTEGER,
    prev_week_count INTEGER,
    count_change INTEGER,
    count_change_pct DECIMAL(6, 2),
    trend_direction VARCHAR(20) CHECK (trend_direction IN ('increasing', 'stable', 'decreasing')),
    associated_hotspots INTEGER,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trend_incident_type_id ON incident_type_trends(incident_type_id);
CREATE INDEX idx_trend_week_start_date ON incident_type_trends(week_start_date);

-- ============================================================================
-- SECTION 14: PUBLIC COMMUNITY SAFETY MAP
-- ============================================================================

CREATE TABLE IF NOT EXISTS public_safety_zones (
    zone_id SERIAL PRIMARY KEY,
    zone_type VARCHAR(20) NOT NULL CHECK (zone_type IN ('grid', 'sector', 'cell', 'custom')),
    zone_geometry JSON,
    district_id SMALLINT REFERENCES districts(district_id),
    sector_id SMALLINT REFERENCES sectors(sector_id),
    cell_id SMALLINT REFERENCES cells(cell_id),
    grid_row INTEGER,
    grid_col INTEGER,
    grid_size_meters INTEGER,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    period_type VARCHAR(20) NOT NULL CHECK (period_type IN ('daily', 'weekly', 'monthly')),
    incident_count INTEGER,
    safety_score DECIMAL(5, 2),
    safety_level VARCHAR(20) CHECK (safety_level IN ('safe', 'moderate', 'elevated', 'high_risk')),
    incident_breakdown JSON,
    top_concern VARCHAR(100),
    trend_vs_prev_period VARCHAR(20) CHECK (trend_vs_prev_period IN ('improving', 'stable', 'worsening')),
    display_color VARCHAR(7),
    is_visible BOOLEAN DEFAULT TRUE,
    min_display_threshold INTEGER DEFAULT 3,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_public_zone_period ON public_safety_zones(period_start, period_end);

-- ============================================================================
-- SECTION 15: SYSTEM CONFIGURATION
-- ============================================================================

CREATE TABLE IF NOT EXISTS system_settings (
    setting_id SERIAL PRIMARY KEY,
    setting_category VARCHAR(30) NOT NULL CHECK (setting_category IN ('general', 'ml', 'verification', 'hotspot', 'notification', 'security', 'privacy', 'display')),
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value JSON,
    value_type VARCHAR(20) DEFAULT 'string' CHECK (value_type IN ('string', 'number', 'boolean', 'json', 'array')),
    display_name VARCHAR(200),
    description TEXT,
    validation_rules JSON,
    default_value JSON,
    requires_admin BOOLEAN DEFAULT FALSE,
    is_sensitive BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER REFERENCES police_users(user_id)
);

-- ============================================================================
-- SECTION 16: AUDIT & ACTIVITY LOGGING
-- ============================================================================

CREATE TABLE IF NOT EXISTS activity_logs (
    log_id BIGSERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES police_users(user_id),
    user_type VARCHAR(20) DEFAULT 'police' CHECK (user_type IN ('police', 'system', 'api')),
    action_type VARCHAR(50) NOT NULL,
    action_category VARCHAR(30) DEFAULT 'system' CHECK (action_category IN ('auth', 'report', 'hotspot', 'user_management', 'settings', 'ml', 'data_export', 'system')),
    action_description VARCHAR(500),
    report_id CHAR(36) REFERENCES incident_reports(report_id),
    hotspot_id INTEGER REFERENCES hotspots(hotspot_id),
    affected_user_id INTEGER REFERENCES police_users(user_id),
    affected_table VARCHAR(100),
    affected_record_id VARCHAR(100),
    old_values JSON,
    new_values JSON,
    ip_address VARCHAR(45),
    user_agent TEXT,
    session_id CHAR(36),
    was_successful BOOLEAN DEFAULT TRUE,
    failure_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_activity_log_user_id ON activity_logs(user_id);
CREATE INDEX idx_activity_log_created_at ON activity_logs(created_at);
CREATE INDEX idx_activity_log_action_category ON activity_logs(action_category);

CREATE TABLE IF NOT EXISTS data_change_audit (
    audit_id BIGSERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    record_id VARCHAR(100) NOT NULL,
    operation VARCHAR(20) NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
    old_values JSON,
    new_values JSON,
    changed_columns JSON,
    changed_by INTEGER REFERENCES police_users(user_id),
    changed_by_type VARCHAR(20) DEFAULT 'system' CHECK (changed_by_type IN ('police', 'system', 'api', 'trigger')),
    ip_address VARCHAR(45),
    application_context VARCHAR(100),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_audit_table_name ON data_change_audit(table_name);
CREATE INDEX idx_audit_changed_at ON data_change_audit(changed_at);

-- ============================================================================
-- SECTION 17: USER FEEDBACK
-- ============================================================================

CREATE TABLE IF NOT EXISTS app_feedback (
    feedback_id SERIAL PRIMARY KEY,
    device_id CHAR(36) REFERENCES devices(device_id),
    feedback_type VARCHAR(30) NOT NULL CHECK (feedback_type IN ('bug_report', 'feature_request', 'usability_issue', 'performance_issue', 'content_issue', 'compliment', 'other')),
    feedback_text TEXT NOT NULL,
    rating TINYINT,
    app_version VARCHAR(20),
    platform VARCHAR(20) CHECK (platform IN ('android', 'ios')),
    os_version VARCHAR(30),
    screen_name VARCHAR(100),
    related_report_id CHAR(36) REFERENCES incident_reports(report_id),
    attachment_count INTEGER DEFAULT 0,
    is_reviewed BOOLEAN DEFAULT FALSE,
    reviewed_at TIMESTAMP,
    reviewed_by INTEGER REFERENCES police_users(user_id),
    review_notes TEXT,
    review_status VARCHAR(20) DEFAULT 'new' CHECK (review_status IN ('new', 'acknowledged', 'investigating', 'resolved', 'wont_fix')),
    requires_followup BOOLEAN DEFAULT FALSE,
    followup_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_feedback_device_id ON app_feedback(device_id);
CREATE INDEX idx_feedback_created_at ON app_feedback(created_at);

CREATE TABLE IF NOT EXISTS feedback_attachments (
    attachment_id SERIAL PRIMARY KEY,
    feedback_id INTEGER NOT NULL REFERENCES app_feedback(feedback_id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size_bytes INTEGER,
    mime_type VARCHAR(100),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_attachment_feedback_id ON feedback_attachments(feedback_id);

-- ============================================================================
-- SECTION 18: API MANAGEMENT
-- ============================================================================

CREATE TABLE IF NOT EXISTS api_keys (
    key_id SERIAL PRIMARY KEY,
    key_name VARCHAR(100) NOT NULL,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    key_prefix VARCHAR(10) UNIQUE,
    owner_user_id INTEGER NOT NULL REFERENCES police_users(user_id) ON DELETE CASCADE,
    owner_description VARCHAR(255),
    permissions JSON,
    rate_limit_per_minute INTEGER,
    allowed_ips JSON,
    allowed_districts JSON,
    is_active BOOLEAN DEFAULT TRUE,
    last_used_at TIMESTAMP,
    total_requests BIGINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    revoked_at TIMESTAMP,
    revoked_reason VARCHAR(255)
);

CREATE INDEX idx_api_key_owner_user_id ON api_keys(owner_user_id);

CREATE TABLE IF NOT EXISTS api_request_logs (
    log_id BIGSERIAL PRIMARY KEY,
    api_key_id INTEGER NOT NULL REFERENCES api_keys(key_id) ON DELETE CASCADE,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(20) NOT NULL CHECK (method IN ('GET', 'POST', 'PUT', 'PATCH', 'DELETE')),
    request_params JSON,
    response_status INTEGER,
    response_time_ms INTEGER,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    had_error BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_api_log_api_key_id ON api_request_logs(api_key_id);
CREATE INDEX idx_api_log_requested_at ON api_request_logs(requested_at);

-- ============================================================================
-- FINAL VERIFICATION
-- ============================================================================

-- This script creates all 33 tables with complete relationships
-- Total tables:
-- 1. devices
-- 2. device_trust_history
-- 3. provinces
-- 4. districts
-- 5. sectors
-- 6. cells
-- 7. villages
-- 8. police_users
-- 9. police_sessions
-- 10. incident_categories
-- 11. incident_types
-- 12. ml_models
-- 13. clustering_runs
-- 14. hotspots
-- 15. hotspot_history
-- 16. incident_reports
-- 17. report_evidence
-- 18. verification_rules
-- 19. rule_execution_logs
-- 20. ml_predictions
-- 21. ml_training_data
-- 22. hotspot_reports
-- 23. notifications
-- 24. daily_statistics
-- 25. incident_type_trends
-- 26. public_safety_zones
-- 27. system_settings
-- 28. activity_logs
-- 29. data_change_audit
-- 30. app_feedback
-- 31. feedback_attachments
-- 32. api_keys
-- 33. api_request_logs
