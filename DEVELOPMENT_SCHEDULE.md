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

- [ ] Initialize Git repository with branching strategy (`main`, `develop`, `feature/*`)
- [ ] Set up Python virtual environment, install FastAPI, Uvicorn, SQLAlchemy, Alembic
- [ ] Design and implement PostgreSQL database schema with PostGIS extension
  - `devices` table (pseudonymous device tracking via SHA-256 hash)
  - `reports` table (incident data, GPS, timestamps, evidence references)
  - `device_trust` table (trust score history, confirmation rates)
  - `clusters` / `hotspots` table (DBSCAN results)
  - `officers` / `admin` tables (dashboard users)
  - `cases` table (unified case management)
  - `activity_log` table (audit trail)
  - `alerts` table (notifications)
- [ ] Write Alembic migration scripts
- [ ] Set up Docker Compose for local PostgreSQL + PostGIS
- [ ] Configure Cloudinary account and test media upload/retrieval
- [ ] Set up project folder structure for backend:
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

- [ ] Implement JWT-based authentication for police officers/admin
- [ ] Implement pseudonymous device registration endpoint (SHA-256 device hash generation)
- [ ] Build Report Submission API:
  - `POST /api/reports` — accept incident data + GPS + timestamp + evidence files
  - `GET /api/reports` — list/filter reports (for dashboard)
  - `GET /api/reports/{id}` — single report detail
  - `PATCH /api/reports/{id}/status` — update case status
- [ ] Build Device Trust API:
  - `GET /api/devices/{hash}/trust` — retrieve device trust score
  - Internal trust score update logic
- [ ] Build Officer/Admin API:
  - `POST /api/auth/login` — officer login
  - `GET /api/officers` — list officers
  - CRUD for officer management
- [ ] Implement Cloudinary upload service (image/video evidence)
- [ ] Write input validation with Pydantic schemas for all endpoints
- [ ] Set up CORS middleware and rate limiting
- [ ] Write unit tests for core endpoints

**Deliverable:** Fully functional REST API with auth, report CRUD, device tracking, and media upload.

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
- [ ] Device trust formula (transparent rule-based):
  ```
  trust_score = (
      base_score
      + (confirmation_rate × w1)
      - (rejection_rate × w2)
      - (spam_flags × w3)
      + (reporting_consistency × w4)
  )
  ```

#### ML Data Preparation

- [ ] Generate synthetic training dataset based on variable tables (Tables 3.1–3.5)
- [ ] Define feature engineering pipeline:
  - Extract report-level features (description_length, evidence_count, image_quality, etc.)
  - Extract device-level features (total_reports, confirmation_rate, etc.)
  - Extract temporal features (time_since_incident, reporting_frequency)
- [ ] Label synthetic data: Verified / Rejected / Pending
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
  - Incident type selector (Theft, Vandalism, Suspicious Activity, etc.)
  - Description text field
  - Automatic GPS capture with accuracy display
  - Automatic timestamp capture
- [ ] Set up API service layer connecting to FastAPI backend

#### Week 4 — Evidence & Offline Support

- [ ] Implement camera integration for photo/video evidence capture
- [ ] Implement gallery picker for existing media
- [ ] Build evidence preview and multi-file attachment UI
- [ ] Implement offline report queue (store locally, sync when connected)
- [ ] Build report history screen (user's own submissions, anonymized)
- [ ] Add network status indicator and connectivity handling
- [ ] Implement local notifications for submission confirmation

**Deliverable:** Functional Flutter app capable of anonymous incident reporting with evidence.

---

### WEEK 4 (Mar 2 – Mar 9): Random Forest Model & AI-Assisted Verification

**Goal:** Train the ML model and implement AI verification checks.

#### Random Forest Classifier

- [ ] Train Random Forest model using scikit-learn:
  - Input features from Tables 3.1 & 3.2
  - Target: `authenticity_label` (Verified / Rejected / Pending)
  - Hyperparameter tuning via GridSearchCV
- [ ] Evaluate model performance:
  - Precision, Recall, F1-score per class
  - Confusion matrix analysis
  - Feature importance ranking
- [ ] Export trained model (joblib/pickle) for API integration
- [ ] Build prediction endpoint: `POST /api/ml/predict-authenticity`
- [ ] Implement authenticity score output (probability 0.0–1.0)

#### AI-Assisted Verification (OpenCV + lightweight checks)

- [ ] Image quality assessment:
  - Blur detection (Laplacian variance)
  - Brightness/contrast check (mean pixel value)
  - Resolution validation
- [ ] Image quality score calculation (0.0–1.0)
- [ ] Integrate perceptual hashing for duplicate image detection
- [ ] GPS anomaly detection (speed-based, geographic bounds)
- [ ] Timestamp anomaly detection (statistical outlier detection)

#### Integration

- [ ] Wire verification pipeline: Rule-based → AI checks → RF prediction → Final score
- [ ] Implement background task processing with Celery + Redis for ML inference
- [ ] Store verification results alongside reports in database

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
  - Total reports stat card
  - Reports by status (Verified / Pending / Rejected)
  - Reports by category chart
  - Recent reports table
  - Trust score distribution

**Deliverable:** Production-ready mobile app; dashboard with auth and home page.

---

### WEEK 6 (Mar 17 – Mar 23): React Dashboard — Case Management & Reports

**Goal:** Build core case management and report viewing features.

- [ ] Build Reports page:
  - Filterable data table (by status, category, date range, trust score)
  - Report detail modal with evidence viewer (images/video from Cloudinary)
  - Verification details display (rule-based results, ML score, AI checks)
  - Status update actions (Verify, Reject, Escalate)
- [ ] Build Cases / Unified Case Management page:
  - Group related reports into cases
  - Case timeline view
  - Evidence aggregation across linked reports
  - Case assignment to officers
- [ ] Build Officers management page:
  - Add/edit/deactivate officers
  - Role-based access control
- [ ] Build Activity Log page:
  - Audit trail of all actions
  - Filterable by officer, action type, date
- [ ] Build Alerts page:
  - System notifications (new high-priority reports, anomalies)
  - Alert configuration settings

**Deliverable:** Fully functional case management and report review interface.

---

### WEEK 7 (Mar 24 – Mar 30): Hotspot Detection & Analytics Dashboard

**Goal:** Implement DBSCAN clustering and analytics visualization.

#### Trust-Weighted DBSCAN

- [ ] Implement trust-weighted DBSCAN algorithm:
  - Weight each data point by `trust_weight` (derived from `final_trust_score`)
  - Configurable `eps_radius` (50–500m) and `min_samples` (3–10)
  - Time window filtering (7, 30, 90 days)
  - Category-based filtering
- [ ] Build hotspot API endpoints:
  - `GET /api/hotspots` — retrieve current clusters
  - `GET /api/hotspots/map-data` — GeoJSON for map rendering
  - `POST /api/hotspots/recalculate` — trigger reclustering
- [ ] Assign `hotspot_risk_level` (Critical / Warning / Normal) based on cluster density and trust weights
- [ ] Schedule periodic recalculation (Celery beat task)

#### Analytics & Visualization (Dashboard)

- [ ] Build Hotspots page:
  - Interactive map (Leaflet.js or Mapbox) with cluster visualization
  - Heatmap overlay toggle
  - Click-to-drill-down into cluster details
  - Time range selector
- [ ] Build Analytics page:
  - Incident trends over time (line charts)
  - Category distribution (pie/bar charts)
  - Trust score distribution histogram
  - Geographic distribution analysis
  - Device trust trends
  - Report verification rate over time
- [ ] Build Settings page:
  - DBSCAN parameter configuration
  - Alert thresholds
  - System configuration

**Deliverable:** Working hotspot detection with map visualization, comprehensive analytics dashboard.

---

### WEEK 8 (Mar 31 – Apr 6): End-to-End Integration & Community Safety Map

**Goal:** Connect all components and build the public safety map.

- [ ] End-to-end flow testing:
  1. Submit report from Flutter app →
  2. Backend receives and stores →
  3. Rule-based verification runs →
  4. AI checks execute (image quality, GPS anomaly, duplicate) →
  5. Random Forest predicts authenticity →
  6. Device trust score updates →
  7. Report appears in dashboard with scores →
  8. Officer reviews and updates status →
  9. DBSCAN recalculates hotspots →
  10. Safety map updates
- [ ] Build Community Safety Map (public-facing):
  - Anonymized cluster display (no individual report locations)
  - Risk level color coding
  - Category filtering
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
  - No PII stored or logged
  - Device hash is non-reversible
  - No IP address logging
- [ ] Input sanitization review (SQL injection, XSS)
- [ ] JWT token security (expiration, refresh, revocation)
- [ ] HTTPS enforcement
- [ ] Rate limiting validation
- [ ] Cloudinary URL security (signed URLs)
- [ ] Database access control review

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
