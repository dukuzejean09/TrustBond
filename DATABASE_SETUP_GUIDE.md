# TrustBond Complete Database Setup Guide

## Overview

This document explains how to implement the complete TrustBond database schema with all 33 tables as specified in the database design documentation.

## Database Structure Summary

**Total Tables: 33**

### Section 1: Core Device Management (2 tables)

- `devices` - Anonymous device profiles
- `device_trust_history` - Trust score history tracking

### Section 2: Rwanda Administrative Geography (5 tables)

- `provinces` - Top-level regions
- `districts` - Primary geographic unit
- `sectors` - District subdivisions
- `cells` - Sector subdivisions
- `villages` - Fine-grained locations

### Section 3: Police User Management (2 tables)

- `police_users` - Police officer accounts
- `police_sessions` - Active login sessions

### Section 4: Incident Taxonomy (2 tables)

- `incident_categories` - Main categories (Theft, Vandalism, etc.)
- `incident_types` - Specific incident types

### Section 5: Machine Learning System (3 tables)

- `ml_models` - Model registry and versioning
- `ml_predictions` - Prediction logs
- `ml_training_data` - Labeled training dataset

### Section 6: Hotspot Detection (4 tables)

- `clustering_runs` - DBSCAN execution logs
- `hotspots` - Detected crime clusters
- `hotspot_reports` - Bridge: reports to hotspots
- `hotspot_history` - Hotspot trend tracking

### Section 7: Incident Reports (Main Transaction) (2 tables)

- `incident_reports` - Core report table
- `report_evidence` - Evidence files (photos, video, audio)

### Section 8: Verification Rules Engine (2 tables)

- `verification_rules` - Configurable validation rules
- `rule_execution_logs` - Rule execution results

### Section 9: Notifications (1 table)

- `notifications` - Police alerts and notifications

### Section 10: Analytics (2 tables)

- `daily_statistics` - Aggregated daily metrics
- `incident_type_trends` - Weekly trend analysis

### Section 11: Public Safety Map (1 table)

- `public_safety_zones` - Anonymized public data

### Section 12: System Configuration (1 table)

- `system_settings` - Application configuration

### Section 13: Audit & Activity (2 tables)

- `activity_logs` - User action audit trail
- `data_change_audit` - Data change tracking

### Section 14: User Feedback (2 tables)

- `app_feedback` - Anonymous app feedback
- `feedback_attachments` - Screenshot attachments

### Section 15: API Management (2 tables)

- `api_keys` - API authentication
- `api_request_logs` - API request tracking

## Setup Instructions

### Option 1: Using the Complete SQL Schema (Recommended)

1. **Load the complete schema file:**

   ```bash
   psql -U your_user -d trustbond < trustbond_complete_schema.sql
   ```

2. **Verify the schema was created:**
   ```bash
   psql -U your_user -d trustbond -c "\dt"
   ```
   This should list all 33 tables.

### Option 2: Using Flask-SQLAlchemy (For Development)

The Python SQLAlchemy models are already created:

1. **Initialize the database:**

   ```bash
   cd backend
   flask db init  # If migrations folder doesn't exist
   flask db migrate -m "Create complete TrustBond schema"
   flask db upgrade
   ```

2. **Verify models import correctly:**
   ```bash
   python -c "from app.models import *; print('Models loaded successfully')"
   ```

### Option 3: Running in Docker

1. **Build and start the database:**

   ```bash
   docker-compose up -d postgres
   ```

2. **Load the schema:**
   ```bash
   docker exec -i trustbond_postgres psql -U trustbond_user -d trustbond < trustbond_complete_schema.sql
   ```

## Key Features

### 1. Privacy & Anonymity

- No PII stored for reporters (only device fingerprint hash)
- Anonymous reports linked to devices, never to individuals
- Encrypted push tokens for notifications

### 2. Hybrid Verification Pipeline

```
Report Submitted → Rule Validation → ML Scoring → Police Review → Resolution
```

### 3. Geographic Hierarchy

```
Province → District → Sector → Cell → Village
```

### 4. Trust Scoring System

- Device trust scores (0-100)
- ML confidence scores
- Police verification as ground truth
- Historical tracking via device_trust_history

### 5. Hotspot Detection

- Trust-weighted DBSCAN clustering
- Real-time hotspot tracking
- Risk assessment and prioritization
- Trend analysis via hotspot_history

### 6. Machine Learning Pipeline

- Multiple model versions (champion model pattern)
- Prediction logging for model monitoring
- Training data management
- Feature vector storage for explainability

### 7. Complete Audit Trail

- All user actions logged (activity_logs)
- All data changes tracked (data_change_audit)
- API request logging
- Timestamp on all modifications

## Important Relationships

### Many-to-Many Relationships

- **Reports ↔ Hotspots:** Via `hotspot_reports` bridge table
- Each report can belong to multiple hotspots
- Trust weighting used for clustering priority

### Foreign Key Constraints

All foreign keys are properly configured with:

- ON DELETE CASCADE for dependent tables
- Index creation for performance
- Constraint checking enabled

## Initial Data to Seed

1. **Rwanda Geographic Data**
   - 5 provinces with boundaries (GeoJSON)
   - 30 districts with centroids
   - All sectors, cells, villages

2. **Incident Categories & Types**
   - Core crime categories (Theft, Vandalism, Assault, etc.)
   - Specific types within each category
   - Severity levels and priority mappings

3. **System Settings**
   - ML model thresholds
   - Rule engine parameters
   - Hotspot detection parameters
   - Notification preferences

4. **Default Police User**
   - Super admin account for initial setup
   - Full system access

## Performance Optimization

### Indexes Created

- District ID (for geographic filtering)
- Device ID (for device lookup)
- Report status (for workflow querying)
- Timestamps (for date range queries)
- Trust classification (for report filtering)
- Hotspot status (for dashboard views)

### Query Patterns Optimized

```sql
-- Fast device lookup
SELECT * FROM devices WHERE device_fingerprint = '...';

-- Report filtering by status
SELECT * FROM incident_reports WHERE report_status = 'pending_review' AND reported_at > NOW() - INTERVAL 7 DAY;

-- Hotspot analysis by district
SELECT * FROM hotspots WHERE district_id = ? AND status = 'active' ORDER BY priority_score DESC;

-- Daily statistics aggregation
SELECT * FROM daily_statistics WHERE stat_date = CURRENT_DATE AND district_id = ?;
```

## Migration Strategy

For existing installations:

1. **Backup current database:**

   ```bash
   pg_dump -U user -d trustbond > backup.sql
   ```

2. **Create new database with complete schema:**

   ```bash
   psql -U user -c "CREATE DATABASE trustbond_new;"
   psql -U user -d trustbond_new < trustbond_complete_schema.sql
   ```

3. **Migrate data from old schema:**

   ```bash
   -- Create mapping for old users to new police_users
   -- Create mapping for old reports to new incident_reports
   -- Validate data integrity
   ```

4. **Switch to new database:**
   ```bash
   # Update connection string in app config
   # Test thoroughly in staging
   # Switch production DNS
   ```

## Troubleshooting

### Missing FK Constraint

If you get "foreign key constraint failed" error:

- Verify parent tables exist before child tables
- Check all FK references are correct
- Ensure GeoJSON valid format for geography

### Duplicate Key Errors

If loading data fails with duplicate key errors:

- Check for duplicate values in UNIQUE fields
- Verify device_fingerprint, rule_code, api_key_prefix uniqueness

### UUID Issues

If UUID generation fails:

- Ensure `uuid-ossp` extension is installed
- Check default value: `default=lambda: str(uuid.uuid4())`

## SQL Verification Queries

```sql
-- Count all tables
SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';
-- Expected: 33

-- List all tables
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;

-- Check foreign key constraints
SELECT constraint_name, table_name, column_name
FROM information_schema.key_column_usage
WHERE constraint_name LIKE 'fk_%'
ORDER BY table_name;

-- Check all indexes
SELECT tablename, indexname FROM pg_indexes WHERE schemaname = 'public' ORDER BY tablename;
```

## Next Steps

1. **Load Rwanda geographic data** - Populate provinces, districts, sectors, cells, villages
2. **Create incident taxonomy** - Categories and types based on Rwanda police classification
3. **Configure system settings** - ML thresholds, rule parameters, notification preferences
4. **Create admin user** - Initial police user for dashboard access
5. **Deploy ML models** - Load trained models into ml_models table
6. **Setup API keys** - Create API authentication for integrations
7. **Configure rules** - Define verification rules for rule engine

## Files Reference

- **trustbond_complete_schema.sql** - Complete SQL schema (33 tables)
- **app/models/device.py** - Device and trust history models
- **app/models/geography.py** - Rwanda geographic hierarchy models
- **app/models/incident_taxonomy.py** - Category and type models
- **app/models/incident_report.py** - Main report table
- **app/models/evidence.py** - Evidence file models
- **app/models/verification_rules.py** - Rule engine models
- **app/models/ml_models.py** - ML system models
- **app/models/hotspots.py** - Hotspot detection models
- **app/models/police_users.py** - Police user and session models
- **app/models/notifications.py** - Notification models
- **app/models/analytics.py** - Analytics models
- **app/models/public_map.py** - Public safety map models
- **app/models/system_settings.py** - Configuration models
- **app/models/audit.py** - Audit logging models
- **app/models/feedback.py** - Feedback models
- **app/models/api_management.py** - API key models

## Support

For database schema questions or issues:

1. Check the complete specification document
2. Review SQL comments in trustbond_complete_schema.sql
3. Examine model definitions in app/models/
4. Test with provided verification queries
