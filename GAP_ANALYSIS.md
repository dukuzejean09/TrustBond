# TrustBond – Gap Analysis: Proposal vs. Implementation

> **Date:** March 12, 2026  
> **Branch:** main  
> **Purpose:** Documents what is fully implemented, what is partially implemented, and what is completely missing compared to the research proposal.

---

## 1. Fully Implemented ✅

| Proposal Feature                                                                                                        | Where Implemented                                                                                        |
| ----------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| Anonymous reporting via pseudonymous device IDs (SHA-256 hash)                                                          | `TrustBond/lib/services/device_service.dart`                                                             |
| Multi-step report submission (incident type → location+description → evidence)                                          | `TrustBond/lib/screens/report_step1_screen.dart`, `report_step2_screen.dart`, `report_step3_screen.dart` |
| Auto GPS capture with accuracy reading                                                                                  | `TrustBond/lib/services/location_service.dart`                                                           |
| Motion/accelerometer sampling at submission (motion_level, movement_speed, was_stationary)                              | `TrustBond/lib/services/motion_service.dart`                                                             |
| Network type capture (WiFi / Mobile / None)                                                                             | `TrustBond/lib/services/device_status_service.dart` → `reports.network_type`                             |
| Battery level capture                                                                                                   | `TrustBond/lib/services/device_status_service.dart` → `reports.battery_level`                            |
| Context tags on reports (Night-time, Weapons involved, etc.)                                                            | `report_step2_screen.dart` + `reports.context_tags` (JSONB)                                              |
| Musanze district boundary enforcement (out-of-scope reports rejected with HTTP 400)                                     | `backend/app/api/v1/reports.py` + `backend/app/core/village_lookup.py`                                   |
| Village/Cell/Sector lookup from GPS coordinates using PostGIS                                                           | `backend/app/core/village_lookup.py`                                                                     |
| Rule-based verification pipeline (description length, screenshot/screen-recording detection, high-severity flag)        | `backend/app/core/report_rules.py`                                                                       |
| EXIF GPS metadata extraction and capture time parsing from uploaded images                                              | `backend/app/api/v1/reports.py` (`_extract_exif_metadata`)                                               |
| GPS anomaly flag (speed > 200 km/h or accuracy > 200 m)                                                                 | `backend/app/core/credibility_model.py`                                                                  |
| Future timestamp flag                                                                                                   | `backend/app/core/credibility_model.py`                                                                  |
| ML credibility scoring with XGBoost pipeline                                                                            | `backend/app/core/credibility_model.py` + `backend/musanze/TrustBond.joblib`                             |
| ML predictions persisted to `ml_predictions` table                                                                      | `backend/app/models/ml_prediction.py`                                                                    |
| Device registration (anonymous, hash-based)                                                                             | `backend/app/api/v1/devices.py`                                                                          |
| Device trust score (stored, used in ML feature pipeline)                                                                | `backend/app/models/device.py` → `device_trust_score`                                                    |
| Device ban flag (`is_banned` column)                                                                                    | `backend/app/models/device.py`                                                                           |
| Hotspot auto-creation triggered after each report submission                                                            | `backend/app/core/hotspot_auto.py` (background task)                                                     |
| Trust-weighted hotspot scoring (rule_status + police review + ML trust_score blend)                                     | `backend/app/core/hotspot_auto.py` (`_weight_for_report`)                                                |
| Hotspot risk levels: low / medium / high                                                                                | `backend/app/core/hotspot_auto.py` (`_risk_level_from_score`)                                            |
| Case management (create, update, link reports, assign officer, CASE-YYYY-NNNN numbering)                                | `backend/app/api/v1/cases.py`                                                                            |
| Police user roles: admin, supervisor, officer                                                                           | `backend/app/models/police_user.py`                                                                      |
| Police report review (confirm / reject decision)                                                                        | `backend/app/models/police_review.py`                                                                    |
| Report assignment to police officers                                                                                    | `backend/app/models/report_assignment.py`                                                                |
| Notifications system                                                                                                    | `backend/app/api/v1/notifications.py`                                                                    |
| Audit logging of all key actions                                                                                        | `backend/app/core/audit.py`                                                                              |
| Dashboard statistics endpoint                                                                                           | `backend/app/api/v1/stats.py`                                                                            |
| Public safety map with Musanze boundaries and location hierarchy                                                        | `TrustBond/lib/screens/safety_map_screen.dart`                                                           |
| Evidence upload to Cloudinary                                                                                           | `backend/app/api/v1/reports.py`                                                                          |
| `EvidenceFile` schema with `perceptual_hash`, `blur_score`, `tamper_score`, `ai_quality_label` columns (DB schema only) | `backend/app/models/evidence_file.py`                                                                    |
| Report number auto-generation (RPT-YYYY-NNNN)                                                                           | `backend/app/api/v1/reports.py`                                                                          |
| React + Vite police dashboard (frontend scaffolded)                                                                     | `frontend/src/`                                                                                          |

---

## 2. Partially Implemented ⚠️

These features exist in the proposal, have partial code or DB columns, but the logic is incomplete or does not match the specification.

### 2.1 Hotspot Detection Algorithm – Grouping used instead of DBSCAN

**Proposal says:** Trust-weighted DBSCAN with configurable `eps_radius`, `min_samples`, `time_window`, and output `cluster_id` / `cluster_density` per Table 3.3.

**What exists:**  
`hotspot_auto.py` groups reports by `village_location_id + incident_type_id` (or rounded lat/long bucket) and counts them against a fixed `min_incidents` threshold. This is a **simple frequency grouping**, not DBSCAN.

**What is missing:**

- `sklearn.cluster.DBSCAN` (or equivalent) is never called
- `eps_radius` and `min_samples` are named constants but not passed to any clustering algorithm
- `cluster_id`, `cluster_density` (Table 3.3) are never computed or stored
- No support for 7 / 30 / 90-day configurable `time_window` filters
- `Hotspot` model has no `cluster_id` or `cluster_density` columns

---

### 2.2 Perceptual Hashing / Duplicate Detection – Schema only, no logic

**Proposal says (Table 3.4):**  
`perceptual_hash` (64-bit image fingerprint), `hash_similarity_score` (Hamming distance 0–64), and `is_duplicate_media` Boolean flag (Table 3.1) for detecting duplicate or recycled evidence images.

**What exists:**  
`evidence_files.perceptual_hash` (String 128) and `is_live_capture` columns exist in the DB.

**What is missing:**

- No `imagehash` library in `requirements.txt`
- `perceptual_hash` is **never computed** during evidence upload
- No Hamming distance comparison against existing hashes
- `hash_similarity_score` does not exist anywhere
- `is_duplicate_media` is referenced in `credibility_model.py` feature mapping but always resolves to `None`
- `ai_checked_at` is never set

---

### 2.3 Image Quality / Blur Scoring – Schema only, no logic

**Proposal says (Tables 3.1 & 3.4):**  
`image_quality_score` (0.0–1.0), `image_blur_score` (Laplacian variance), `image_brightness` (mean pixel value), and `ai_quality_label` (good / poor / suspicious).

**What exists:**  
`evidence_files.blur_score`, `tamper_score`, and `ai_quality_label` columns exist in the DB schema.

**What is missing:**

- No Laplacian variance (blur) calculation using OpenCV or PIL
- No mean pixel brightness computation
- `blur_score` is **never set** during upload
- `image_quality_score` (Table 3.1) feature fed to ML always resolves to `None`
- `ai_quality_label` is never set; `ai_checked_at` is never populated

---

### 2.4 Device Trust Score – Initial value only, never recalculated

**Proposal says (Table 3.2):**  
A transparent rule-based formula driven by `confirmation_rate`, `rejected_reports`, `spam_flag_count`, `reporting_frequency`, `unique_locations_count`, and `last_activity_days`.

**What exists:**  
`device_trust_score` starts at 50.00 (default). It is read for ML features and displayed in the dashboard.

**What is missing:**

- **No update logic** runs after a police review decision (confirm / reject)
- `reporting_frequency`, `unique_locations_count`, `last_activity_days`, and `avg_response_time` (Table 3.2) are not stored on the `Device` model
- No endpoint or background job recalculates `device_trust_score` based on outcomes
- Devices cannot accumulate earned trust or lose it dynamically

---

### 2.5 ML Explainability – Placeholder

**Proposal says:** "Explainable machine learning" (Abstract, Section 1.3).

**What exists:**  
`ml_predictions.explanation` column (JSONB) exists. `score_report_credibility()` sets it to `None` with a code comment: _"placeholder; can be filled with SHAP/feature attributions later"_.

**What is missing:**

- `shap` library is not in `requirements.txt`
- No SHAP / feature-importance values are computed or stored
- Police dashboard has no explainability UI

---

### 2.6 Banned Device Enforcement – Flag exists, not enforced

**Proposal says:** Device reliability maintained with transparent rule-based trust; implicitly, banned devices should be blocked.

**What exists:**  
`Device.is_banned` (Boolean, default False) is stored and shown in the dashboard.

**What is missing:**

- `backend/app/api/v1/reports.py` does **not** check `device.is_banned` before accepting a report
- A banned device can still register new reports without restriction

---

### 2.7 Public Safety Map – No Hotspot Markers Shown

**Proposal says (Objective 4):** "Trust-aware hotspot detection and visualization … present actionable insights through … a privacy-safe public safety map."

**What exists:**  
`safety_map_screen.dart` renders Musanze sector/cell/village boundaries and the user's GPS pin. A `public_hotspots` API endpoint exists (`backend/app/api/v1/public_hotspots.py`).

**What is missing:**

- `safety_map_screen.dart` **never calls** the `public_hotspots` endpoint
- No hotspot circles or markers are rendered on the citizen map
- Citizens see boundaries only—no safety intelligence is surfaced

---

### 2.8 `time_since_incident` – Not Captured

**Proposal says (Table 3.1):** `time_since_incident` (hours between incident occurrence and submission).

**What exists:**  
Only `reported_at` (submission time) is stored.

**What is missing:**

- No "when did the incident happen?" date/time input in the report form
- `incident_occurred_at` column does not exist on `Report`
- `time_since_incident` feature always resolves to `None` in the ML pipeline

---

### 2.9 `image_metadata_valid` – Extracted but not stored as Boolean

**Proposal says (Table 3.1):** `image_metadata_valid` (EXIF metadata consistency, Boolean).

**What exists:**  
EXIF GPS is extracted and `media_latitude` / `media_longitude` are saved on `EvidenceFile`. A comparison between EXIF GPS and submitted GPS is possible.

**What is missing:**

- No `image_metadata_valid` column on `EvidenceFile`
- No explicit Boolean stored indicating whether EXIF GPS matched submitted GPS
- `metadata_gps_match` (Table 3.4) is never saved

---

### 2.10 `gps_location_type` – Derivable from existing data but not computed

**Proposal says (Table 3.1):** A categorical feature (Indoor / Outdoor / Unknown) indicating whether the GPS signal was acquired indoors or outdoors.

**What exists:**  
The system already captures `gps_accuracy` (metres) from the device GPS fix via `TrustBond/lib/services/location_service.dart` and stores it in `reports.gps_accuracy`. GPS accuracy directly reflects signal quality: outdoor fixes typically yield < 20 m accuracy while indoor or obstructed fixes produce > 50–100 m accuracy. The device's physical GPS coordinates (latitude, longitude) are equally captured and passed to PostGIS for village-level reverse geocoding.

**What is missing:**

- No backend rule converts `gps_accuracy` into a `gps_location_type` label (Outdoor / Indoor / Unknown)
- `gps_location_type` is not stored as an explicit column on `Report`
- The ML feature pipeline always passes `None` for this field, even though the source data (`gps_accuracy`) is present
- Suggested derivation rule (to be applied on the backend at report creation):
  - `gps_accuracy < 25 m` → `Outdoor`
  - `25 m ≤ gps_accuracy < 100 m` → `Unknown`
  - `gps_accuracy ≥ 100 m` → `Indoor`

---

## 3. Completely Missing ❌

These features appear in the proposal but have **zero implementation** anywhere in the codebase.

### 3.1 Text Sentiment Analysis & Keyword Flagging (Table 3.4)

**Proposal:** `text_sentiment_score` (−1.0 to 1.0) and `keyword_flag_count` (suspicious keyword count) from report descriptions.

**Status:** No NLP library (TextBlob, VADER, NLTK) is present in `requirements.txt`. No sentiment scoring or keyword pattern matching runs at any point in the pipeline. These features always pass as `None` to the ML model.

---

### 3.2 Device Table Variables: `avg_response_time`, `reporting_frequency`, `unique_locations_count`, `last_activity_days` (Table 3.2)

**Proposal:** These four metrics form part of the rule-based device trust formula.

**Status:** None of these columns exist on the `Device` model. They are never calculated or stored. The trust formula described in the proposal cannot be executed.

---

### 3.3 `priority_level` per Report (Table 3.5)

**Proposal:** ML output `priority_level` (High / Medium / Low) assigned to each report.

**Status:** `MLPrediction` stores `trust_score` and `prediction_label` (likely_real / suspicious / fake). There is no `priority_level` output or field on reports. Priority exists only on `Case`, not on individual reports.

---

### 3.4 `hotspot_risk_level` as ML/Cluster Output (Table 3.5)

**Proposal:** `hotspot_risk_level` (Critical / Warning / Normal) as a model prediction output.

**Status:** `Hotspot.risk_level` uses low / medium / high labels derived from a hand-crafted score threshold — not a model prediction. The label set (Critical / Warning / Normal) does not match the implementation (low / medium / high). No ML model produces this field.

---

### 3.5 `final_trust_score` Combined Score (Table 3.5)

**Proposal:** A final combined report trust score (0–100) blending rule-based and ML scores.

**Status:** `MLPrediction.trust_score` is the raw ML probability × 100. There is no combined formula that blends the rule-based `rule_status`, the ML `trust_score`, and the device trust into a single unified `final_trust_score` per report.

---

## 4. Model Inconsistency

| Topic                | Proposal Says                                             | Code Does                                                       |
| -------------------- | --------------------------------------------------------- | --------------------------------------------------------------- |
| Classifier algorithm | Random Forest (mentioned throughout Abstract, Ch.1, Ch.3) | XGBoost (`XGBClassifier`) — `train_report_credibility_model.py` |
| Hotspot algorithm    | Trust-weighted DBSCAN                                     | Simple frequency grouping by village + incident type            |
| Risk level labels    | Critical / Warning / Normal (Table 3.5)                   | low / medium / high (Hotspot model)                             |
| Priority labels      | High / Medium / Low (Table 3.5)                           | High / Medium / Low (Cases only, not reports)                   |

---

## 5. Priority Recommendations

The following items should be addressed to align the system with the proposal:

| Priority    | Gap                                                                                                                    | Effort             |
| ----------- | ---------------------------------------------------------------------------------------------------------------------- | ------------------ |
| 🔴 Critical | Implement DBSCAN hotspot clustering (replaces current grouping)                                                        | High               |
| 🔴 Critical | Enforce `is_banned` check at report submission                                                                         | Low                |
| 🔴 Critical | Recalculate `device_trust_score` after police review decisions                                                         | Medium             |
| 🟠 High     | Compute perceptual hash + Hamming duplicate detection on evidence upload                                               | Medium             |
| 🟠 High     | Compute image blur score (Laplacian variance) on evidence upload                                                       | Medium             |
| 🟠 High     | Show hotspot markers on the public safety map in the Flutter app                                                       | Medium             |
| 🟠 High     | Add "incident occurred at" field to report form + DB                                                                   | Low                |
| 🟡 Medium   | Implement text sentiment analysis + keyword flagging                                                                   | Medium             |
| 🟡 Medium   | Integrate SHAP for ML explainability                                                                                   | Medium             |
| 🟡 Medium   | Add missing device metrics: `avg_response_time`, `reporting_frequency`, `unique_locations_count`, `last_activity_days` | Medium             |
| 🟡 Medium   | Compute and store `final_trust_score` per report                                                                       | Low                |
| 🟢 Low      | Add `priority_level` output field to reports (separate from cases)                                                     | Low                |
| 🟢 Low      | Align risk level labels (Critical/Warning/Normal vs low/medium/high)                                                   | Low                |
| 🟢 Low      | Store `image_metadata_valid` / `metadata_gps_match` Boolean on EvidenceFile                                            | Low                |
| 🟢 Low      | Derive and store `gps_location_type` from already-captured `gps_accuracy` on the backend                               | Low                |
| 🟢 Low      | Align proposal language (Random Forest) with actual model (XGBoost)                                                    | Documentation only |
