-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- ========================================================
-- 1. devices — Anonymous Reporter Devices
-- ========================================================
CREATE TABLE devices (
    device_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_hash      VARCHAR(255) NOT NULL UNIQUE,
    first_seen_at    TIMESTAMP NOT NULL DEFAULT NOW(),
    total_reports    INT NOT NULL DEFAULT 0,
    trusted_reports  INT NOT NULL DEFAULT 0,
    flagged_reports  INT NOT NULL DEFAULT 0,
    device_trust_score DECIMAL(5,2) NOT NULL DEFAULT 50.00
);

CREATE INDEX idx_devices_hash ON devices (device_hash);

-- ========================================================
-- 2. incident_types — Incident Categories
-- ========================================================
CREATE TYPE location_type_enum      AS ENUM ('sector','cell','village');
CREATE TYPE motion_level_enum       AS ENUM ('low','medium','high');
CREATE TYPE rule_status_enum        AS ENUM ('passed','flagged','rejected');
CREATE TYPE file_type_enum          AS ENUM ('photo','video');
CREATE TYPE ai_quality_label_enum   AS ENUM ('good','poor','suspicious');
CREATE TYPE prediction_label_enum   AS ENUM ('likely_real','suspicious','fake');
CREATE TYPE police_role_enum        AS ENUM ('admin','supervisor','officer');
CREATE TYPE review_decision_enum    AS ENUM ('confirmed','rejected','investigation');
CREATE TYPE ground_truth_enum       AS ENUM ('real','fake');
CREATE TYPE risk_level_enum         AS ENUM ('low','medium','high');
CREATE TYPE assignment_status_enum  AS ENUM ('assigned','investigating','resolved','closed');
CREATE TYPE assignment_priority_enum AS ENUM ('low','medium','high','urgent');
CREATE TYPE notification_type_enum  AS ENUM ('report','hotspot','assignment','system');
CREATE TYPE actor_type_enum         AS ENUM ('system','police_user');

CREATE TABLE incident_types (
    incident_type_id SMALLINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    type_name        VARCHAR(100) NOT NULL UNIQUE,
    description      TEXT,
    severity_weight  DECIMAL(3,2) NOT NULL DEFAULT 1.00,
    is_active        BOOLEAN NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ========================================================
-- 3. locations — Administrative Boundaries (Musanze)
-- ========================================================
CREATE TABLE locations (
    location_id        INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    location_type      location_type_enum NOT NULL,
    location_name      VARCHAR(100) NOT NULL,
    parent_location_id INT REFERENCES locations(location_id),
    geometry           GEOMETRY(Geometry, 4326),
    centroid_lat       DECIMAL(10,7),
    centroid_long      DECIMAL(10,7),
    is_active          BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX idx_locations_geo ON locations USING GIST (geometry);

-- ========================================================
-- 4. reports — Incident Reports (Raw Submissions)
-- ========================================================
CREATE TABLE reports (
    report_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id           UUID NOT NULL REFERENCES devices(device_id),
    incident_type_id    SMALLINT NOT NULL REFERENCES incident_types(incident_type_id),
    description         TEXT,
    latitude            DECIMAL(10,7) NOT NULL,
    longitude           DECIMAL(10,7) NOT NULL,
    gps_accuracy        DECIMAL(6,2),
    motion_level        motion_level_enum,
    movement_speed      DECIMAL(6,2),
    was_stationary      BOOLEAN,
    village_location_id INT REFERENCES locations(location_id),
    reported_at         TIMESTAMP NOT NULL DEFAULT NOW(),
    rule_status         rule_status_enum NOT NULL DEFAULT 'passed',
    is_flagged          BOOLEAN NOT NULL DEFAULT FALSE,
    feature_vector      JSONB,
    ai_ready            BOOLEAN NOT NULL DEFAULT FALSE,
    features_extracted  TIMESTAMP
);

CREATE INDEX idx_reports_device     ON reports (device_id);
CREATE INDEX idx_reports_type       ON reports (incident_type_id);
CREATE INDEX idx_reports_reported   ON reports (reported_at);
CREATE INDEX idx_reports_rule       ON reports (rule_status);
CREATE INDEX idx_reports_ai_ready   ON reports (ai_ready);

-- ========================================================
-- 5. evidence_files — Report Evidence
-- ========================================================
CREATE TABLE evidence_files (
    evidence_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id        UUID NOT NULL REFERENCES reports(report_id) ON DELETE CASCADE,
    file_url         VARCHAR(500) NOT NULL,
    file_type        file_type_enum NOT NULL,
    media_latitude   DECIMAL(10,7),
    media_longitude  DECIMAL(10,7),
    captured_at      TIMESTAMP,
    is_live_capture  BOOLEAN NOT NULL DEFAULT FALSE,
    uploaded_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    perceptual_hash  VARCHAR(128),
    blur_score       DECIMAL(6,3),
    tamper_score     DECIMAL(6,3),
    ai_quality_label ai_quality_label_enum,
    ai_checked_at    TIMESTAMP
);

CREATE INDEX idx_evidence_report ON evidence_files (report_id);
CREATE INDEX idx_evidence_phash  ON evidence_files (perceptual_hash);

-- ========================================================
-- 6. ml_predictions — Machine Learning Outputs
-- ========================================================
CREATE TABLE ml_predictions (
    prediction_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id        UUID NOT NULL REFERENCES reports(report_id) ON DELETE CASCADE,
    trust_score      DECIMAL(5,2),
    prediction_label prediction_label_enum,
    model_version    VARCHAR(50),
    evaluated_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    confidence       DECIMAL(5,2),
    explanation      JSONB,
    processing_time  INT,
    model_type       VARCHAR(50),
    is_final         BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_ml_report  ON ml_predictions (report_id);
CREATE INDEX idx_ml_final   ON ml_predictions (is_final);

-- ========================================================
-- 7. police_users — Police Accounts & Roles
-- ========================================================
CREATE TABLE police_users (
    police_user_id       INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    first_name           VARCHAR(150) NOT NULL,
    middle_name          VARCHAR(150),
    last_name            VARCHAR(150) NOT NULL,
    email                VARCHAR(255) NOT NULL UNIQUE,
    phone_number         VARCHAR(20),
    password_hash        VARCHAR(255) NOT NULL,
    badge_number         VARCHAR(50) UNIQUE,
    role                 police_role_enum NOT NULL,
    assigned_location_id INT REFERENCES locations(location_id),
    is_active            BOOLEAN NOT NULL DEFAULT TRUE,
    created_at           TIMESTAMP NOT NULL DEFAULT NOW(),
    last_login_at        TIMESTAMP
);

CREATE INDEX idx_police_email ON police_users (email);

-- ========================================================
-- 8. police_reviews — Ground Truth Decisions
-- ========================================================
CREATE TABLE police_reviews (
    review_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id          UUID NOT NULL REFERENCES reports(report_id) ON DELETE CASCADE,
    police_user_id     INT NOT NULL REFERENCES police_users(police_user_id),
    decision           review_decision_enum NOT NULL,
    review_note        TEXT,
    reviewed_at        TIMESTAMP NOT NULL DEFAULT NOW(),
    ground_truth_label ground_truth_enum,
    confidence_level   DECIMAL(5,2),
    used_for_training  BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_review_report ON police_reviews (report_id);

-- ========================================================
-- 9. hotspots — Risk Clusters
-- ========================================================
CREATE TABLE hotspots (
    hotspot_id        INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    center_lat        DECIMAL(10,7) NOT NULL,
    center_long       DECIMAL(10,7) NOT NULL,
    radius_meters     DECIMAL(8,2),
    incident_count    INT NOT NULL DEFAULT 0,
    risk_level        risk_level_enum NOT NULL,
    time_window_hours INT,
    detected_at       TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ========================================================
-- 10. hotspot_reports — Hotspot Membership
-- ========================================================
CREATE TABLE hotspot_reports (
    hotspot_id INT  NOT NULL REFERENCES hotspots(hotspot_id) ON DELETE CASCADE,
    report_id  UUID NOT NULL REFERENCES reports(report_id)   ON DELETE CASCADE,
    PRIMARY KEY (hotspot_id, report_id)
);

-- ========================================================
-- 11. incident_groups — Duplicate Incident Grouping
-- ========================================================
CREATE TABLE incident_groups (
    group_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_type_id SMALLINT NOT NULL REFERENCES incident_types(incident_type_id),
    center_lat       DECIMAL(10,7),
    center_long      DECIMAL(10,7),
    start_time       TIMESTAMP,
    end_time         TIMESTAMP,
    report_count     INT NOT NULL DEFAULT 0,
    created_at       TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ========================================================
-- 12. report_assignments — Case Handling Workflow
-- ========================================================
CREATE TABLE report_assignments (
    assignment_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id      UUID NOT NULL REFERENCES reports(report_id) ON DELETE CASCADE,
    police_user_id INT  NOT NULL REFERENCES police_users(police_user_id),
    status         assignment_status_enum NOT NULL DEFAULT 'assigned',
    priority       assignment_priority_enum NOT NULL DEFAULT 'medium',
    assigned_at    TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at   TIMESTAMP
);

CREATE INDEX idx_assign_report  ON report_assignments (report_id);
CREATE INDEX idx_assign_officer ON report_assignments (police_user_id);
CREATE INDEX idx_assign_status  ON report_assignments (status);

-- ========================================================
-- 13. notifications — System Alerts
-- ========================================================
CREATE TABLE notifications (
    notification_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    police_user_id      INT NOT NULL REFERENCES police_users(police_user_id),
    title               VARCHAR(150) NOT NULL,
    message             TEXT,
    type                notification_type_enum NOT NULL,
    related_entity_type VARCHAR(50),
    related_entity_id   CHAR(36),
    is_read             BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_notif_user   ON notifications (police_user_id);
CREATE INDEX idx_notif_unread ON notifications (police_user_id, is_read);

-- ========================================================
-- 14. audit_logs — Security & Accountability
-- ========================================================
CREATE TABLE audit_logs (
    log_id         BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    actor_type     actor_type_enum NOT NULL,
    actor_id       INT,
    action_type    VARCHAR(100) NOT NULL,
    entity_type    VARCHAR(50),
    entity_id      CHAR(36),
    action_details JSON,
    ip_address     VARCHAR(45),
    success        BOOLEAN NOT NULL DEFAULT TRUE,
    created_at     TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_actor  ON audit_logs (actor_type, actor_id);
CREATE INDEX idx_audit_entity ON audit_logs (entity_type, entity_id);
CREATE INDEX idx_audit_time   ON audit_logs (created_at);

-- ========================================================
-- Seed: Default incident types
-- ========================================================
INSERT INTO incident_types (type_name, description, severity_weight) VALUES
    ('Theft',               'Stealing of property',                          0.70),
    ('Vandalism',           'Deliberate destruction of property',            0.50),
    ('Suspicious Activity', 'Unusual or concerning behavior',                0.40),
    ('Assault',             'Physical attack on a person',                   0.90),
    ('Fraud',               'Deceptive practices for personal gain',         0.60),
    ('Drug Activity',       'Drug-related incidents',                        0.80),
    ('Trespassing',         'Unauthorized entry onto property',              0.30),
    ('Noise Disturbance',   'Excessive or disruptive noise',                 0.20),
    ('Traffic Incident',    'Road accidents or violations',                  0.50),
    ('Other',               'Incidents not covered by other categories',     0.30);
