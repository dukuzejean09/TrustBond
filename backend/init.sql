-- ============================================================================
-- TrustBond Database Initialization v2.0
-- Privacy-Preserving Anonymous Community Incident Reporting System
-- ============================================================================
-- This file initializes the database with:
-- 1. Schema from trustbond_complete_schema.sql (16 tables)
-- 2. Rwanda administrative locations
-- 3. Default admin user
-- 4. Initial ML models configuration
-- ============================================================================

-- Include the main schema (run trustbond_complete_schema.sql first)
-- \i /docker-entrypoint-initdb.d/trustbond_complete_schema.sql

-- ============================================================================
-- RWANDA ADMINISTRATIVE LOCATIONS
-- Hierarchical: Province → District → Sector → Cell → Village
-- ============================================================================

-- Provinces (5)
INSERT INTO locations (location_type, name, code, latitude, longitude, population, is_active) VALUES
('province', 'Kigali City', 'KGL', -1.9403, 29.8739, 1132686, TRUE),
('province', 'Eastern Province', 'EST', -1.7833, 30.4833, 2595703, TRUE),
('province', 'Western Province', 'WST', -2.4833, 29.2333, 2471239, TRUE),
('province', 'Northern Province', 'NTH', -1.6500, 29.8833, 1726370, TRUE),
('province', 'Southern Province', 'STH', -2.6000, 29.7500, 2589975, TRUE);

-- Districts for Kigali City (3)
INSERT INTO locations (parent_id, location_type, name, code, latitude, longitude, population, is_active) VALUES
((SELECT location_id FROM locations WHERE code = 'KGL'), 'district', 'Gasabo', 'KGL-GSB', -1.8833, 30.0833, 530907, TRUE),
((SELECT location_id FROM locations WHERE code = 'KGL'), 'district', 'Kicukiro', 'KGL-KCK', -1.9833, 30.0667, 318564, TRUE),
((SELECT location_id FROM locations WHERE code = 'KGL'), 'district', 'Nyarugenge', 'KGL-NYR', -1.9500, 29.8500, 284324, TRUE);

-- Districts for Eastern Province (7)
INSERT INTO locations (parent_id, location_type, name, code, latitude, longitude, population, is_active) VALUES
((SELECT location_id FROM locations WHERE code = 'EST'), 'district', 'Bugesera', 'EST-BGS', -2.2000, 30.0500, 363339, TRUE),
((SELECT location_id FROM locations WHERE code = 'EST'), 'district', 'Gatsibo', 'EST-GTS', -1.5833, 30.4500, 433997, TRUE),
((SELECT location_id FROM locations WHERE code = 'EST'), 'district', 'Kayonza', 'EST-KYZ', -1.8500, 30.6500, 346751, TRUE),
((SELECT location_id FROM locations WHERE code = 'EST'), 'district', 'Kirehe', 'EST-KRH', -2.2667, 30.7667, 340983, TRUE),
((SELECT location_id FROM locations WHERE code = 'EST'), 'district', 'Ngoma', 'EST-NGM', -2.1500, 30.4333, 336250, TRUE),
((SELECT location_id FROM locations WHERE code = 'EST'), 'district', 'Nyagatare', 'EST-NYG', -1.3000, 30.3167, 465855, TRUE),
((SELECT location_id FROM locations WHERE code = 'EST'), 'district', 'Rwamagana', 'EST-RWM', -1.9500, 30.4333, 313461, TRUE);

-- Districts for Western Province (7)
INSERT INTO locations (parent_id, location_type, name, code, latitude, longitude, population, is_active) VALUES
((SELECT location_id FROM locations WHERE code = 'WST'), 'district', 'Karongi', 'WST-KRG', -2.0667, 29.3500, 331063, TRUE),
((SELECT location_id FROM locations WHERE code = 'WST'), 'district', 'Ngororero', 'WST-NGR', -1.8667, 29.5833, 334413, TRUE),
((SELECT location_id FROM locations WHERE code = 'WST'), 'district', 'Nyabihu', 'WST-NYB', -1.6500, 29.5000, 295340, TRUE),
((SELECT location_id FROM locations WHERE code = 'WST'), 'district', 'Nyamasheke', 'WST-NYM', -2.3500, 29.1333, 382118, TRUE),
((SELECT location_id FROM locations WHERE code = 'WST'), 'district', 'Rubavu', 'WST-RBV', -1.7500, 29.2833, 403662, TRUE),
((SELECT location_id FROM locations WHERE code = 'WST'), 'district', 'Rusizi', 'WST-RSZ', -2.5000, 29.0000, 401882, TRUE),
((SELECT location_id FROM locations WHERE code = 'WST'), 'district', 'Rutsiro', 'WST-RTS', -1.9333, 29.3167, 324654, TRUE);

-- Districts for Northern Province (5)
INSERT INTO locations (parent_id, location_type, name, code, latitude, longitude, population, is_active) VALUES
((SELECT location_id FROM locations WHERE code = 'NTH'), 'district', 'Burera', 'NTH-BRR', -1.4667, 29.8333, 336582, TRUE),
((SELECT location_id FROM locations WHERE code = 'NTH'), 'district', 'Gakenke', 'NTH-GKK', -1.6833, 29.7833, 338486, TRUE),
((SELECT location_id FROM locations WHERE code = 'NTH'), 'district', 'Gicumbi', 'NTH-GCB', -1.5833, 30.0500, 395606, TRUE),
((SELECT location_id FROM locations WHERE code = 'NTH'), 'district', 'Musanze', 'NTH-MSZ', -1.5000, 29.6333, 368267, TRUE),
((SELECT location_id FROM locations WHERE code = 'NTH'), 'district', 'Rulindo', 'NTH-RLD', -1.7167, 29.9833, 287429, TRUE);

-- Districts for Southern Province (8)
INSERT INTO locations (parent_id, location_type, name, code, latitude, longitude, population, is_active) VALUES
((SELECT location_id FROM locations WHERE code = 'STH'), 'district', 'Gisagara', 'STH-GSG', -2.6167, 29.8500, 322506, TRUE),
((SELECT location_id FROM locations WHERE code = 'STH'), 'district', 'Huye', 'STH-HYE', -2.5833, 29.7500, 328605, TRUE),
((SELECT location_id FROM locations WHERE code = 'STH'), 'district', 'Kamonyi', 'STH-KMN', -2.0000, 29.9000, 340501, TRUE),
((SELECT location_id FROM locations WHERE code = 'STH'), 'district', 'Muhanga', 'STH-MHG', -2.0833, 29.7500, 319141, TRUE),
((SELECT location_id FROM locations WHERE code = 'STH'), 'district', 'Nyamagabe', 'STH-NYM', -2.4833, 29.5000, 341491, TRUE),
((SELECT location_id FROM locations WHERE code = 'STH'), 'district', 'Nyanza', 'STH-NYZ', -2.3500, 29.7500, 323719, TRUE),
((SELECT location_id FROM locations WHERE code = 'STH'), 'district', 'Nyaruguru', 'STH-NYR', -2.7500, 29.5000, 297459, TRUE),
((SELECT location_id FROM locations WHERE code = 'STH'), 'district', 'Ruhango', 'STH-RHG', -2.2167, 29.7833, 316557, TRUE);

-- Sample Sectors for Gasabo District
INSERT INTO locations (parent_id, location_type, name, code, latitude, longitude, is_active) VALUES
((SELECT location_id FROM locations WHERE code = 'KGL-GSB'), 'sector', 'Bumbogo', 'KGL-GSB-BMB', -1.8500, 30.1333, TRUE),
((SELECT location_id FROM locations WHERE code = 'KGL-GSB'), 'sector', 'Gatsata', 'KGL-GSB-GTS', -1.9000, 30.0500, TRUE),
((SELECT location_id FROM locations WHERE code = 'KGL-GSB'), 'sector', 'Gikomero', 'KGL-GSB-GKM', -1.8333, 30.1000, TRUE),
((SELECT location_id FROM locations WHERE code = 'KGL-GSB'), 'sector', 'Gisozi', 'KGL-GSB-GSZ', -1.9167, 30.0333, TRUE),
((SELECT location_id FROM locations WHERE code = 'KGL-GSB'), 'sector', 'Jabana', 'KGL-GSB-JBN', -1.8667, 30.0833, TRUE),
((SELECT location_id FROM locations WHERE code = 'KGL-GSB'), 'sector', 'Jali', 'KGL-GSB-JLI', -1.8833, 30.1500, TRUE),
((SELECT location_id FROM locations WHERE code = 'KGL-GSB'), 'sector', 'Kacyiru', 'KGL-GSB-KCY', -1.9333, 30.0667, TRUE),
((SELECT location_id FROM locations WHERE code = 'KGL-GSB'), 'sector', 'Kimihurura', 'KGL-GSB-KMH', -1.9500, 30.1000, TRUE),
((SELECT location_id FROM locations WHERE code = 'KGL-GSB'), 'sector', 'Kimironko', 'KGL-GSB-KMR', -1.9333, 30.1167, TRUE),
((SELECT location_id FROM locations WHERE code = 'KGL-GSB'), 'sector', 'Kinyinya', 'KGL-GSB-KNY', -1.9000, 30.1000, TRUE),
((SELECT location_id FROM locations WHERE code = 'KGL-GSB'), 'sector', 'Ndera', 'KGL-GSB-NDR', -1.9167, 30.1667, TRUE),
((SELECT location_id FROM locations WHERE code = 'KGL-GSB'), 'sector', 'Nduba', 'KGL-GSB-NDB', -1.8500, 30.0667, TRUE),
((SELECT location_id FROM locations WHERE code = 'KGL-GSB'), 'sector', 'Remera', 'KGL-GSB-RMR', -1.9500, 30.1333, TRUE),
((SELECT location_id FROM locations WHERE code = 'KGL-GSB'), 'sector', 'Rusororo', 'KGL-GSB-RSR', -1.8833, 30.1167, TRUE),
((SELECT location_id FROM locations WHERE code = 'KGL-GSB'), 'sector', 'Rutunga', 'KGL-GSB-RTG', -1.8667, 30.0500, TRUE);

-- Sample Sectors for Kicukiro District
INSERT INTO locations (parent_id, location_type, name, code, latitude, longitude, is_active) VALUES
((SELECT location_id FROM locations WHERE code = 'KGL-KCK'), 'sector', 'Gahanga', 'KGL-KCK-GHG', -2.0333, 30.1000, TRUE),
((SELECT location_id FROM locations WHERE code = 'KGL-KCK'), 'sector', 'Gatenga', 'KGL-KCK-GTG', -1.9833, 30.0667, TRUE),
((SELECT location_id FROM locations WHERE code = 'KGL-KCK'), 'sector', 'Gikondo', 'KGL-KCK-GKD', -1.9667, 30.0500, TRUE),
((SELECT location_id FROM locations WHERE code = 'KGL-KCK'), 'sector', 'Kagarama', 'KGL-KCK-KGR', -1.9833, 30.0833, TRUE),
((SELECT location_id FROM locations WHERE code = 'KGL-KCK'), 'sector', 'Kanombe', 'KGL-KCK-KNB', -1.9667, 30.1333, TRUE),
((SELECT location_id FROM locations WHERE code = 'KGL-KCK'), 'sector', 'Kicukiro', 'KGL-KCK-KCK', -1.9833, 30.1000, TRUE),
((SELECT location_id FROM locations WHERE code = 'KGL-KCK'), 'sector', 'Kigarama', 'KGL-KCK-KGM', -1.9833, 30.1167, TRUE),
((SELECT location_id FROM locations WHERE code = 'KGL-KCK'), 'sector', 'Masaka', 'KGL-KCK-MSK', -2.0167, 30.1333, TRUE),
((SELECT location_id FROM locations WHERE code = 'KGL-KCK'), 'sector', 'Niboye', 'KGL-KCK-NBY', -2.0000, 30.0833, TRUE),
((SELECT location_id FROM locations WHERE code = 'KGL-KCK'), 'sector', 'Nyarugunga', 'KGL-KCK-NYR', -2.0000, 30.1000, TRUE);

-- Sample Sectors for Nyarugenge District
INSERT INTO locations (parent_id, location_type, name, code, latitude, longitude, is_active) VALUES
((SELECT location_id FROM locations WHERE code = 'KGL-NYR'), 'sector', 'Gitega', 'KGL-NYR-GTG', -1.9500, 29.8667, TRUE),
((SELECT location_id FROM locations WHERE code = 'KGL-NYR'), 'sector', 'Kanyinya', 'KGL-NYR-KNY', -1.9167, 29.8333, TRUE),
((SELECT location_id FROM locations WHERE code = 'KGL-NYR'), 'sector', 'Kigali', 'KGL-NYR-KGL', -1.9500, 30.0500, TRUE),
((SELECT location_id FROM locations WHERE code = 'KGL-NYR'), 'sector', 'Kimisagara', 'KGL-NYR-KMS', -1.9500, 30.0333, TRUE),
((SELECT location_id FROM locations WHERE code = 'KGL-NYR'), 'sector', 'Mageragere', 'KGL-NYR-MGR', -1.9833, 29.8833, TRUE),
((SELECT location_id FROM locations WHERE code = 'KGL-NYR'), 'sector', 'Muhima', 'KGL-NYR-MHM', -1.9500, 30.0333, TRUE),
((SELECT location_id FROM locations WHERE code = 'KGL-NYR'), 'sector', 'Nyakabanda', 'KGL-NYR-NYK', -1.9667, 30.0167, TRUE),
((SELECT location_id FROM locations WHERE code = 'KGL-NYR'), 'sector', 'Nyamirambo', 'KGL-NYR-NYM', -1.9833, 30.0167, TRUE),
((SELECT location_id FROM locations WHERE code = 'KGL-NYR'), 'sector', 'Nyarugenge', 'KGL-NYR-NYR', -1.9500, 30.0500, TRUE),
((SELECT location_id FROM locations WHERE code = 'KGL-NYR'), 'sector', 'Rwezamenyo', 'KGL-NYR-RWZ', -1.9667, 30.0000, TRUE);

-- ============================================================================
-- DEFAULT ADMIN USER
-- Password: Admin@123 (bcrypt hashed)
-- ============================================================================
INSERT INTO police_users (
    username, 
    email, 
    password_hash, 
    full_name, 
    badge_number, 
    phone_number,
    role, 
    can_access_all_locations,
    is_active,
    password_changed_at
) VALUES (
    'admin',
    'admin@trustbond.rw',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4u4TZqhzL2kF.Kme', -- Admin@123
    'System Administrator',
    'ADMIN-001',
    '+250788000001',
    'super_admin',
    TRUE,
    TRUE,
    CURRENT_TIMESTAMP
);

-- Additional demo users
INSERT INTO police_users (
    username, 
    email, 
    password_hash, 
    full_name, 
    badge_number,
    phone_number, 
    role, 
    assigned_location_id,
    is_active
) VALUES 
(
    'commander.gasabo',
    'commander.gasabo@police.rw',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4u4TZqhzL2kF.Kme', -- Admin@123
    'Jean Pierre Habimana',
    'CMD-GSB-001',
    '+250788000002',
    'commander',
    (SELECT location_id FROM locations WHERE code = 'KGL-GSB'),
    TRUE
),
(
    'officer.kimironko',
    'officer.kimironko@police.rw',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4u4TZqhzL2kF.Kme', -- Admin@123
    'Marie Claire Uwimana',
    'OFC-KMR-001',
    '+250788000003',
    'officer',
    (SELECT location_id FROM locations WHERE code = 'KGL-GSB-KMR'),
    TRUE
),
(
    'analyst.kigali',
    'analyst@police.rw',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4u4TZqhzL2kF.Kme', -- Admin@123
    'Patrick Niyonzima',
    'ANL-KGL-001',
    '+250788000004',
    'analyst',
    (SELECT location_id FROM locations WHERE code = 'KGL'),
    TRUE
);

-- ============================================================================
-- INITIAL ML MODELS CONFIGURATION
-- ============================================================================
INSERT INTO ml_models (
    model_name,
    model_type,
    model_version,
    description,
    algorithm,
    input_features,
    output_format,
    is_active,
    created_at
) VALUES 
(
    'TrustScorer v1',
    'trust_scoring',
    'v1.0.0',
    'Initial trust scoring model - calculates overall trust score for reports based on device history, location patterns, and motion data',
    'RandomForest',
    '{"features": ["device_trust_score", "location_accuracy", "motion_score", "time_of_day", "device_reports_count", "previous_verified_rate"]}',
    '{"output": "trust_score", "range": [0, 1], "confidence": true}',
    TRUE,
    CURRENT_TIMESTAMP
),
(
    'AnomalyDetector v1',
    'anomaly_detection',
    'v1.0.0',
    'Detects GPS spoofing, bot submissions, and other anomalous patterns',
    'IsolationForest',
    '{"features": ["gps_accuracy", "motion_variance", "submission_speed", "location_jump_distance", "sensor_consistency"]}',
    '{"output": "anomaly_score", "flags": ["gps_spoof", "bot_pattern", "static_motion", "impossible_travel"]}',
    TRUE,
    CURRENT_TIMESTAMP
),
(
    'IncidentClusterer v1',
    'clustering',
    'v1.0.0',
    'Groups related incident reports based on location, time, and incident type similarity',
    'DBSCAN',
    '{"features": ["latitude", "longitude", "incident_time", "incident_type", "description_embedding"]}',
    '{"output": "cluster_id", "confidence": true, "cluster_size": true}',
    TRUE,
    CURRENT_TIMESTAMP
),
(
    'PriorityPredictor v1',
    'priority_prediction',
    'v1.0.0',
    'Predicts urgency and priority level for cases based on incident type, location risk, and report volume',
    'XGBoost',
    '{"features": ["incident_severity", "location_risk_score", "report_count", "trust_score_avg", "time_since_incident", "evidence_count"]}',
    '{"output": "priority", "levels": ["low", "medium", "high", "critical"], "confidence": true}',
    TRUE,
    CURRENT_TIMESTAMP
);

-- ============================================================================
-- LOG INITIALIZATION
-- ============================================================================
INSERT INTO activity_logs (
    actor_type,
    actor_id,
    action_type,
    entity_type,
    entity_id,
    action_details,
    success
) VALUES (
    'system',
    'init_script',
    'database.initialized',
    'database',
    'trustbond_v2',
    '{"version": "2.0.0", "tables": 16, "schema": "trustbond_complete_schema.sql", "timestamp": "' || CURRENT_TIMESTAMP || '"}',
    TRUE
);

-- ============================================================================
-- INITIALIZATION COMPLETE
-- ============================================================================
-- Database initialized with:
-- - 16 tables (schema from trustbond_complete_schema.sql)
-- - 5 provinces, 30 districts, 35 sample sectors
-- - 4 police users (admin + 3 demo)
-- - 4 ML models (trust_scoring, anomaly_detection, clustering, priority_prediction)
-- - 8 incident categories with 36 sub-types
-- - Default system settings for verification and ML
-- ============================================================================
