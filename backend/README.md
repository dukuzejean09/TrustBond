# TrustBond Backend API v2.0

**Privacy-Preserving Anonymous Community Incident Reporting System for Rwanda**

Rwanda National Police (RNP) Crime Reporting System - Backend API

## Technology Stack

- **Framework**: Python Flask 3.0
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT (JSON Web Tokens)
- **Machine Learning**: scikit-learn for trust scoring
- **Geospatial**: geopy for location calculations
- **Containerization**: Docker

## Database Architecture

The system uses 33 database tables organized into domains:

### Device Management

- `devices` - Anonymous device registration
- `device_trust_history` - Trust score history

### Rwanda Administrative Geography

- `provinces` → `districts` → `sectors` → `cells` → `villages`

### Incident Management

- `incident_categories` - Crime categories
- `incident_types` - Specific incident types
- `incident_reports` - Anonymous reports
- `report_evidence` - Evidence files

### Verification Engine

- `verification_rules` - Rule definitions
- `rule_execution_logs` - Execution history

### Machine Learning

- `ml_models` - Model configurations
- `ml_predictions` - Prediction results
- `ml_training_data` - Training samples

### Hotspot Detection

- `hotspots` - Detected crime hotspots
- `hotspot_reports` - Reports in hotspots
- `hotspot_history` - Severity changes
- `clustering_runs` - DBSCAN runs

### Police Users

- `police_users` - Officer accounts
- `police_sessions` - Login sessions

### Supporting Features

- `notifications` - System notifications
- `daily_statistics` - Analytics
- `incident_type_trends` - Trend analysis
- `public_safety_zones` - Public map data
- `system_settings` - Configuration
- `activity_logs` - Audit trail
- `data_change_audits` - Change tracking
- `app_feedback` - User feedback
- `feedback_attachments` - Feedback files
- `api_keys` - API authentication
- `api_request_logs` - Request logging

## Quick Start with Docker

### Prerequisites

- Docker and Docker Compose installed

### Running the Application

1. **Start the containers:**

   ```bash
   docker-compose up -d
   ```

2. **Seed the database with default data:**

   ```bash
   docker-compose exec api python seed_complete.py
   ```

3. **Access the API:**
   - API: http://localhost:5000
   - Health check: http://localhost:5000/api/health

### Default Credentials

| Role        | Email                | Password    |
| ----------- | -------------------- | ----------- |
| Super Admin | admin@rnp.gov.rw     | password123 |
| Commander   | commander@rnp.gov.rw | password123 |
| Officer     | officer@rnp.gov.rw   | password123 |
| Analyst     | analyst@rnp.gov.rw   | password123 |

## API Endpoints Overview

### Core Endpoints

| Prefix                  | Description                        |
| ----------------------- | ---------------------------------- |
| `/api/devices`          | Device registration and management |
| `/api/geography`        | Rwanda administrative hierarchy    |
| `/api/incidents`        | Incident report submission         |
| `/api/hotspots`         | Crime hotspot detection            |
| `/api/police`           | Police user authentication         |
| `/api/verification`     | Verification rules engine          |
| `/api/ml-models`        | ML model management                |
| `/api/analytics-v2`     | Analytics and statistics           |
| `/api/notifications-v2` | Notification management            |
| `/api/audit`            | Activity logging                   |
| `/api/feedback`         | App feedback                       |
| `/api/api-management`   | API key management                 |
| `/api/public-map`       | Public safety map                  |
| `/api/settings`         | System configuration               |

### Authentication

- `POST /api/police/login` - Police user login
- `POST /api/police/logout` - User logout
- `POST /api/police/refresh` - Refresh JWT token
- `GET /api/auth/me` - Get current user
- `POST /api/auth/change-password` - Change password

### Users

- `GET /api/users` - List users (admin only)
- `GET /api/users/:id` - Get user details
- `PUT /api/users/:id` - Update user
- `DELETE /api/users/:id` - Delete user (admin only)
- `GET /api/users/officers` - List officers
- `POST /api/users/create-officer` - Create officer (admin only)

### Reports

- `GET /api/reports` - List reports
- `POST /api/reports` - Create report (authenticated)
- `POST /api/reports/anonymous` - Create anonymous report (no auth required) ⭐
- `GET /api/reports/track/:tracking_code` - Track anonymous report (no auth required) ⭐
- `GET /api/reports/:id` - Get report details
- `PUT /api/reports/:id` - Update report
- `POST /api/reports/:id/assign` - Assign report to officer
- `GET /api/reports/my-reports` - Get current user's reports

### Alerts

- `GET /api/alerts` - List active alerts (public)
- `GET /api/alerts/all` - List all alerts (admin/officer)
- `POST /api/alerts` - Create alert
- `PUT /api/alerts/:id` - Update alert
- `DELETE /api/alerts/:id` - Delete alert
- `POST /api/alerts/:id/cancel` - Cancel alert

### Dashboard

- `GET /api/dashboard/stats` - Get statistics
- `GET /api/dashboard/reports-by-category` - Reports by category
- `GET /api/dashboard/reports-by-status` - Reports by status
- `GET /api/dashboard/reports-by-district` - Reports by district
- `GET /api/dashboard/reports-trend` - Reports trend (30 days)
- `GET /api/dashboard/recent-reports` - Recent reports
- `GET /api/dashboard/officer-performance` - Officer metrics

### Mobile-Specific Endpoints ⭐ (No Auth Required)

- `GET /api/mobile/stats` - Public statistics for home screen
- `GET /api/mobile/emergency-contacts` - Emergency contact numbers
- `GET /api/mobile/nearby-reports` - Anonymous summary of nearby reports
- `GET /api/mobile/crime-categories` - Available crime categories
- `GET /api/mobile/districts` - Rwanda districts by province
- `GET /api/mobile/app-config` - App configuration
- `GET /api/mobile/report-tips` - Tips for effective reporting
- `GET /api/mobile/faqs` - Frequently asked questions

### File Uploads

- `POST /api/uploads/evidence` - Upload single evidence file
- `POST /api/uploads/evidence/multiple` - Upload multiple files
- `GET /api/uploads/evidence/:filename` - Get uploaded file
- `DELETE /api/uploads/evidence/:filename` - Delete uploaded file

## Docker Hub

### Build and Push to Docker Hub

```bash
# Build the image
docker build -t yourusername/trustbond-api:latest .

# Login to Docker Hub
docker login

# Push the image
docker push yourusername/trustbond-api:latest
```

### Pull and Run from Docker Hub

```bash
# Pull the image
docker pull yourusername/trustbond-api:latest

# Run with Docker Compose (recommended)
docker-compose up -d
```

## Local Development

### Setup

1. Create virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set environment variables:

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Run the application:
   ```bash
   python run.py
   ```

## Environment Variables

| Variable       | Description                          | Default     |
| -------------- | ------------------------------------ | ----------- |
| FLASK_APP      | Flask application entry point        | run.py      |
| FLASK_ENV      | Environment (development/production) | development |
| SECRET_KEY     | Flask secret key                     | -           |
| JWT_SECRET_KEY | JWT signing key                      | -           |
| DATABASE_URL   | PostgreSQL connection URL            | -           |

## License

MIT License - Rwanda National Police
