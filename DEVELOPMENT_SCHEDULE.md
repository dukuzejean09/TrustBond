# TrustBond — Development Schedule

**Duration:** 10 Weeks (Feb 10, 2026 – Apr 27, 2026)  
**Methodology:** Agile (1-week sprints)  
**Team Setup:** Full-stack development with parallel workstreams

---

## High-Level Phase Overview

| Phase                                       | Weeks     | Focus                                                              |
| ------------------------------------------- | --------- | ------------------------------------------------------------------ |
| Phase 1 — Foundation & Backend Core         | Week 1–2  | Environment setup, DB schema, auth, core API                       |
| Phase 2 — ML Pipeline & Verification Engine | Week 3–4  | Data prep, Random Forest model, rule-based checks, AI verification |
| Phase 3 — Mobile App (Flutter)              | Week 3–5  | Citizen reporting app with evidence capture                        |
| Phase 4 — Police Dashboard (React)          | Week 5–7  | Case management, analytics, hotspot visualization                  |
| Phase 5 — Integration & Hotspot Detection   | Week 7–8  | DBSCAN, trust scoring, end-to-end integration                      |
| Phase 6 — Testing, Hardening & Deployment   | Week 9–10 | Field testing, security audit, deployment                          |

---

## Detailed Week-by-Week Breakdown

---

### WEEK 1 (Feb 10 – Feb 16): Project Setup & Database Foundation

**Goal:** Establish the entire development environment and data layer.

- [x] Initialize Git repository with branching strategy (`main`, `develop`, `feature/*`)
- [x] Set up Python virtual environment, install FastAPI, Uvicorn, SQLAlchemy, Alembic
- [x] Design and implement PostgreSQL database schema with PostGIS extension (14 tables):
  - `devices` — anonymous reporter devices (device_hash, device_trust_score, total/trusted/flagged reports)
  - `incident_types` — incident categories (type_name, severity_weight, is_active)
  - `reports` — raw incident submissions (GPS, motion_level, movement_speed, was_stationary, rule_status, is_flagged, feature_vector JSONB, ai_ready)
  - `evidence_files` — report evidence (file_url, file_type, media GPS, is_live_capture, perceptual_hash, blur_score, tamper_score, ai_quality_label)
  - `ml_predictions` — ML outputs (trust_score, prediction_label, confidence, explanation JSONB, model_type, is_final)
  - `police_users` — police accounts & roles (badge_number, role ENUM, assigned_location_id)
  - `police_reviews` — ground truth decisions (decision, ground_truth_label, confidence_level, used_for_training)
  - `locations` — administrative boundaries for Musanze (location_type sector/cell/village, geometry GEOMETRY, parent hierarchy)
  - `hotspots` — DBSCAN risk clusters (center coords, radius_meters, risk_level, time_window_hours)
  - `hotspot_reports` — hotspot-report membership (composite PK)
  - `incident_groups` — duplicate incident grouping (center coords, time range, report_count)
  - `report_assignments` — case handling workflow (status, priority, assigned/completed timestamps)
  - `notifications` — system alerts (type: report/hotspot/assignment/system, related_entity_type/id)
  - `audit_logs` — security & accountability (actor_type, action_type, entity_type, ip_address, success)
- [x] Write Alembic migration scripts
- [x] Set up Docker Compose for local PostgreSQL + PostGIS
- [x] Configure Cloudinary account and test media upload/retrieval
- [x] Set up project folder structure for backend:
  ```
  backend/
  ├── app/
  │   ├── api/           # Route handlers
  │   ├── core/          # Config, security, deps
  │   ├── models/        # SQLAlchemy models
  │   ├── schemas/       # Pydantic schemas
  │   ├── services/      # Business logic
  │   ├── ml/            # ML models & verification
  │   └── utils/         # Helpers
  ├── alembic/
  ├── tests/
  └── requirements.txt
  ```

**Deliverable:** Running PostgreSQL/PostGIS database with complete schema, FastAPI project skeleton.

---

### WEEK 2 (Feb 17 – Feb 23): Core Backend API & Authentication

**Goal:** Build all essential API endpoints and secure authentication.

- [x] Implement JWT-based authentication for `police_users` (role-based: admin, supervisor, officer)
- [x] Implement pseudonymous device registration endpoint (SHA-256 → `devices.device_hash`)
- [x] Build Incident Types API:
  - `GET /api/incident-types` — list active categories from `incident_types`
  - `POST /api/incident-types` — admin creates new types (type_name, severity_weight)
- [x] Build Report Submission API:
  - `POST /api/reports` — accept incident data + GPS + motion_level + movement_speed + was_stationary + village_location_id (FK → `locations`)
  - `GET /api/reports` — list/filter reports for dashboard (join `incident_types`, `devices`, `ml_predictions`)
  - `GET /api/reports/{id}` — single report with evidence_files, ml_predictions, police_reviews, assignments
  - `PATCH /api/reports/{id}` — update rule_status, is_flagged
- [x] Build Evidence Files API:
  - `POST /api/reports/{id}/evidence` — upload to Cloudinary, store in `evidence_files` (file_url, file_type, media GPS, is_live_capture)
  - `GET /api/reports/{id}/evidence` — retrieve evidence for a report
- [x] Build Device Trust API:
  - `GET /api/devices/{hash}` — retrieve device record with trust score, total/trusted/flagged counts
  - Internal logic: update `devices.device_trust_score` after each `police_reviews` decision
- [x] Build Police Users API:
  - `POST /api/auth/login` — JWT login (update `police_users.last_login_at`)
  - `GET /api/police-users` — list officers (filterable by role, assigned_location_id)
  - `POST /api/police-users` — create officer (admin only: first_name, last_name, email, phone, badge_number, role, assigned_location_id)
  - `PATCH /api/police-users/{id}` — update officer, toggle is_active
- [x] Build Locations API:
  - `GET /api/locations` — list Musanze admin boundaries (sectors → cells → villages hierarchy)
  - `GET /api/locations/{id}` — single location with geometry
- [x] Implement Cloudinary upload service (photo/video evidence)
- [x] Write Pydantic schemas matching all 14 database tables
- [x] Set up CORS middleware, rate limiting
- [x] Write `audit_logs` entries for all state-changing API calls (actor_type, action_type, entity_type, entity_id, ip_address)
- [x] Write unit tests for core endpoints

**Deliverable:** Fully functional REST API covering all 14 tables, JWT auth, report CRUD, evidence upload, device tracking, locations, and audit logging.

---

### WEEK 3 (Feb 24 – Mar 2): Rule-Based Verification & ML Data Preparation

**Goal:** Implement deterministic verification checks and prepare ML training data.

#### Rule-Based Verification Pipeline

- [ ] GPS validation:
  - Check coordinates fall within Rwanda/Musanze bounds
  - Flag impossible GPS accuracy values (>1000m)
  - Detect GPS spoofing via speed checks between consecutive reports
- [ ] Timestamp validation:
  - Reject future-dated reports
  - Flag reports with `time_since_incident > 168 hours`
  - Detect timestamp anomalies (timezone mismatches)
- [ ] Evidence metadata checks:
  - EXIF data extraction and validation
  - EXIF GPS vs submitted GPS comparison
  - Image metadata consistency scoring
- [ ] Duplicate detection:
  - Perceptual hashing (pHash) for submitted images
  - Hamming distance comparison against existing report images
  - Flag duplicate media submissions
- [ ] Device trust formula (updates `devices.device_trust_score` using `devices` columns):

  ```
  device_trust_score = (
      base_score
      + (trusted_reports / total_reports × w1)
      - (flagged_reports / total_reports × w2)
      + (consistency_bonus × w3)
  )
  ```

  - Inputs: `devices.total_reports`, `devices.trusted_reports`, `devices.flagged_reports`
  - Triggered after each `police_reviews` entry (decision = confirmed → trusted++, rejected → flagged++)

#### ML Data Preparation

- [ ] Build feature extraction pipeline that populates `reports.feature_vector` (JSONB) and sets `reports.ai_ready = true`:
  - Report-level: description length, evidence count, gps_accuracy, motion_level, movement_speed, was_stationary
  - Device-level: `devices.total_reports`, `devices.trusted_reports`, `devices.flagged_reports`, `devices.device_trust_score`
  - Evidence-level: `evidence_files.blur_score`, `evidence_files.tamper_score`, `evidence_files.is_live_capture`, `evidence_files.ai_quality_label`
  - Temporal: time since incident, reporting frequency per device
  - Set `reports.features_extracted` timestamp on completion
- [ ] Generate synthetic training data matching schema columns
- [ ] Label using `police_reviews.ground_truth_label` (real / fake) where `used_for_training = true`
- [ ] Split data into train/validation/test sets (70/15/15)

**Deliverable:** Working rule-based verification pipeline, labeled dataset ready for model training.

---

### WEEK 3–4 (Feb 24 – Mar 9): Flutter Mobile App — Core Features (Parallel Track)

**Goal:** Build the citizen-facing mobile application with core reporting functionality.

#### Week 3 — App Foundation

- [ ] Initialize Flutter project with clean architecture:
  ```
  lib/
  ├── config/        # API config, constants, themes
  ├── models/        # Data models
  ├── providers/     # State management
  ├── screens/       # UI screens
  ├── services/      # API & device services
  └── main.dart
  ```
- [ ] Implement pseudonymous device ID generation (SHA-256 of device attributes)
- [ ] Build onboarding/welcome screens (no login required — anonymous)
- [ ] Implement report submission screen:
  - Incident type selector (fetched from `incident_types` API)
  - Description text field
  - Automatic GPS capture (latitude, longitude, gps_accuracy)
  - Motion sensor data capture (motion_level, movement_speed, was_stationary)
  - Automatic timestamp capture (reported_at)
  - Auto-resolve village_location_id via GPS → `locations` lookup
- [ ] Set up API service layer connecting to FastAPI backend

#### Week 4 — Evidence & Offline Support

- [ ] Implement camera integration for photo/video evidence capture:
  - Capture media GPS (media_latitude, media_longitude)
  - Record capture timestamp (captured_at)
  - Detect if live capture (is_live_capture flag)
- [ ] Implement gallery picker for existing media
- [ ] Build evidence preview and multi-file attachment UI (maps to `evidence_files`)
- [ ] Implement offline report queue (store locally, sync when connected)
- [ ] Build report history screen (user's own submissions via device_hash, anonymized)
- [ ] Add network status indicator and connectivity handling
- [ ] Implement local notifications for submission confirmation

**Deliverable:** Functional Flutter app capable of anonymous incident reporting with evidence.

---

### WEEK 4 (Mar 2 – Mar 9): Random Forest Model & AI-Assisted Verification

**Goal:** Train the ML model and implement AI verification checks.

#### Random Forest Classifier

- [ ] Train Random Forest model using scikit-learn:
  - Input: `reports.feature_vector` (JSONB) — only where `reports.ai_ready = true`
  - Target: `police_reviews.ground_truth_label` (real / fake) — only where `used_for_training = true`
  - Hyperparameter tuning via GridSearchCV
- [ ] Evaluate model performance:
  - Precision, Recall, F1-score per class
  - Confusion matrix analysis
  - Feature importance ranking → stored in `ml_predictions.explanation` (JSONB / SHAP values)
- [ ] Export trained model (joblib/pickle) for API integration
- [ ] Build prediction endpoint: `POST /api/ml/predict` → writes to `ml_predictions` table:
  - `trust_score`, `prediction_label` (likely_real / suspicious / fake)
  - `confidence`, `model_version`, `model_type` = 'random_forest'
  - `processing_time` (ms), `is_final = true` for production predictions
- [ ] Implement authenticity score output (probability 0.0–1.0)

#### AI-Assisted Verification (OpenCV + lightweight checks) → writes to `evidence_files`

- [ ] Image quality assessment:
  - Blur detection (Laplacian variance) → `evidence_files.blur_score`
  - Tampering/manipulation analysis → `evidence_files.tamper_score`
  - Combined assessment → `evidence_files.ai_quality_label` (good / poor / suspicious)
  - Set `evidence_files.ai_checked_at` timestamp
- [ ] Perceptual hashing for duplicate detection:
  - Compute pHash → `evidence_files.perceptual_hash`
  - Compare Hamming distance against existing hashes in DB
  - Flag duplicates in `reports.is_flagged`
- [ ] GPS anomaly detection (speed-based using `reports.movement_speed`, geographic bounds via `locations`)
- [ ] Timestamp anomaly detection (statistical outlier detection on `reports.reported_at`)
- [ ] Anomaly model predictions → `ml_predictions` with `model_type` = 'anomaly' or 'vision'

#### Integration

- [ ] Wire verification pipeline: Rule-based (`reports.rule_status`) → AI checks (`evidence_files` scores) → RF prediction (`ml_predictions`) → Final trust update (`devices.device_trust_score`)
- [ ] Implement background task processing with Celery + Redis for ML inference
- [ ] All ML results stored in `ml_predictions`; evidence analysis in `evidence_files`

**Deliverable:** Trained Random Forest model integrated into API, complete AI verification pipeline.

---

### WEEK 5 (Mar 10 – Mar 16): Flutter App Polish & React Dashboard Start

**Goal:** Finalize mobile app; begin police dashboard.

#### Flutter — Final Features

- [ ] Build community safety map screen (public-facing, anonymized clusters)
- [ ] Implement pull-to-refresh and pagination for report lists
- [ ] Add app settings screen (language preference, notification toggle)
- [ ] UI polish: loading states, error handling, empty states
- [ ] Handle edge cases: no GPS, no camera permission, large files
- [ ] Test on multiple Android devices / emulators

#### React Dashboard — Foundation

- [ ] Set up React project with Tailwind CSS (already bootstrapped in `dashboard-react/`)
- [ ] Implement authentication flow (JWT login for officers)
- [ ] Build Layout component (sidebar navigation, header, responsive design)
- [ ] Build Dashboard home page:
  - Total reports stat card (count from `reports`)
  - Reports by `reports.rule_status` (passed / flagged / rejected)
  - Reports by `incident_types.type_name` chart
  - Recent reports table (join `reports` + `devices` + `ml_predictions` + `incident_types`)
  - ML trust score distribution (`ml_predictions.trust_score` where `is_final = true`)
  - Device trust overview (`devices.device_trust_score` averages)
  - Pending assignments count (from `report_assignments` where status = 'assigned')
  - Unread notifications badge (from `notifications` where `is_read = false`)

**Deliverable:** Production-ready mobile app; dashboard with auth and home page.

---

### WEEK 6 (Mar 17 – Mar 23): React Dashboard — Case Management & Reports

**Goal:** Build core case management and report viewing features.

- [ ] Build Reports page (data from `reports` + `incident_types` + `devices` + `ml_predictions`):
  - Filterable data table (by `reports.rule_status`, `incident_types.type_name`, date range, `ml_predictions.trust_score`)
  - Report detail modal with:
    - Evidence viewer (`evidence_files` — images/video from Cloudinary URLs)
    - AI verification details: `blur_score`, `tamper_score`, `ai_quality_label`, `perceptual_hash` matches
    - ML prediction panel: `prediction_label`, `trust_score`, `confidence`, `explanation` (SHAP)
    - Rule check status: `reports.rule_status` (passed/flagged/rejected)
    - Device trust info: `devices.device_trust_score`, total/trusted/flagged counts
  - Police Review actions → writes to `police_reviews` (confirmed / rejected / investigation)
    - Officer selects `ground_truth_label` (real / fake), `confidence_level`
    - Checkbox for `used_for_training` (allow model retraining)
- [ ] Build Report Assignments page (data from `report_assignments`):
  - Assign reports to officers (`police_user_id`) with priority (low/medium/high/urgent)
  - Track workflow: assigned → investigating → resolved → closed
  - Show `assigned_at`, `completed_at` timestamps
- [ ] Build Incident Groups page (data from `incident_groups`):
  - View grouped duplicate reports (same incident, multiple submissions)
  - Show center location, time range, report_count
  - Drill into individual reports within a group
- [ ] Build Officers management page (data from `police_users`):
  - Add/edit officers: first_name, last_name, email, phone, badge_number, role, assigned_location_id
  - Toggle `is_active` status
  - Role-based access control (admin / supervisor / officer)
  - Show `last_login_at`
- [ ] Build Activity Log page (data from `audit_logs`):
  - Display: actor_type, action_type, entity_type, entity_id, ip_address, success, timestamp
  - Filterable by actor (system vs police_user), action_type, date range
- [ ] Build Notifications page (data from `notifications`):
  - Show: title, message, type (report/hotspot/assignment/system)
  - Link to related entity via `related_entity_type` + `related_entity_id`
  - Mark as read (`is_read` toggle)

**Deliverable:** Fully functional report management, police reviews, report assignments, incident groups, officers, activity log, and notifications UI — all mapped to schema tables.

---

### WEEK 7 (Mar 24 – Mar 30): Hotspot Detection & Analytics Dashboard

**Goal:** Implement DBSCAN clustering and analytics visualization.

#### Trust-Weighted DBSCAN → writes to `hotspots` + `hotspot_reports`

- [ ] Implement trust-weighted DBSCAN algorithm:
  - Input: `reports` where `rule_status = 'passed'` and `ai_ready = true`
  - Weight each point by `ml_predictions.trust_score` (where `is_final = true`)
  - Configurable eps_radius → stored as `hotspots.radius_meters`
  - Time window filtering → `hotspots.time_window_hours` (168, 720, 2160 = 7d, 30d, 90d)
  - Category-based filtering via `reports.incident_type_id`
- [ ] Build hotspot API endpoints:
  - `GET /api/hotspots` — retrieve from `hotspots` table (center_lat, center_long, radius_meters, incident_count, risk_level)
  - `GET /api/hotspots/{id}/reports` — retrieve linked reports via `hotspot_reports` join
  - `GET /api/hotspots/map-data` — GeoJSON for map rendering using `locations.geometry`
  - `POST /api/hotspots/recalculate` — trigger reclustering, rebuild `hotspot_reports` associations
- [ ] Assign `hotspots.risk_level` (low / medium / high) based on cluster density, incident_count, and trust weights
- [ ] Generate `notifications` (type = 'hotspot') when new high-risk clusters detected
- [ ] Schedule periodic recalculation (Celery beat task)

#### Analytics & Visualization (Dashboard)

- [ ] Build Hotspots page (data from `hotspots` + `hotspot_reports` + `locations`):
  - Interactive map (Leaflet.js) with cluster visualization at `hotspots.center_lat/center_long`
  - Cluster circles sized by `hotspots.radius_meters`, colored by `hotspots.risk_level`
  - Heatmap overlay toggle
  - Click-to-drill-down: show linked reports via `hotspot_reports`
  - Time range selector matching `hotspots.time_window_hours`
  - Overlay `locations.geometry` (sector/cell/village boundaries)
- [ ] Build Analytics page (aggregating across all tables):
  - Incident trends over time (from `reports.reported_at`)
  - Category distribution by `incident_types.type_name` with `severity_weight`
  - ML trust score distribution (`ml_predictions.trust_score` histogram)
  - `reports.rule_status` breakdown (passed/flagged/rejected)
  - Device trust trends (`devices.device_trust_score` over time)
  - Police review rate (`police_reviews` confirmed vs rejected vs investigation)
  - Evidence quality summary (`evidence_files.ai_quality_label` distribution)
  - Geographic distribution by `locations` hierarchy
- [ ] Build Settings page:
  - DBSCAN parameter configuration (eps, min_samples, time_window)
  - `incident_types` management (add/edit categories, severity_weight)
  - Notification thresholds
  - System configuration

**Deliverable:** Working hotspot detection with map visualization, comprehensive analytics dashboard.

---

### WEEK 8 (Mar 31 – Apr 6): End-to-End Integration & Community Safety Map

**Goal:** Connect all components and build the public safety map.

- [ ] End-to-end flow testing (mapped to database):
  1. Flutter app generates `device_hash` → `devices` table (first_seen_at set)
  2. Submit report → `reports` table (latitude, longitude, gps_accuracy, motion_level, movement_speed, was_stationary, village_location_id)
  3. Upload evidence → `evidence_files` table (file_url via Cloudinary, media GPS, is_live_capture)
  4. Rule-based checks → `reports.rule_status` updated (passed/flagged/rejected)
  5. AI checks → `evidence_files` updated (blur_score, tamper_score, perceptual_hash, ai_quality_label, ai_checked_at)
  6. Feature extraction → `reports.feature_vector` populated, `reports.ai_ready = true`, `reports.features_extracted` set
  7. Random Forest → `ml_predictions` created (trust_score, prediction_label, confidence, explanation, model_version, model_type, is_final)
  8. Device trust recalculated → `devices.device_trust_score` updated based on total/trusted/flagged
  9. Report appears in dashboard with all joined data
  10. Officer reviews → `police_reviews` (decision, ground_truth_label, confidence_level, used_for_training)
  11. Assignment created → `report_assignments` (status, priority)
  12. DBSCAN recalculates → `hotspots` + `hotspot_reports` rebuilt
  13. Notifications generated → `notifications` for relevant officers
  14. All actions logged → `audit_logs`
  15. Safety map & community map update with anonymized hotspot data
- [ ] Build Community Safety Map (public-facing):
  - Anonymized `hotspots` display (center_lat/center_long, radius_meters — no individual report locations)
  - Risk level color coding from `hotspots.risk_level` (low/medium/high)
  - Category filtering by `incident_types`
  - `locations.geometry` overlay (sector/cell/village boundaries)
  - Mobile-responsive design
- [ ] Implement real-time updates (WebSocket or polling) for dashboard
- [ ] API error handling and edge case coverage
- [ ] Performance optimization:
  - Database query optimization and indexing
  - API response caching where appropriate
  - Image processing optimization
- [ ] Fix integration bugs discovered during end-to-end testing

**Deliverable:** Fully integrated system with all components communicating correctly.

---

### WEEK 9 (Apr 7 – Apr 13): Testing & Security Hardening

**Goal:** Comprehensive testing and security audit.

#### Functional Testing

- [ ] Backend unit tests (pytest): ≥80% coverage on core services
- [ ] API integration tests for all endpoints
- [ ] ML model validation against held-out test set
- [ ] Flutter widget and integration tests
- [ ] Dashboard component tests
- [ ] Cross-browser testing for dashboard (Chrome, Firefox, Edge)

#### Security Audit

- [ ] Verify anonymity guarantees:
  - Only `devices.device_hash` stored (no PII, no reversibility)
  - No PII in `reports`, `evidence_files`, or `audit_logs`
  - `audit_logs.ip_address` only for police_user sessions, never for reporters
- [ ] Input sanitization review (SQL injection on all endpoints, XSS on dashboard)
- [ ] JWT token security (expiration, refresh, revocation for `police_users`)
- [ ] HTTPS enforcement
- [ ] Rate limiting per `devices.device_hash` to prevent spam
- [ ] Cloudinary URL security (signed URLs for `evidence_files.file_url`)
- [ ] Role-based access control validation (`police_users.role`: admin/supervisor/officer)
- [ ] Database access control review (PostGIS geometry data, JSONB fields)

#### Performance Testing

- [ ] Load testing with concurrent report submissions
- [ ] Database query performance under load
- [ ] ML inference latency benchmarking
- [ ] Mobile app performance profiling (memory, battery, network)

#### Bug Fixes

- [ ] Address all critical and high-priority bugs from testing
- [ ] UI/UX refinements based on internal review

**Deliverable:** Tested, secure, and performance-validated system.

---

### WEEK 10 (Apr 14 – Apr 27): Deployment, Field Testing & Documentation

**Goal:** Deploy to production, conduct field testing in Musanze, and finalize documentation.

#### Deployment (Apr 14–16)

- [ ] Set up production server (VPS or cloud instance)
- [ ] Configure Nginx reverse proxy with SSL/TLS
- [ ] Deploy PostgreSQL/PostGIS production database
- [ ] Deploy FastAPI backend with Gunicorn/Uvicorn workers
- [ ] Deploy React dashboard (static build via Nginx)
- [ ] Configure Celery workers and Redis for production
- [ ] Set up database backups (automated daily)
- [ ] Deploy monitoring and logging

#### Field Testing in Musanze (Apr 17–23)

- [ ] Install app on test devices
- [ ] Conduct controlled report submissions across different locations
- [ ] Verify GPS accuracy in urban and rural areas of Musanze
- [ ] Test offline mode and sync behavior
- [ ] Validate hotspot detection with real geographic data
- [ ] Gather feedback from test users (police officers, community members)
- [ ] Document field test results and observations

#### Final Documentation & Handover (Apr 24–27)

- [ ] Write API documentation (Swagger/OpenAPI auto-generated)
- [ ] Create user guide for mobile app
- [ ] Create admin guide for police dashboard
- [ ] Document ML model performance metrics and methodology
- [ ] Prepare system architecture diagrams
- [ ] Final bug fixes from field testing feedback
- [ ] Build Android APK release for distribution
- [ ] Project presentation preparation

**Deliverable:** Deployed production system, field-tested in Musanze, complete documentation.

---

## Parallel Workstream Summary

```
Week   1    2    3    4    5    6    7    8    9    10
       |----|----|----|----|----|----|----|----|----|
Backend ████████████████████░░░░░░░░░░░░░░░░░░░░░░░
ML/AI  ░░░░░░░░░░██████████░░░░░░░░░░░░░░░░░░░░░░░
Flutter░░░░░░░░░░██████████████░░░░░░░░░░░░░░░░░░░░
React  ░░░░░░░░░░░░░░░░░░░░████████████░░░░░░░░░░░░
DBSCAN ░░░░░░░░░░░░░░░░░░░░░░░░░░░░████░░░░░░░░░░░░
Integr.░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░████░░░░░░░░
Testing░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░████░░░░
Deploy ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░████
```

---

## Key Milestones

| Milestone                    | Target Date           | Criteria                                    |
| ---------------------------- | --------------------- | ------------------------------------------- |
| **M1:** Backend API Complete | Feb 23 (End Week 2)   | All CRUD endpoints functional, auth working |
| **M2:** ML Model Trained     | Mar 9 (End Week 4)    | RF model achieving ≥85% F1-score            |
| **M3:** Mobile App Ready     | Mar 16 (End Week 5)   | Full reporting flow with evidence capture   |
| **M4:** Dashboard Complete   | Mar 30 (End Week 7)   | Case management, analytics, hotspot map     |
| **M5:** System Integrated    | Apr 6 (End Week 8)    | End-to-end flow verified                    |
| **M6:** Testing Complete     | Apr 13 (End Week 9)   | All critical tests passing                  |
| **M7:** Production Deployed  | Apr 16 (Mid Week 10)  | Live system accessible                      |
| **M8:** Field Testing Done   | Apr 23 (Late Week 10) | Musanze validation complete                 |
| **M9:** Project Complete     | Apr 27 (End Week 10)  | Documentation and presentation ready        |

---

## Technology Stack Summary

| Layer               | Technology                   | Purpose                              |
| ------------------- | ---------------------------- | ------------------------------------ |
| Mobile App          | Flutter (Dart)               | Anonymous citizen reporting          |
| Dashboard           | React.js + Tailwind CSS      | Police case management & analytics   |
| Backend API         | Python + FastAPI             | RESTful services, business logic     |
| Database            | PostgreSQL + PostGIS         | Data storage, geospatial queries     |
| ML Model            | scikit-learn (Random Forest) | Report authenticity classification   |
| Clustering          | DBSCAN (scikit-learn)        | Trust-weighted hotspot detection     |
| Image Analysis      | OpenCV                       | Blur detection, quality scoring      |
| Duplicate Detection | pHash (imagehash)            | Perceptual image hashing             |
| Media Storage       | Cloudinary                   | Secure evidence file hosting         |
| Task Queue          | Celery + Redis               | Async ML inference & processing      |
| Auth                | JWT (PyJWT)                  | Stateless authentication             |
| Maps                | Leaflet.js / Mapbox          | Dashboard & safety map visualization |
| Deployment          | Nginx + Docker               | Reverse proxy, containerization      |
| Version Control     | Git + GitHub                 | Source code management               |

---

## Risk Mitigation

| Risk                             | Impact                      | Mitigation                                                                 |
| -------------------------------- | --------------------------- | -------------------------------------------------------------------------- |
| ML model underperforms           | Trust scoring unreliable    | Fallback to rule-based scoring only; retrain with augmented data           |
| PostGIS complex queries slow     | Dashboard laggy             | Pre-compute hotspots on schedule; add database indexes                     |
| Cloudinary upload failures       | Evidence lost               | Local fallback storage; retry queue in Celery                              |
| GPS inaccuracy on budget devices | Bad location data           | Accept reports with accuracy warning; wider DBSCAN eps                     |
| Tight timeline slippage          | Incomplete features         | Prioritize core flow (report → verify → dashboard); defer analytics polish |
| Field testing access issues      | Untested in real conditions | Simulate Musanze conditions locally with synthetic GPS data                |

---

## Definition of Done (Per Sprint)

- [ ] All planned features implemented and functional
- [ ] Unit tests written and passing
- [ ] Code reviewed and merged to `develop`
- [ ] No critical bugs remaining
- [ ] API endpoints documented
- [ ] Tested on target devices/browsers

---

_Schedule created: February 10, 2026_  
_Target completion: April 27, 2026 (10 weeks / 2 months 2 weeks)_
