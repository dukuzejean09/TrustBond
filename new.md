# TrustBond — Full & Complete Database Schema (Improved)

**Project:** TrustBond: An Intelligent Anonymous Crime Reporting and Hotspot Detection System  
**Database:** PostgreSQL + PostGIS  
**Version:** 2.0 — Full Design Document  
**Pilot Area:** Musanze District, Rwanda

---

## Design Principles

- All citizen-facing tables store **no personally identifiable information (PII)**. Device identity is represented solely by a one-way SHA-256 hash.
- **Soft deletes** (`is_deleted`, `deleted_at`) are used across all reportable entities to preserve audit trails.
- **PostGIS geometry columns** (`GEOMETRY(Point, 4326)`, `GEOMETRY(Polygon, 4326)`) are used for all spatial data to enable efficient geospatial queries.
- All primary keys use **UUID** for public-facing entities (reports, evidence, cases) and **BIGINT/INT** for internal administrative tables (audit logs, config).
- `ENUM` types are defined as **PostgreSQL custom ENUM types** before table creation for maintainability.
- All foreign keys include `ON DELETE RESTRICT` by default to prevent accidental cascade deletions.
- `created_at` and `updated_at` columns use `TIMESTAMPTZ` (timezone-aware) for international correctness.
- Columns that carry computed or derived ML/AI values are **nullable** until the pipeline completes.

---

## Table Index

| #   | Table Name               | Purpose                                 |
| --- | ------------------------ | --------------------------------------- |
| 1   | `devices`                | Anonymous reporter device registry      |
| 2   | `device_trust_history`   | Trust score change log per device       |
| 3   | `incident_types`         | Incident category definitions           |
| 4   | `locations`              | Administrative boundaries (Musanze)     |
| 5   | `reports`                | Raw incident submissions                |
| 6   | `report_rule_checks`     | Stage 1 rule-based validation results   |
| 7   | `evidence_files`         | Attached media files per report         |
| 8   | `ml_predictions`         | Machine learning model outputs          |
| 9   | `police_users`           | Officer accounts and roles              |
| 10  | `police_sessions`        | JWT session and refresh token tracking  |
| 11  | `police_reviews`         | Ground truth officer decisions          |
| 12  | `report_assignments`     | Case handling and assignment workflow   |
| 13  | `incident_groups`        | Duplicate/related incident grouping     |
| 14  | `incident_group_members` | Reports linked to an incident group     |
| 15  | `hotspots`               | DBSCAN-detected risk clusters           |
| 16  | `hotspot_reports`        | Reports contributing to a hotspot       |
| 17  | `hotspot_run_logs`       | Metadata per DBSCAN execution run       |
| 18  | `notifications`          | System alerts for officers and citizens |
| 19  | `officer_notes`          | Internal investigation notes            |
| 20  | `system_config`          | Runtime configuration parameters        |
| 21  | `ml_model_registry`      | Trained model version tracking          |
| 22  | `audit_logs`             | Security and accountability log         |

---

## 1. `devices` — Anonymous Reporter Devices

Stores the pseudonymous fingerprint of each reporting device. No personal data is ever stored here.

| Column                   | Type           | Constraints                   | Description                                                           |
| ------------------------ | -------------- | ----------------------------- | --------------------------------------------------------------------- |
| `device_id`              | `UUID`         | PK, DEFAULT gen_random_uuid() | Internal unique device identifier                                     |
| `device_hash`            | `VARCHAR(64)`  | NOT NULL, UNIQUE              | SHA-256 hash of device hardware attributes — the only identity token  |
| `first_seen_at`          | `TIMESTAMPTZ`  | NOT NULL, DEFAULT NOW()       | Timestamp of first ever report from this device                       |
| `last_active_at`         | `TIMESTAMPTZ`  | NOT NULL, DEFAULT NOW()       | Timestamp of most recent report submission                            |
| `total_reports`          | `INT`          | NOT NULL, DEFAULT 0           | Cumulative reports submitted across all time                          |
| `trusted_reports`        | `INT`          | NOT NULL, DEFAULT 0           | Reports confirmed as genuine by police                                |
| `flagged_reports`        | `INT`          | NOT NULL, DEFAULT 0           | Reports marked suspicious or rejected                                 |
| `pending_reports`        | `INT`          | NOT NULL, DEFAULT 0           | Reports currently awaiting review                                     |
| `confirmation_rate`      | `DECIMAL(5,4)` | NOT NULL, DEFAULT 0.0         | Ratio of trusted_reports to total reviewed (0.0000–1.0000)            |
| `reporting_frequency`    | `DECIMAL(6,2)` | NULLABLE                      | Average reports submitted per month                                   |
| `unique_locations_count` | `INT`          | NOT NULL, DEFAULT 0           | Count of distinct GPS locations reported from                         |
| `spam_flag_count`        | `INT`          | NOT NULL, DEFAULT 0           | Number of times flagged as spammer by officers                        |
| `device_trust_score`     | `DECIMAL(5,2)` | NOT NULL, DEFAULT 50.00       | Current reliability score (0.00–100.00); recomputed after each review |
| `is_blacklisted`         | `BOOLEAN`      | NOT NULL, DEFAULT FALSE       | If TRUE, device reports are excluded from hotspot clustering          |
| `blacklisted_at`         | `TIMESTAMPTZ`  | NULLABLE                      | Timestamp when blacklist was applied                                  |
| `blacklisted_reason`     | `TEXT`         | NULLABLE                      | Officer-entered reason for blacklisting                               |

**Indexes:**

- `UNIQUE INDEX` on `device_hash`
- `INDEX` on `device_trust_score`
- `INDEX` on `is_blacklisted`

---

## 2. `device_trust_history` — Trust Score Change Log

Tracks every change to a device's trust score for auditing and trend analysis.

| Column                   | Type           | Constraints                                   | Description                                                                                                                                        |
| ------------------------ | -------------- | --------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `history_id`             | `BIGINT`       | PK, SERIAL                                    | Auto-incrementing log ID                                                                                                                           |
| `device_id`              | `UUID`         | NOT NULL, FK → `devices(device_id)`           | The device whose score changed                                                                                                                     |
| `previous_score`         | `DECIMAL(5,2)` | NOT NULL                                      | Trust score before the change                                                                                                                      |
| `new_score`              | `DECIMAL(5,2)` | NOT NULL                                      | Trust score after the change                                                                                                                       |
| `change_reason`          | `VARCHAR(100)` | NOT NULL                                      | Enum-like label: `report_confirmed`, `report_rejected`, `spam_flag_added`, `spam_flag_removed`, `manual_admin_override`, `scheduled_recalculation` |
| `triggered_by_report_id` | `UUID`         | NULLABLE, FK → `reports(report_id)`           | The report that triggered the recalculation (if applicable)                                                                                        |
| `triggered_by_user_id`   | `INT`          | NULLABLE, FK → `police_users(police_user_id)` | The officer who triggered a manual override                                                                                                        |
| `changed_at`             | `TIMESTAMPTZ`  | NOT NULL, DEFAULT NOW()                       | When the change occurred                                                                                                                           |

**Indexes:**

- `INDEX` on `(device_id, changed_at DESC)` for fast history retrieval

---

## 3. `incident_types` — Incident Categories

Master reference table for all supported incident categories.

| Column              | Type           | Constraints             | Description                                                 |
| ------------------- | -------------- | ----------------------- | ----------------------------------------------------------- |
| `incident_type_id`  | `SMALLINT`     | PK, SERIAL              | Auto-incrementing type ID                                   |
| `type_name`         | `VARCHAR(100)` | NOT NULL, UNIQUE        | Human-readable name (e.g. "Theft", "Assault", "Vandalism")  |
| `type_code`         | `VARCHAR(30)`  | NOT NULL, UNIQUE        | Machine-readable code (e.g. `THEFT`, `ASSAULT`)             |
| `description`       | `TEXT`         | NULLABLE                | Full explanation of what this category includes             |
| `severity_weight`   | `DECIMAL(3,2)` | NOT NULL, DEFAULT 1.00  | Risk multiplier used in hotspot risk scoring (0.10–3.00)    |
| `icon_name`         | `VARCHAR(50)`  | NULLABLE                | Icon identifier for mobile app UI rendering                 |
| `color_hex`         | `CHAR(6)`      | NULLABLE                | UI color code for map and dashboard display (hex without #) |
| `requires_evidence` | `BOOLEAN`      | NOT NULL, DEFAULT FALSE | Whether this type enforces mandatory evidence attachment    |
| `is_active`         | `BOOLEAN`      | NOT NULL, DEFAULT TRUE  | Whether this type is currently selectable in the app        |
| `display_order`     | `SMALLINT`     | NOT NULL, DEFAULT 0     | Sort order for mobile app display                           |
| `created_at`        | `TIMESTAMPTZ`  | NOT NULL, DEFAULT NOW() |                                                             |
| `updated_at`        | `TIMESTAMPTZ`  | NOT NULL, DEFAULT NOW() |                                                             |

---

## 4. `locations` — Administrative Boundaries (Musanze)

Hierarchical administrative boundary table covering Musanze District sectors, cells, and villages. Supports spatial containment queries via PostGIS.

| Column                | Type                                         | Constraints                             | Description                                              |
| --------------------- | -------------------------------------------- | --------------------------------------- | -------------------------------------------------------- |
| `location_id`         | `INT`                                        | PK, SERIAL                              | Auto-incrementing location ID                            |
| `location_type`       | `ENUM('district','sector','cell','village')` | NOT NULL                                | Administrative level                                     |
| `location_name`       | `VARCHAR(100)`                               | NOT NULL                                | Official name of the location                            |
| `location_code`       | `VARCHAR(30)`                                | NULLABLE, UNIQUE                        | Official government code (if applicable)                 |
| `parent_location_id`  | `INT`                                        | NULLABLE, FK → `locations(location_id)` | Parent in the hierarchy (NULL for top-level district)    |
| `geometry`            | `GEOMETRY(Polygon, 4326)`                    | NULLABLE                                | PostGIS polygon boundary for spatial containment queries |
| `centroid`            | `GEOMETRY(Point, 4326)`                      | NULLABLE                                | PostGIS centroid point (auto-derived from geometry)      |
| `centroid_lat`        | `DECIMAL(10,7)`                              | NULLABLE                                | Centroid latitude (denormalized for fast queries)        |
| `centroid_lon`        | `DECIMAL(10,7)`                              | NULLABLE                                | Centroid longitude (denormalized for fast queries)       |
| `area_sq_km`          | `DECIMAL(10,4)`                              | NULLABLE                                | Area of this location in square kilometers               |
| `population_estimate` | `INT`                                        | NULLABLE                                | Estimated population (for density normalization)         |
| `is_active`           | `BOOLEAN`                                    | NOT NULL, DEFAULT TRUE                  | Whether currently in use                                 |
| `created_at`          | `TIMESTAMPTZ`                                | NOT NULL, DEFAULT NOW()                 |                                                          |

**Indexes:**

- `GIST INDEX` on `geometry` for spatial queries
- `INDEX` on `parent_location_id`
- `INDEX` on `location_type`

---

## 5. `reports` — Incident Reports (Raw Submissions)

The central table. Each row represents one citizen report submission. No PII is stored.

| Column                      | Type                                                                    | Constraints                                       | Description                                                                        |
| --------------------------- | ----------------------------------------------------------------------- | ------------------------------------------------- | ---------------------------------------------------------------------------------- |
| `report_id`                 | `UUID`                                                                  | PK, DEFAULT gen_random_uuid()                     | Unique report identifier                                                           |
| `device_id`                 | `UUID`                                                                  | NOT NULL, FK → `devices(device_id)`               | Reporting device (pseudonymous)                                                    |
| `incident_type_id`          | `SMALLINT`                                                              | NOT NULL, FK → `incident_types(incident_type_id)` | Incident category                                                                  |
| `description`               | `TEXT`                                                                  | NOT NULL                                          | Citizen-written incident description                                               |
| `description_length`        | `INT`                                                                   | NOT NULL                                          | Character count (stored to avoid recomputing)                                      |
| `latitude`                  | `DECIMAL(10,7)`                                                         | NOT NULL                                          | GPS latitude of the incident                                                       |
| `longitude`                 | `DECIMAL(10,7)`                                                         | NOT NULL                                          | GPS longitude of the incident                                                      |
| `location_point`            | `GEOMETRY(Point, 4326)`                                                 | NOT NULL                                          | PostGIS geometry (auto-computed from lat/lon for spatial queries)                  |
| `gps_accuracy`              | `DECIMAL(6,2)`                                                          | NOT NULL                                          | GPS accuracy radius in meters                                                      |
| `gps_location_type`         | `ENUM('indoor','outdoor','unknown')`                                    | NOT NULL, DEFAULT 'unknown'                       | Whether GPS was captured indoors or outdoors                                       |
| `motion_level`              | `ENUM('stationary','low','medium','high')`                              | NULLABLE                                          | Device motion level at time of submission                                          |
| `movement_speed`            | `DECIMAL(6,2)`                                                          | NULLABLE                                          | Device speed in km/h at time of submission                                         |
| `was_stationary`            | `BOOLEAN`                                                               | NULLABLE                                          | TRUE if device was not moving when report was submitted                            |
| `village_location_id`       | `INT`                                                                   | NULLABLE, FK → `locations(location_id)`           | Derived village from GPS containment query                                         |
| `cell_location_id`          | `INT`                                                                   | NULLABLE, FK → `locations(location_id)`           | Derived cell from GPS containment query                                            |
| `sector_location_id`        | `INT`                                                                   | NULLABLE, FK → `locations(location_id)`           | Derived sector from GPS containment query                                          |
| `incident_timestamp`        | `TIMESTAMPTZ`                                                           | NOT NULL                                          | When the incident occurred (citizen-reported)                                      |
| `reported_at`               | `TIMESTAMPTZ`                                                           | NOT NULL, DEFAULT NOW()                           | When the report was submitted to the system                                        |
| `time_since_incident_hours` | `DECIMAL(8,2)`                                                          | NULLABLE                                          | Computed: hours between incident_timestamp and reported_at                         |
| `network_type`              | `ENUM('wifi','mobile_data','offline_queued')`                           | NOT NULL                                          | Network connection type at submission                                              |
| `app_version`               | `VARCHAR(20)`                                                           | NULLABLE                                          | Mobile app version used for submission                                             |
| `rule_status`               | `ENUM('passed','flagged','rejected')`                                   | NOT NULL, DEFAULT 'flagged'                       | Stage 1 rule-based check outcome                                                   |
| `ml_status`                 | `ENUM('pending','processing','complete','failed')`                      | NOT NULL, DEFAULT 'pending'                       | ML pipeline processing state                                                       |
| `review_status`             | `ENUM('pending','under_review','confirmed','rejected','investigation')` | NOT NULL, DEFAULT 'pending'                       | Police review state                                                                |
| `priority_level`            | `ENUM('low','medium','high','urgent')`                                  | NULLABLE                                          | Set by ML pipeline or officer override                                             |
| `final_trust_score`         | `DECIMAL(5,2)`                                                          | NULLABLE                                          | Final aggregated trust score (0.00–100.00); set after all pipeline stages complete |
| `is_flagged`                | `BOOLEAN`                                                               | NOT NULL, DEFAULT FALSE                           | Quick lookup: TRUE if rule_status = 'flagged' or 'rejected'                        |
| `is_duplicate`              | `BOOLEAN`                                                               | NOT NULL, DEFAULT FALSE                           | Flagged as duplicate of another report                                             |
| `duplicate_of_report_id`    | `UUID`                                                                  | NULLABLE, FK → `reports(report_id)`               | Original report if this is a duplicate                                             |
| `incident_group_id`         | `UUID`                                                                  | NULLABLE, FK → `incident_groups(group_id)`        | Linked incident group (if merged)                                                  |
| `feature_vector`            | `JSONB`                                                                 | NULLABLE                                          | Precomputed ML feature values for this report                                      |
| `ai_ready`                  | `BOOLEAN`                                                               | NOT NULL, DEFAULT FALSE                           | TRUE when feature_vector has been computed and report is ready for ML inference    |
| `features_extracted_at`     | `TIMESTAMPTZ`                                                           | NULLABLE                                          | Timestamp when feature extraction completed                                        |
| `is_deleted`                | `BOOLEAN`                                                               | NOT NULL, DEFAULT FALSE                           | Soft delete flag                                                                   |
| `deleted_at`                | `TIMESTAMPTZ`                                                           | NULLABLE                                          | When soft delete was applied                                                       |
| `deleted_by`                | `INT`                                                                   | NULLABLE, FK → `police_users(police_user_id)`     | Officer who deleted                                                                |
| `created_at`                | `TIMESTAMPTZ`                                                           | NOT NULL, DEFAULT NOW()                           |                                                                                    |
| `updated_at`                | `TIMESTAMPTZ`                                                           | NOT NULL, DEFAULT NOW()                           |                                                                                    |

**Indexes:**

- `GIST INDEX` on `location_point` for spatial hotspot queries
- `INDEX` on `(device_id, reported_at DESC)`
- `INDEX` on `review_status`
- `INDEX` on `priority_level`
- `INDEX` on `(incident_type_id, reported_at DESC)`
- `INDEX` on `(sector_location_id, reported_at DESC)` for district filtering
- `INDEX` on `final_trust_score`
- `INDEX` on `is_deleted` (partial: WHERE is_deleted = FALSE)

---

## 6. `report_rule_checks` — Stage 1 Rule-Based Validation Results

One row per report. Stores the detailed outcome of every Stage 1 validation check. Kept separate from `reports` to avoid column bloat on the main table.

| Column                       | Type                                  | Constraints                                 | Description                                                             |
| ---------------------------- | ------------------------------------- | ------------------------------------------- | ----------------------------------------------------------------------- |
| `check_id`                   | `UUID`                                | PK, DEFAULT gen_random_uuid()               |                                                                         |
| `report_id`                  | `UUID`                                | NOT NULL, UNIQUE, FK → `reports(report_id)` | One record per report                                                   |
| `gps_in_rwanda_bounds`       | `BOOLEAN`                             | NULLABLE                                    | GPS coordinates within Rwanda bounding box                              |
| `gps_accuracy_acceptable`    | `BOOLEAN`                             | NULLABLE                                    | GPS accuracy < configured threshold                                     |
| `timestamp_not_future`       | `BOOLEAN`                             | NULLABLE                                    | Incident timestamp is not in the future                                 |
| `timestamp_not_too_old`      | `BOOLEAN`                             | NULLABLE                                    | Incident timestamp is within 7 days                                     |
| `gps_speed_valid`            | `BOOLEAN`                             | NULLABLE                                    | Movement speed is physically plausible (< 200 km/h)                     |
| `gps_speed_value_kmh`        | `DECIMAL(8,2)`                        | NULLABLE                                    | Computed speed between this and previous report from same device        |
| `description_length_valid`   | `BOOLEAN`                             | NULLABLE                                    | Description meets minimum character threshold                           |
| `duplicate_media_detected`   | `BOOLEAN`                             | NULLABLE                                    | Perceptual hash matched an existing report's media                      |
| `duplicate_media_similarity` | `DECIMAL(5,4)`                        | NULLABLE                                    | Hamming distance normalized score (0=identical, 1=completely different) |
| `exif_gps_match`             | `BOOLEAN`                             | NULLABLE                                    | EXIF GPS (before stripping) matched submitted GPS within tolerance      |
| `device_rate_limit_exceeded` | `BOOLEAN`                             | NULLABLE                                    | Device submitted too many reports in a short window                     |
| `spam_keywords_detected`     | `BOOLEAN`                             | NULLABLE                                    | Description contains known spam pattern keywords                        |
| `total_checks_run`           | `SMALLINT`                            | NULLABLE                                    | Number of rule checks that were executed                                |
| `total_checks_passed`        | `SMALLINT`                            | NULLABLE                                    | Number of rule checks that passed                                       |
| `rule_pass_rate`             | `DECIMAL(5,4)`                        | NULLABLE                                    | Ratio of passed to total checks (0.0000–1.0000)                         |
| `overall_rule_status`        | `ENUM('passed','flagged','rejected')` | NULLABLE                                    | Final Stage 1 verdict                                                   |
| `checked_at`                 | `TIMESTAMPTZ`                         | NULLABLE                                    | When rule checks completed                                              |

---

## 7. `evidence_files` — Report Evidence (Media Attachments)

Stores metadata for each photo or video attached to a report. The actual files are stored in Cloudinary; only the URL and analysis results are stored here.

| Column                      | Type                                            | Constraints                         | Description                                                                      |
| --------------------------- | ----------------------------------------------- | ----------------------------------- | -------------------------------------------------------------------------------- |
| `evidence_id`               | `UUID`                                          | PK, DEFAULT gen_random_uuid()       | Unique evidence record ID                                                        |
| `report_id`                 | `UUID`                                          | NOT NULL, FK → `reports(report_id)` | Parent report                                                                    |
| `file_url`                  | `VARCHAR(500)`                                  | NOT NULL                            | Cloudinary secure URL                                                            |
| `cloudinary_public_id`      | `VARCHAR(200)`                                  | NOT NULL, UNIQUE                    | Cloudinary asset identifier for management operations                            |
| `file_type`                 | `ENUM('photo','video')`                         | NOT NULL                            | Media type                                                                       |
| `file_size_bytes`           | `INT`                                           | NULLABLE                            | File size in bytes                                                               |
| `mime_type`                 | `VARCHAR(50)`                                   | NULLABLE                            | e.g. `image/jpeg`, `video/mp4`                                                   |
| `original_filename`         | `VARCHAR(255)`                                  | NULLABLE                            | Original filename (stripped of device-identifying metadata)                      |
| `width_px`                  | `SMALLINT`                                      | NULLABLE                            | Image width in pixels                                                            |
| `height_px`                 | `SMALLINT`                                      | NULLABLE                            | Image height in pixels                                                           |
| `duration_seconds`          | `DECIMAL(8,2)`                                  | NULLABLE                            | Video duration (NULL for photos)                                                 |
| `media_latitude`            | `DECIMAL(10,7)`                                 | NULLABLE                            | GPS latitude from EXIF (before stripping) — used for consistency check only      |
| `media_longitude`           | `DECIMAL(10,7)`                                 | NULLABLE                            | GPS longitude from EXIF (before stripping)                                       |
| `captured_at`               | `TIMESTAMPTZ`                                   | NULLABLE                            | Photo/video capture timestamp from EXIF                                          |
| `is_live_capture`           | `BOOLEAN`                                       | NOT NULL, DEFAULT FALSE             | TRUE if captured directly via app camera (not from gallery)                      |
| `exif_stripped`             | `BOOLEAN`                                       | NOT NULL, DEFAULT TRUE              | Confirms EXIF metadata was removed before storage                                |
| `uploaded_at`               | `TIMESTAMPTZ`                                   | NOT NULL, DEFAULT NOW()             | When the file was uploaded                                                       |
| `perceptual_hash`           | `VARCHAR(128)`                                  | NULLABLE                            | 64-bit perceptual hash (pHash) for duplicate detection                           |
| `blur_score`                | `DECIMAL(8,4)`                                  | NULLABLE                            | Laplacian variance — higher = sharper; < 100 = blurry                            |
| `brightness_score`          | `DECIMAL(6,3)`                                  | NULLABLE                            | Mean pixel value (0–255); flag if < 30 (dark) or > 240 (overexposed)             |
| `image_quality_score`       | `DECIMAL(5,4)`                                  | NULLABLE                            | Composite quality score (0.0000–1.0000) from blur + brightness                   |
| `tamper_score`              | `DECIMAL(5,4)`                                  | NULLABLE                            | Manipulation detection score (0.0000–1.0000; higher = more suspicious)           |
| `is_screenshot_suspected`   | `BOOLEAN`                                       | NULLABLE                            | TRUE if image appears to be a screenshot rather than a photo                     |
| `is_ai_generated_suspected` | `BOOLEAN`                                       | NULLABLE                            | TRUE if image appears digitally generated                                        |
| `ai_quality_label`          | `ENUM('good','acceptable','poor','suspicious')` | NULLABLE                            | AI quality verdict                                                               |
| `hash_match_report_id`      | `UUID`                                          | NULLABLE, FK → `reports(report_id)` | Report that contains the matching duplicate media                                |
| `hash_hamming_distance`     | `SMALLINT`                                      | NULLABLE                            | Hamming distance to nearest matching pHash (0 = identical, 64 = fully different) |
| `ai_checked_at`             | `TIMESTAMPTZ`                                   | NULLABLE                            | When AI image analysis completed                                                 |

**Indexes:**

- `INDEX` on `report_id`
- `INDEX` on `perceptual_hash` for fast duplicate detection lookups
- `INDEX` on `ai_quality_label`

---

## 8. `ml_predictions` — Machine Learning Outputs

Stores every ML inference result for each report. Multiple rows per report are possible (one per model type, or when reprocessed with a new model version).

| Column                   | Type                                             | Constraints                                  | Description                                                                  |
| ------------------------ | ------------------------------------------------ | -------------------------------------------- | ---------------------------------------------------------------------------- |
| `prediction_id`          | `UUID`                                           | PK, DEFAULT gen_random_uuid()                | Unique prediction record                                                     |
| `report_id`              | `UUID`                                           | NOT NULL, FK → `reports(report_id)`          | Report this prediction evaluates                                             |
| `model_id`               | `INT`                                            | NOT NULL, FK → `ml_model_registry(model_id)` | The specific trained model version used                                      |
| `model_type`             | `VARCHAR(50)`                                    | NOT NULL                                     | `random_forest`, `anomaly_detector`, `vision_quality`, `nlp_sentiment`       |
| `model_version`          | `VARCHAR(50)`                                    | NOT NULL                                     | Model version string (e.g. `rf_v2.1.0`) — denormalized for query convenience |
| `prediction_label`       | `ENUM('likely_real','suspicious','likely_fake')` | NOT NULL                                     | Model's classification output                                                |
| `trust_score`            | `DECIMAL(5,2)`                                   | NOT NULL                                     | ML-computed trust confidence (0.00–100.00)                                   |
| `confidence`             | `DECIMAL(5,4)`                                   | NOT NULL                                     | Model class probability (0.0000–1.0000)                                      |
| `gps_anomaly_flag`       | `BOOLEAN`                                        | NULLABLE                                     | GPS location flagged as anomalous by Isolation Forest                        |
| `gps_anomaly_score`      | `DECIMAL(6,4)`                                   | NULLABLE                                     | Isolation Forest anomaly score                                               |
| `timestamp_anomaly_flag` | `BOOLEAN`                                        | NULLABLE                                     | Submission time flagged as anomalous                                         |
| `text_sentiment_score`   | `DECIMAL(5,4)`                                   | NULLABLE                                     | NLP sentiment score (-1.0000 to 1.0000)                                      |
| `keyword_flag_count`     | `SMALLINT`                                       | NULLABLE                                     | Count of suspicious keyword matches                                          |
| `explanation`            | `JSONB`                                          | NULLABLE                                     | SHAP feature importance values for explainability panel                      |
| `top_features`           | `JSONB`                                          | NULLABLE                                     | Top 5 feature names and contribution scores                                  |
| `processing_time_ms`     | `INT`                                            | NULLABLE                                     | Inference time in milliseconds (for performance monitoring)                  |
| `is_final`               | `BOOLEAN`                                        | NOT NULL, DEFAULT FALSE                      | TRUE for the current production prediction used in trust score computation   |
| `evaluated_at`           | `TIMESTAMPTZ`                                    | NOT NULL, DEFAULT NOW()                      | When inference completed                                                     |

**Indexes:**

- `INDEX` on `(report_id, is_final)` for fast active prediction lookup
- `INDEX` on `model_id`
- `INDEX` on `prediction_label`

---

## 9. `police_users` — Officer Accounts and Roles

Stores all police officer accounts. This table holds PII only for officers (not for citizens).

| Column                  | Type                                             | Constraints                                   | Description                                   |
| ----------------------- | ------------------------------------------------ | --------------------------------------------- | --------------------------------------------- |
| `police_user_id`        | `INT`                                            | PK, SERIAL                                    | Unique officer ID                             |
| `first_name`            | `VARCHAR(150)`                                   | NOT NULL                                      | Officer first name                            |
| `middle_name`           | `VARCHAR(150)`                                   | NULLABLE                                      | Officer middle name                           |
| `last_name`             | `VARCHAR(150)`                                   | NOT NULL                                      | Officer last name                             |
| `email`                 | `VARCHAR(255)`                                   | NOT NULL, UNIQUE                              | Officer login email                           |
| `phone_number`          | `VARCHAR(20)`                                    | NULLABLE                                      | Internal phone number (not exposed to public) |
| `password_hash`         | `VARCHAR(255)`                                   | NOT NULL                                      | bcrypt hash (cost factor 12)                  |
| `badge_number`          | `VARCHAR(50)`                                    | UNIQUE, NULLABLE                              | Official police badge number                  |
| `role`                  | `ENUM('admin','supervisor','analyst','officer')` | NOT NULL, DEFAULT 'officer'                   | Access control role                           |
| `assigned_location_id`  | `INT`                                            | NULLABLE, FK → `locations(location_id)`       | Officer's primary jurisdiction                |
| `is_active`             | `BOOLEAN`                                        | NOT NULL, DEFAULT TRUE                        | Account enabled/disabled                      |
| `must_change_password`  | `BOOLEAN`                                        | NOT NULL, DEFAULT TRUE                        | Forces password change on first login         |
| `failed_login_attempts` | `SMALLINT`                                       | NOT NULL, DEFAULT 0                           | Consecutive failed login count                |
| `locked_until`          | `TIMESTAMPTZ`                                    | NULLABLE                                      | Account lockout expiry (NULL = not locked)    |
| `last_login_at`         | `TIMESTAMPTZ`                                    | NULLABLE                                      | Most recent successful login                  |
| `last_login_ip`         | `INET`                                           | NULLABLE                                      | IP of most recent login (internal record)     |
| `created_at`            | `TIMESTAMPTZ`                                    | NOT NULL, DEFAULT NOW()                       | Account creation time                         |
| `created_by`            | `INT`                                            | NULLABLE, FK → `police_users(police_user_id)` | Admin who created this account                |
| `updated_at`            | `TIMESTAMPTZ`                                    | NOT NULL, DEFAULT NOW()                       |                                               |

**Indexes:**

- `UNIQUE INDEX` on `email`
- `INDEX` on `role`
- `INDEX` on `assigned_location_id`

---

## 10. `police_sessions` — JWT Session Tracking

Tracks active refresh tokens for officer sessions. Enables logout, token revocation, and concurrent session management.

| Column               | Type           | Constraints                                   | Description                                           |
| -------------------- | -------------- | --------------------------------------------- | ----------------------------------------------------- |
| `session_id`         | `UUID`         | PK, DEFAULT gen_random_uuid()                 | Unique session identifier                             |
| `police_user_id`     | `INT`          | NOT NULL, FK → `police_users(police_user_id)` | Session owner                                         |
| `refresh_token_hash` | `VARCHAR(255)` | NOT NULL, UNIQUE                              | bcrypt hash of the refresh token                      |
| `device_info`        | `VARCHAR(255)` | NULLABLE                                      | Browser / OS / device description for session display |
| `ip_address`         | `INET`         | NULLABLE                                      | IP address of session origin                          |
| `issued_at`          | `TIMESTAMPTZ`  | NOT NULL, DEFAULT NOW()                       | When the token was issued                             |
| `expires_at`         | `TIMESTAMPTZ`  | NOT NULL                                      | Refresh token expiry (default: 7 days from issued_at) |
| `last_used_at`       | `TIMESTAMPTZ`  | NULLABLE                                      | Most recent use of this refresh token                 |
| `is_revoked`         | `BOOLEAN`      | NOT NULL, DEFAULT FALSE                       | TRUE after logout or forced revocation                |
| `revoked_at`         | `TIMESTAMPTZ`  | NULLABLE                                      | When revocation occurred                              |

**Indexes:**

- `INDEX` on `(police_user_id, is_revoked)`
- `INDEX` on `expires_at` (for cleanup jobs)

---

## 11. `police_reviews` — Ground Truth Officer Decisions

Records the official decision of a reviewing officer on a report. This is the source of ground truth labels used to train the Random Forest model.

| Column                   | Type                                                                   | Constraints                                   | Description                                                                                               |
| ------------------------ | ---------------------------------------------------------------------- | --------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `review_id`              | `UUID`                                                                 | PK, DEFAULT gen_random_uuid()                 | Unique review record                                                                                      |
| `report_id`              | `UUID`                                                                 | NOT NULL, FK → `reports(report_id)`           | The report being reviewed                                                                                 |
| `police_user_id`         | `INT`                                                                  | NOT NULL, FK → `police_users(police_user_id)` | Reviewing officer                                                                                         |
| `decision`               | `ENUM('confirmed','rejected','under_investigation','needs_more_info')` | NOT NULL                                      | Officer's verdict                                                                                         |
| `review_note`            | `TEXT`                                                                 | NULLABLE                                      | Officer's qualitative notes about this decision                                                           |
| `rejection_reason_code`  | `VARCHAR(50)`                                                          | NULLABLE                                      | Standardized rejection reason (e.g. `duplicate`, `insufficient_evidence`, `false_report`, `out_of_scope`) |
| `reviewed_at`            | `TIMESTAMPTZ`                                                          | NOT NULL, DEFAULT NOW()                       | When the review was completed                                                                             |
| `time_to_review_minutes` | `INT`                                                                  | NULLABLE                                      | Minutes from report submission to this review (computed)                                                  |
| `ground_truth_label`     | `ENUM('real','fake','uncertain')`                                      | NOT NULL                                      | Training label derived from decision (used for ML training)                                               |
| `confidence_level`       | `DECIMAL(5,2)`                                                         | NULLABLE                                      | Officer-stated certainty (0–100); used to weight training samples                                         |
| `used_for_training`      | `BOOLEAN`                                                              | NOT NULL, DEFAULT FALSE                       | Whether this row has been included in an ML training run                                                  |
| `training_run_id`        | `INT`                                                                  | NULLABLE, FK → `ml_model_registry(model_id)`  | Which model training used this label                                                                      |
| `is_appealed`            | `BOOLEAN`                                                              | NOT NULL, DEFAULT FALSE                       | TRUE if citizen or supervisor challenged this decision                                                    |
| `appeal_outcome`         | `ENUM('upheld','overturned')`                                          | NULLABLE                                      | Result of appeal process                                                                                  |

**Indexes:**

- `INDEX` on `(report_id, reviewed_at DESC)`
- `INDEX` on `police_user_id`
- `INDEX` on `decision`
- `INDEX` on `used_for_training`

---

## 12. `report_assignments` — Case Handling Workflow

Tracks which officer is handling a report and the status of the investigation.

| Column            | Type                                                                | Constraints                                   | Description                               |
| ----------------- | ------------------------------------------------------------------- | --------------------------------------------- | ----------------------------------------- |
| `assignment_id`   | `UUID`                                                              | PK, DEFAULT gen_random_uuid()                 | Unique assignment record                  |
| `report_id`       | `UUID`                                                              | NOT NULL, FK → `reports(report_id)`           | The assigned report                       |
| `police_user_id`  | `INT`                                                               | NOT NULL, FK → `police_users(police_user_id)` | The officer assigned to this report       |
| `assigned_by`     | `INT`                                                               | NOT NULL, FK → `police_users(police_user_id)` | Supervisor who made the assignment        |
| `status`          | `ENUM('assigned','investigating','resolved','closed','reassigned')` | NOT NULL, DEFAULT 'assigned'                  | Current assignment status                 |
| `priority`        | `ENUM('low','medium','high','urgent')`                              | NOT NULL, DEFAULT 'medium'                    | Assignment priority                       |
| `assignment_note` | `TEXT`                                                              | NULLABLE                                      | Instructions or context from supervisor   |
| `resolution_note` | `TEXT`                                                              | NULLABLE                                      | Officer's resolution summary              |
| `assigned_at`     | `TIMESTAMPTZ`                                                       | NOT NULL, DEFAULT NOW()                       | When the assignment was made              |
| `response_due_at` | `TIMESTAMPTZ`                                                       | NULLABLE                                      | SLA deadline for initial response         |
| `resolved_at`     | `TIMESTAMPTZ`                                                       | NULLABLE                                      | When status changed to resolved or closed |
| `updated_at`      | `TIMESTAMPTZ`                                                       | NOT NULL, DEFAULT NOW()                       |                                           |

**Indexes:**

- `INDEX` on `(police_user_id, status)`
- `INDEX` on `(report_id, assigned_at DESC)`
- `INDEX` on `priority`

---

## 13. `incident_groups` — Duplicate/Related Incident Grouping

Groups multiple reports that refer to the same physical incident. Used for unified case view.

| Column             | Type                                                     | Constraints                                       | Description                                       |
| ------------------ | -------------------------------------------------------- | ------------------------------------------------- | ------------------------------------------------- |
| `group_id`         | `UUID`                                                   | PK, DEFAULT gen_random_uuid()                     | Unique group identifier                           |
| `group_title`      | `VARCHAR(255)`                                           | NULLABLE                                          | Officer-assigned name for this incident group     |
| `incident_type_id` | `SMALLINT`                                               | NOT NULL, FK → `incident_types(incident_type_id)` | Primary incident category for the group           |
| `center_lat`       | `DECIMAL(10,7)`                                          | NOT NULL                                          | Geographic centroid latitude of the group         |
| `center_lon`       | `DECIMAL(10,7)`                                          | NOT NULL                                          | Geographic centroid longitude of the group        |
| `center_point`     | `GEOMETRY(Point, 4326)`                                  | NOT NULL                                          | PostGIS point for spatial queries                 |
| `location_id`      | `INT`                                                    | NULLABLE, FK → `locations(location_id)`           | Derived administrative location                   |
| `start_time`       | `TIMESTAMPTZ`                                            | NOT NULL                                          | Earliest incident timestamp among member reports  |
| `end_time`         | `TIMESTAMPTZ`                                            | NOT NULL                                          | Latest incident timestamp among member reports    |
| `report_count`     | `INT`                                                    | NOT NULL, DEFAULT 0                               | Number of linked reports (maintained via trigger) |
| `status`           | `ENUM('open','under_investigation','resolved','closed')` | NOT NULL, DEFAULT 'open'                          | Group investigation status                        |
| `created_by`       | `INT`                                                    | NULLABLE, FK → `police_users(police_user_id)`     | Officer who created the group                     |
| `created_at`       | `TIMESTAMPTZ`                                            | NOT NULL, DEFAULT NOW()                           |                                                   |
| `updated_at`       | `TIMESTAMPTZ`                                            | NOT NULL, DEFAULT NOW()                           |                                                   |

---

## 14. `incident_group_members` — Reports Linked to an Incident Group

Join table linking reports to incident groups.

| Column        | Type           | Constraints                                   | Description                                                  |
| ------------- | -------------- | --------------------------------------------- | ------------------------------------------------------------ |
| `group_id`    | `UUID`         | NOT NULL, FK → `incident_groups(group_id)`    | The incident group                                           |
| `report_id`   | `UUID`         | NOT NULL, FK → `reports(report_id)`           | The member report                                            |
| `linked_at`   | `TIMESTAMPTZ`  | NOT NULL, DEFAULT NOW()                       | When the report was linked to the group                      |
| `linked_by`   | `INT`          | NULLABLE, FK → `police_users(police_user_id)` | Officer who linked the report                                |
| `link_reason` | `VARCHAR(100)` | NULLABLE                                      | `manual`, `system_suggested`, `duplicate_media`, `proximity` |

**Primary Key:** `(group_id, report_id)`

---

## 15. `hotspots` — DBSCAN-Detected Risk Clusters

Each row represents one geographic cluster identified in a single DBSCAN execution run.

| Column                       | Type                                     | Constraints                                       | Description                                                                          |
| ---------------------------- | ---------------------------------------- | ------------------------------------------------- | ------------------------------------------------------------------------------------ |
| `hotspot_id`                 | `UUID`                                   | PK, DEFAULT gen_random_uuid()                     | Unique cluster identifier                                                            |
| `run_id`                     | `UUID`                                   | NOT NULL, FK → `hotspot_run_logs(run_id)`         | The DBSCAN run that produced this cluster                                            |
| `cluster_label`              | `INT`                                    | NOT NULL                                          | DBSCAN internal cluster number (-1 = noise; noise points are NOT stored as hotspots) |
| `center_lat`                 | `DECIMAL(10,7)`                          | NOT NULL                                          | Weighted centroid latitude                                                           |
| `center_lon`                 | `DECIMAL(10,7)`                          | NOT NULL                                          | Weighted centroid longitude                                                          |
| `center_point`               | `GEOMETRY(Point, 4326)`                  | NOT NULL                                          | PostGIS centroid for map rendering                                                   |
| `boundary_polygon`           | `GEOMETRY(Polygon, 4326)`                | NULLABLE                                          | Convex hull polygon of the cluster (for map shading)                                 |
| `radius_meters`              | `DECIMAL(8,2)`                           | NOT NULL                                          | Approximate radius from centroid to farthest member point                            |
| `incident_count`             | `INT`                                    | NOT NULL                                          | Number of reports in this cluster                                                    |
| `mean_trust_score`           | `DECIMAL(5,2)`                           | NOT NULL                                          | Average final_trust_score of cluster members                                         |
| `weighted_incident_count`    | `DECIMAL(8,2)`                           | NOT NULL                                          | Sum of trust weights of all member reports                                           |
| `cluster_density`            | `DECIMAL(10,4)`                          | NOT NULL                                          | Reports per square kilometer                                                         |
| `dominant_incident_type_id`  | `SMALLINT`                               | NULLABLE, FK → `incident_types(incident_type_id)` | Most frequent incident type                                                          |
| `incident_type_distribution` | `JSONB`                                  | NULLABLE                                          | Counts of all incident types: `{"THEFT": 5, "VANDALISM": 2}`                         |
| `risk_level`                 | `ENUM('low','medium','high','critical')` | NOT NULL                                          | Risk classification for map display                                                  |
| `time_window_hours`          | `INT`                                    | NOT NULL                                          | Time window used for this run (168 = 7 days, 720 = 30 days, 2160 = 90 days)          |
| `time_window_start`          | `TIMESTAMPTZ`                            | NOT NULL                                          | Start of the time window for member reports                                          |
| `time_window_end`            | `TIMESTAMPTZ`                            | NOT NULL                                          | End of the time window for member reports                                            |
| `location_id`                | `INT`                                    | NULLABLE, FK → `locations(location_id)`           | Administrative area containing this hotspot centroid                                 |
| `eps_radius_meters`          | `DECIMAL(8,2)`                           | NOT NULL                                          | EPS parameter used in DBSCAN run                                                     |
| `min_samples`                | `INT`                                    | NOT NULL                                          | min_samples parameter used                                                           |
| `is_active`                  | `BOOLEAN`                                | NOT NULL, DEFAULT TRUE                            | FALSE for historical/superseded clusters                                             |
| `detected_at`                | `TIMESTAMPTZ`                            | NOT NULL, DEFAULT NOW()                           | When this cluster was computed                                                       |

**Indexes:**

- `GIST INDEX` on `center_point`
- `GIST INDEX` on `boundary_polygon`
- `INDEX` on `(is_active, risk_level)`
- `INDEX` on `run_id`

---

## 16. `hotspot_reports` — Reports Contributing to a Hotspot

Join table linking reports to the hotspot clusters they belong to.

| Column                   | Type           | Constraints                           | Description                                                   |
| ------------------------ | -------------- | ------------------------------------- | ------------------------------------------------------------- |
| `hotspot_id`             | `UUID`         | NOT NULL, FK → `hotspots(hotspot_id)` | The hotspot cluster                                           |
| `report_id`              | `UUID`         | NOT NULL, FK → `reports(report_id)`   | The member report                                             |
| `trust_weight`           | `DECIMAL(5,4)` | NOT NULL                              | Normalized trust weight used in weighted centroid calculation |
| `distance_from_center_m` | `DECIMAL(8,2)` | NULLABLE                              | Meters from this report to cluster centroid                   |

**Primary Key:** `(hotspot_id, report_id)`

**Indexes:**

- `INDEX` on `report_id` for reverse lookup (which cluster is this report in?)

---

## 17. `hotspot_run_logs` — DBSCAN Execution Metadata

One row per DBSCAN run. Tracks parameters used, performance, and results summary.

| Column                     | Type                                          | Constraints                                   | Description                                           |
| -------------------------- | --------------------------------------------- | --------------------------------------------- | ----------------------------------------------------- |
| `run_id`                   | `UUID`                                        | PK, DEFAULT gen_random_uuid()                 | Unique run identifier                                 |
| `run_type`                 | `ENUM('scheduled','manual','parameter_test')` | NOT NULL                                      | How the run was triggered                             |
| `triggered_by`             | `INT`                                         | NULLABLE, FK → `police_users(police_user_id)` | Officer who triggered manual run (NULL for scheduled) |
| `eps_radius_meters`        | `DECIMAL(8,2)`                                | NOT NULL                                      | EPS neighborhood radius used                          |
| `min_samples`              | `INT`                                         | NOT NULL                                      | Minimum points to form a cluster                      |
| `trust_score_threshold`    | `DECIMAL(5,2)`                                | NOT NULL                                      | Minimum report trust score to include in clustering   |
| `time_window_hours`        | `INT`                                         | NOT NULL                                      | Time window size                                      |
| `time_window_start`        | `TIMESTAMPTZ`                                 | NOT NULL                                      | Start of report date range                            |
| `time_window_end`          | `TIMESTAMPTZ`                                 | NOT NULL                                      | End of report date range                              |
| `total_reports_considered` | `INT`                                         | NULLABLE                                      | Reports eligible for this run (above trust threshold) |
| `total_reports_clustered`  | `INT`                                         | NULLABLE                                      | Reports assigned to a cluster                         |
| `noise_point_count`        | `INT`                                         | NULLABLE                                      | Reports classified as noise (-1)                      |
| `clusters_found`           | `INT`                                         | NULLABLE                                      | Number of distinct clusters produced                  |
| `critical_clusters`        | `INT`                                         | NULLABLE                                      | Clusters with risk_level = critical                   |
| `high_clusters`            | `INT`                                         | NULLABLE                                      | Clusters with risk_level = high                       |
| `execution_time_ms`        | `INT`                                         | NULLABLE                                      | Total DBSCAN computation time in milliseconds         |
| `status`                   | `ENUM('running','complete','failed')`         | NOT NULL, DEFAULT 'running'                   | Run status                                            |
| `error_message`            | `TEXT`                                        | NULLABLE                                      | Error detail if status = failed                       |
| `started_at`               | `TIMESTAMPTZ`                                 | NOT NULL, DEFAULT NOW()                       | Run start time                                        |
| `completed_at`             | `TIMESTAMPTZ`                                 | NULLABLE                                      | Run completion time                                   |

---

## 18. `notifications` — System Alerts

Stores all system-generated notifications for police officers. Citizen notifications are delivered via push and not stored server-side beyond a short TTL.

| Column                | Type                                                                                                               | Constraints                                   | Description                                                             |
| --------------------- | ------------------------------------------------------------------------------------------------------------------ | --------------------------------------------- | ----------------------------------------------------------------------- |
| `notification_id`     | `UUID`                                                                                                             | PK, DEFAULT gen_random_uuid()                 | Unique notification ID                                                  |
| `police_user_id`      | `INT`                                                                                                              | NOT NULL, FK → `police_users(police_user_id)` | Recipient officer                                                       |
| `title`               | `VARCHAR(150)`                                                                                                     | NOT NULL                                      | Short notification title                                                |
| `message`             | `TEXT`                                                                                                             | NOT NULL                                      | Full notification message body                                          |
| `type`                | `ENUM('new_report','hotspot_detected','assignment','status_change','system_alert','model_alert','security_alert')` | NOT NULL                                      | Notification category                                                   |
| `priority`            | `ENUM('low','normal','high','critical')`                                                                           | NOT NULL, DEFAULT 'normal'                    | Display urgency                                                         |
| `related_entity_type` | `VARCHAR(50)`                                                                                                      | NULLABLE                                      | Table name: `reports`, `hotspots`, `report_assignments`, etc.           |
| `related_entity_id`   | `UUID`                                                                                                             | NULLABLE                                      | ID of the related entity (cast from relevant PK type)                   |
| `action_url`          | `VARCHAR(500)`                                                                                                     | NULLABLE                                      | Deep link URL within the dashboard for one-click navigation             |
| `is_read`             | `BOOLEAN`                                                                                                          | NOT NULL, DEFAULT FALSE                       | Read state                                                              |
| `read_at`             | `TIMESTAMPTZ`                                                                                                      | NULLABLE                                      | When the notification was opened                                        |
| `is_dismissed`        | `BOOLEAN`                                                                                                          | NOT NULL, DEFAULT FALSE                       | Whether the officer dismissed without acting                            |
| `expires_at`          | `TIMESTAMPTZ`                                                                                                      | NULLABLE                                      | After this time, the notification is hidden (for time-sensitive alerts) |
| `created_at`          | `TIMESTAMPTZ`                                                                                                      | NOT NULL, DEFAULT NOW()                       |                                                                         |

**Indexes:**

- `INDEX` on `(police_user_id, is_read, created_at DESC)` for fast inbox queries
- `INDEX` on `expires_at` for cleanup jobs

---

## 19. `officer_notes` — Internal Investigation Notes

Allows officers to attach internal notes to reports or incident groups. These notes are never visible to citizens.

| Column           | Type          | Constraints                                   | Description                                       |
| ---------------- | ------------- | --------------------------------------------- | ------------------------------------------------- |
| `note_id`        | `UUID`        | PK, DEFAULT gen_random_uuid()                 | Unique note ID                                    |
| `report_id`      | `UUID`        | NULLABLE, FK → `reports(report_id)`           | Associated report (if note is on a report)        |
| `group_id`       | `UUID`        | NULLABLE, FK → `incident_groups(group_id)`    | Associated incident group (if note is on a group) |
| `police_user_id` | `INT`         | NOT NULL, FK → `police_users(police_user_id)` | Officer who wrote the note                        |
| `note_content`   | `TEXT`        | NOT NULL                                      | Note text                                         |
| `is_sensitive`   | `BOOLEAN`     | NOT NULL, DEFAULT FALSE                       | If TRUE, only supervisors and admins can view     |
| `created_at`     | `TIMESTAMPTZ` | NOT NULL, DEFAULT NOW()                       |                                                   |
| `updated_at`     | `TIMESTAMPTZ` | NOT NULL, DEFAULT NOW()                       |                                                   |
| `is_deleted`     | `BOOLEAN`     | NOT NULL, DEFAULT FALSE                       | Soft delete                                       |

**Constraint:** At least one of `report_id` or `group_id` must be non-NULL (enforced by CHECK constraint).

---

## 20. `system_config` — Runtime Configuration Parameters

Key-value store for all system-configurable parameters. Allows admins to change thresholds without code deployments.

| Column          | Type                                            | Constraints                                   | Description                                                                            |
| --------------- | ----------------------------------------------- | --------------------------------------------- | -------------------------------------------------------------------------------------- |
| `config_key`    | `VARCHAR(100)`                                  | PK                                            | Unique configuration key (e.g. `trust_formula.rf_weight`)                              |
| `config_value`  | `TEXT`                                          | NOT NULL                                      | Serialized value (stored as string; application parses to correct type)                |
| `value_type`    | `ENUM('float','int','boolean','string','json')` | NOT NULL                                      | How to deserialize config_value                                                        |
| `default_value` | `TEXT`                                          | NOT NULL                                      | Original default for reset operations                                                  |
| `description`   | `TEXT`                                          | NULLABLE                                      | Human-readable explanation of this parameter                                           |
| `category`      | `VARCHAR(50)`                                   | NOT NULL                                      | Grouping: `trust_formula`, `rule_checks`, `dbscan`, `notifications`, `retention`, `ml` |
| `is_sensitive`  | `BOOLEAN`                                       | NOT NULL, DEFAULT FALSE                       | TRUE for API keys and secrets (values displayed masked in UI)                          |
| `updated_by`    | `INT`                                           | NULLABLE, FK → `police_users(police_user_id)` | Admin who last changed this value                                                      |
| `updated_at`    | `TIMESTAMPTZ`                                   | NOT NULL, DEFAULT NOW()                       |                                                                                        |

**Example rows:**

| config_key                             | config_value | value_type | category        |
| -------------------------------------- | ------------ | ---------- | --------------- |
| `trust_formula.rf_weight`              | `0.40`       | `float`    | `trust_formula` |
| `trust_formula.rules_weight`           | `0.25`       | `float`    | `trust_formula` |
| `trust_formula.device_weight`          | `0.20`       | `float`    | `trust_formula` |
| `trust_formula.ai_weight`              | `0.15`       | `float`    | `trust_formula` |
| `rule_checks.gps_accuracy_threshold_m` | `500`        | `int`      | `rule_checks`   |
| `rule_checks.max_speed_kmh`            | `200`        | `int`      | `rule_checks`   |
| `rule_checks.min_description_chars`    | `20`         | `int`      | `rule_checks`   |
| `rule_checks.max_reports_per_hour`     | `10`         | `int`      | `rule_checks`   |
| `dbscan.default_eps_meters`            | `100`        | `int`      | `dbscan`        |
| `dbscan.default_min_samples`           | `5`          | `int`      | `dbscan`        |
| `dbscan.schedule_interval_hours`       | `6`          | `int`      | `dbscan`        |
| `dbscan.min_trust_score_threshold`     | `40`         | `int`      | `dbscan`        |
| `retention.reports_days`               | `730`        | `int`      | `retention`     |
| `retention.audit_log_days`             | `1825`       | `int`      | `retention`     |

---

## 21. `ml_model_registry` — Trained Model Version Tracking

Tracks all trained ML models and controls which version is active in production.

| Column                  | Type                                                         | Constraints                                   | Description                                                            |
| ----------------------- | ------------------------------------------------------------ | --------------------------------------------- | ---------------------------------------------------------------------- |
| `model_id`              | `INT`                                                        | PK, SERIAL                                    | Unique model record ID                                                 |
| `model_name`            | `VARCHAR(100)`                                               | NOT NULL                                      | Human-readable name (e.g. `Random Forest Authenticator v2`)            |
| `model_type`            | `VARCHAR(50)`                                                | NOT NULL                                      | `random_forest`, `anomaly_detector`, `vision_quality`, `nlp_sentiment` |
| `version_tag`           | `VARCHAR(50)`                                                | NOT NULL, UNIQUE                              | Version string (e.g. `rf_v2.1.0`)                                      |
| `artifact_path`         | `VARCHAR(500)`                                               | NOT NULL                                      | Path to serialized model file (.pkl)                                   |
| `training_dataset_size` | `INT`                                                        | NULLABLE                                      | Number of labeled reports used for training                            |
| `training_date`         | `TIMESTAMPTZ`                                                | NULLABLE                                      | When training was completed                                            |
| `feature_count`         | `INT`                                                        | NULLABLE                                      | Number of input features                                               |
| `feature_list`          | `JSONB`                                                      | NULLABLE                                      | List of feature names in model input order                             |
| `precision_score`       | `DECIMAL(5,4)`                                               | NULLABLE                                      | Evaluation precision on test set                                       |
| `recall_score`          | `DECIMAL(5,4)`                                               | NULLABLE                                      | Evaluation recall on test set                                          |
| `f1_score`              | `DECIMAL(5,4)`                                               | NULLABLE                                      | Evaluation F1 on test set                                              |
| `auc_roc`               | `DECIMAL(5,4)`                                               | NULLABLE                                      | AUC-ROC on test set                                                    |
| `confusion_matrix`      | `JSONB`                                                      | NULLABLE                                      | Full confusion matrix as JSON                                          |
| `hyperparameters`       | `JSONB`                                                      | NULLABLE                                      | Hyperparameters used (n_estimators, max_depth, etc.)                   |
| `status`                | `ENUM('training','staging','production','retired','failed')` | NOT NULL, DEFAULT 'staging'                   | Deployment status                                                      |
| `promoted_at`           | `TIMESTAMPTZ`                                                | NULLABLE                                      | When this model was promoted to production                             |
| `promoted_by`           | `INT`                                                        | NULLABLE, FK → `police_users(police_user_id)` | Admin who approved the promotion                                       |
| `retired_at`            | `TIMESTAMPTZ`                                                | NULLABLE                                      | When this model was retired                                            |
| `notes`                 | `TEXT`                                                       | NULLABLE                                      | Admin notes on this model version                                      |
| `created_at`            | `TIMESTAMPTZ`                                                | NOT NULL, DEFAULT NOW()                       |                                                                        |

**Constraint:** Only one row can have `status = 'production'` per `model_type`. Enforced by partial unique index: `UNIQUE INDEX` on `(model_type)` WHERE `status = 'production'`.

---

## 22. `audit_logs` — Security and Accountability

Append-only, tamper-evident log of all officer actions and system events. Never soft-deleted; never updated.

| Column           | Type                                           | Constraints                                  | Description                                                  |
| ---------------- | ---------------------------------------------- | -------------------------------------------- | ------------------------------------------------------------ |
| `log_id`         | `BIGINT`                                       | PK, SERIAL                                   | Auto-incrementing log ID                                     |
| `actor_type`     | `ENUM('police_user','system','celery_worker')` | NOT NULL                                     | Who performed the action                                     |
| `actor_id`       | `INT`                                          | NULLABLE                                     | Police user ID (NULL for system/worker actors)               |
| `action_type`    | `VARCHAR(100)`                                 | NOT NULL                                     | Standardized action code (see action types below)            |
| `entity_type`    | `VARCHAR(50)`                                  | NULLABLE                                     | Table/entity being acted on (e.g. `reports`, `police_users`) |
| `entity_id`      | `VARCHAR(36)`                                  | NULLABLE                                     | ID of the entity (UUID or INT stored as string)              |
| `action_details` | `JSONB`                                        | NULLABLE                                     | Before/after values, parameters, or context                  |
| `ip_address`     | `INET`                                         | NULLABLE                                     | Officer's IP address at time of action                       |
| `user_agent`     | `TEXT`                                         | NULLABLE                                     | Browser/client user agent string                             |
| `success`        | `BOOLEAN`                                      | NOT NULL, DEFAULT TRUE                       | Whether the action succeeded                                 |
| `error_message`  | `TEXT`                                         | NULLABLE                                     | Error description if success = FALSE                         |
| `session_id`     | `UUID`                                         | NULLABLE, FK → `police_sessions(session_id)` | Session that performed the action                            |
| `created_at`     | `TIMESTAMPTZ`                                  | NOT NULL, DEFAULT NOW()                      | When the event occurred                                      |

**Indexes:**

- `INDEX` on `(actor_id, created_at DESC)` for officer activity queries
- `INDEX` on `(entity_type, entity_id)` for entity-specific history
- `INDEX` on `action_type`
- `INDEX` on `created_at DESC` for log browsing

**Defined action_type values:**

| action_type                   | Trigger                                  |
| ----------------------------- | ---------------------------------------- |
| `REPORT_SUBMITTED`            | New citizen report received              |
| `REPORT_STATUS_CHANGED`       | Report review_status updated             |
| `REPORT_ASSIGNED`             | Report assigned to officer               |
| `REPORT_VERIFIED`             | Report confirmed by officer              |
| `REPORT_REJECTED`             | Report rejected by officer               |
| `REPORT_DELETED`              | Report soft-deleted                      |
| `REPORT_FLAGGED_DUPLICATE`    | Report marked as duplicate               |
| `EVIDENCE_DOWNLOADED`         | Officer downloaded media file            |
| `EVIDENCE_FLAGGED`            | Officer manually flagged evidence        |
| `GROUP_CREATED`               | Incident group created                   |
| `GROUP_REPORT_LINKED`         | Report added to group                    |
| `GROUP_CLOSED`                | Incident group closed                    |
| `HOTSPOT_RUN_TRIGGERED`       | DBSCAN run started                       |
| `HOTSPOT_RUN_COMPLETE`        | DBSCAN run finished                      |
| `ML_MODEL_PROMOTED`           | Model version set to production          |
| `ML_MODEL_RETIRED`            | Model version retired                    |
| `OFFICER_LOGIN`               | Successful login                         |
| `OFFICER_LOGIN_FAILED`        | Failed login attempt                     |
| `OFFICER_LOGOUT`              | Explicit logout                          |
| `OFFICER_ACCOUNT_CREATED`     | New officer account created              |
| `OFFICER_ACCOUNT_DEACTIVATED` | Officer account disabled                 |
| `OFFICER_PASSWORD_CHANGED`    | Password changed                         |
| `OFFICER_ROLE_CHANGED`        | Role updated                             |
| `DEVICE_BLACKLISTED`          | Device trust score floored / blacklisted |
| `DEVICE_SPAM_FLAGGED`         | Device manually flagged for spam         |
| `CONFIG_CHANGED`              | system_config value updated              |
| `TRUST_FORMULA_CHANGED`       | Trust formula weights updated            |

---

## Entity Relationship Summary

```
devices ─────────────────────────────────────────┐
    │ 1                                           │
    │ N                                           │
reports ──────────── evidence_files               │
    │  │                                          │
    │  ├──── report_rule_checks (1:1)             │
    │  ├──── ml_predictions (1:N)                 │
    │  ├──── police_reviews (1:N)                 │
    │  ├──── report_assignments (1:N)             │
    │  ├──── incident_group_members (N:M) ──── incident_groups
    │  └──── hotspot_reports (N:M) ─────────── hotspots
    │                                           │
    │                                     hotspot_run_logs
    │
police_users ──── police_reviews
    │         ├── report_assignments
    │         ├── officer_notes
    │         ├── notifications
    │         ├── police_sessions
    │         └── audit_logs

incident_types ── reports
               └─ incident_groups
                └─ hotspots

locations ── reports
          ├─ police_users
          ├─ incident_groups
          └─ hotspots

ml_model_registry ── ml_predictions
                  └─ police_reviews (training_run_id)

system_config (standalone key-value configuration)
device_trust_history ── devices
```

```

```
