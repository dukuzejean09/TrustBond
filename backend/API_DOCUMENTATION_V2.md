# TrustBond API Documentation v2.0

## Overview

TrustBond is a Privacy-Preserving Anonymous Community Incident Reporting System for Rwanda.
This document covers all available API endpoints organized by feature domain.

## Base URL

```
http://localhost:5000/api
```

## Authentication

Most admin endpoints require JWT authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

### Authentication Endpoints

| Method | Endpoint              | Description              |
| ------ | --------------------- | ------------------------ |
| POST   | `/api/police/login`   | Police user login        |
| POST   | `/api/police/logout`  | Logout current session   |
| POST   | `/api/police/refresh` | Refresh JWT token        |
| GET    | `/api/police/me`      | Get current user profile |

---

## Device Management (`/api/devices`)

Mobile device registration and trust scoring.

### Public Endpoints (Mobile App)

| Method | Endpoint                       | Description              |
| ------ | ------------------------------ | ------------------------ |
| POST   | `/devices/register`            | Register a new device    |
| POST   | `/devices/heartbeat`           | Send device heartbeat    |
| GET    | `/devices/<device_id>/profile` | Get device trust profile |

### Admin Endpoints (Authenticated)

| Method | Endpoint                       | Description             |
| ------ | ------------------------------ | ----------------------- |
| GET    | `/devices`                     | List all devices        |
| GET    | `/devices/<device_id>`         | Get device details      |
| PUT    | `/devices/<device_id>`         | Update device           |
| POST   | `/devices/<device_id>/block`   | Block a device          |
| POST   | `/devices/<device_id>/unblock` | Unblock a device        |
| GET    | `/devices/<device_id>/history` | Get trust score history |
| GET    | `/devices/stats`               | Get device statistics   |

---

## Geography (`/api/geography`)

Rwanda administrative hierarchy (Province → District → Sector → Cell → Village).

### Public Endpoints

| Method | Endpoint                    | Description                                     |
| ------ | --------------------------- | ----------------------------------------------- |
| GET    | `/geography/provinces`      | List all provinces                              |
| GET    | `/geography/provinces/<id>` | Get province details                            |
| GET    | `/geography/districts`      | List districts (optional province_id filter)    |
| GET    | `/geography/districts/<id>` | Get district details                            |
| GET    | `/geography/sectors`        | List sectors (optional district_id filter)      |
| GET    | `/geography/sectors/<id>`   | Get sector details                              |
| GET    | `/geography/cells`          | List cells (optional sector_id filter)          |
| GET    | `/geography/villages`       | List villages (optional cell_id filter)         |
| POST   | `/geography/resolve`        | Resolve coordinates to administrative hierarchy |
| POST   | `/geography/validate`       | Validate location is within Rwanda              |

### Admin Endpoints (Authenticated)

| Method | Endpoint                    | Description     |
| ------ | --------------------------- | --------------- |
| POST   | `/geography/provinces`      | Create province |
| PUT    | `/geography/provinces/<id>` | Update province |
| POST   | `/geography/districts`      | Create district |
| PUT    | `/geography/districts/<id>` | Update district |
| POST   | `/geography/sectors`        | Create sector   |
| POST   | `/geography/cells`          | Create cell     |
| POST   | `/geography/villages`       | Create village  |

---

## Incidents (`/api/incidents`)

Incident report submission and management.

### Public Endpoints (Mobile App)

| Method | Endpoint                           | Description                      |
| ------ | ---------------------------------- | -------------------------------- |
| POST   | `/incidents`                       | Submit anonymous incident report |
| GET    | `/incidents/track/<tracking_code>` | Track report status              |
| GET    | `/incidents/categories`            | Get incident categories          |
| GET    | `/incidents/types`                 | Get incident types               |
| GET    | `/incidents/types/<category_id>`   | Get types by category            |

### Admin Endpoints (Authenticated)

| Method | Endpoint                          | Description             |
| ------ | --------------------------------- | ----------------------- |
| GET    | `/incidents`                      | List all incidents      |
| GET    | `/incidents/<report_id>`          | Get incident details    |
| PUT    | `/incidents/<report_id>`          | Update incident         |
| PUT    | `/incidents/<report_id>/status`   | Update incident status  |
| PUT    | `/incidents/<report_id>/assign`   | Assign to officer       |
| POST   | `/incidents/<report_id>/verify`   | Verify incident         |
| GET    | `/incidents/<report_id>/evidence` | Get incident evidence   |
| POST   | `/incidents/<report_id>/evidence` | Add evidence            |
| GET    | `/incidents/stats`                | Get incident statistics |
| POST   | `/incidents/categories`           | Create category         |
| POST   | `/incidents/types`                | Create incident type    |

---

## Hotspots (`/api/hotspots`)

Crime hotspot detection and management using DBSCAN clustering.

### Admin Endpoints (Authenticated)

| Method | Endpoint                         | Description                     |
| ------ | -------------------------------- | ------------------------------- |
| GET    | `/hotspots`                      | List all hotspots               |
| GET    | `/hotspots/<hotspot_id>`         | Get hotspot details             |
| POST   | `/hotspots/detect`               | Run hotspot detection algorithm |
| PUT    | `/hotspots/<hotspot_id>`         | Update hotspot                  |
| PUT    | `/hotspots/<hotspot_id>/status`  | Update hotspot status           |
| POST   | `/hotspots/<hotspot_id>/assign`  | Assign officer to hotspot       |
| GET    | `/hotspots/<hotspot_id>/reports` | Get reports in hotspot          |
| GET    | `/hotspots/<hotspot_id>/history` | Get hotspot history             |
| GET    | `/hotspots/clustering-runs`      | List clustering runs            |
| GET    | `/hotspots/stats`                | Get hotspot statistics          |

---

## Public Safety Map (`/api/public-map`)

Public-facing anonymized safety data.

### Public Endpoints (No Auth Required)

| Method | Endpoint                      | Description             |
| ------ | ----------------------------- | ----------------------- |
| GET    | `/public-map/data`            | Get anonymized map data |
| GET    | `/public-map/zones`           | Get public safety zones |
| GET    | `/public-map/zones/<zone_id>` | Get specific zone       |

### Admin Endpoints (Authenticated)

| Method | Endpoint                            | Description                 |
| ------ | ----------------------------------- | --------------------------- |
| GET    | `/public-map/admin/zones`           | List all zones (admin view) |
| POST   | `/public-map/admin/zones`           | Create safety zone          |
| PUT    | `/public-map/admin/zones/<zone_id>` | Update safety zone          |
| DELETE | `/public-map/admin/zones/<zone_id>` | Delete safety zone          |
| POST   | `/public-map/admin/sync`            | Sync zones from hotspots    |

---

## Police Users (`/api/police`)

Police user authentication and management.

### Public Endpoints

| Method | Endpoint         | Description |
| ------ | ---------------- | ----------- |
| POST   | `/police/login`  | User login  |
| POST   | `/police/logout` | User logout |

### Authenticated Endpoints

| Method | Endpoint                  | Description         |
| ------ | ------------------------- | ------------------- |
| GET    | `/police/me`              | Get current user    |
| PUT    | `/police/me`              | Update current user |
| POST   | `/police/change-password` | Change password     |
| POST   | `/police/refresh`         | Refresh token       |
| GET    | `/police/sessions`        | Get user sessions   |

### Admin Endpoints (Manage Users Permission)

| Method | Endpoint                              | Description         |
| ------ | ------------------------------------- | ------------------- |
| GET    | `/police/users`                       | List all users      |
| GET    | `/police/users/<user_id>`             | Get user details    |
| POST   | `/police/users`                       | Create new user     |
| PUT    | `/police/users/<user_id>`             | Update user         |
| DELETE | `/police/users/<user_id>`             | Deactivate user     |
| PUT    | `/police/users/<user_id>/permissions` | Update permissions  |
| GET    | `/police/users/stats`                 | Get user statistics |

---

## Verification Rules (`/api/verification`)

Rule-based verification engine management.

### Admin Endpoints (Authenticated)

| Method | Endpoint                               | Description                 |
| ------ | -------------------------------------- | --------------------------- |
| GET    | `/verification/rules`                  | List all rules              |
| GET    | `/verification/rules/<rule_id>`        | Get rule details            |
| POST   | `/verification/rules`                  | Create rule                 |
| PUT    | `/verification/rules/<rule_id>`        | Update rule                 |
| DELETE | `/verification/rules/<rule_id>`        | Delete rule                 |
| PUT    | `/verification/rules/<rule_id>/toggle` | Enable/disable rule         |
| PUT    | `/verification/rules/reorder`          | Reorder rules               |
| POST   | `/verification/execute`                | Execute rules on report     |
| GET    | `/verification/logs`                   | Get execution logs          |
| GET    | `/verification/stats`                  | Get verification statistics |

---

## ML Models (`/api/ml-models`)

Machine learning model management.

### Admin Endpoints (Authenticated)

| Method | Endpoint                            | Description          |
| ------ | ----------------------------------- | -------------------- |
| GET    | `/ml-models`                        | List all models      |
| GET    | `/ml-models/<model_id>`             | Get model details    |
| POST   | `/ml-models`                        | Create model         |
| PUT    | `/ml-models/<model_id>`             | Update model         |
| DELETE | `/ml-models/<model_id>`             | Delete model         |
| PUT    | `/ml-models/<model_id>/activate`    | Set as active model  |
| POST   | `/ml-models/<model_id>/score`       | Generate trust score |
| GET    | `/ml-models/<model_id>/predictions` | Get predictions      |
| GET    | `/ml-models/training-data`          | Get training data    |
| POST   | `/ml-models/training-data`          | Add training data    |

---

## Analytics (`/api/analytics-v2`)

Comprehensive analytics and statistics.

### Authenticated Endpoints

| Method | Endpoint                                | Description             |
| ------ | --------------------------------------- | ----------------------- |
| GET    | `/analytics-v2/dashboard`               | Get dashboard stats     |
| GET    | `/analytics-v2/overview`                | Get quick overview      |
| GET    | `/analytics-v2/time-series/incidents`   | Incident time series    |
| GET    | `/analytics-v2/geographic/distribution` | Geographic distribution |
| GET    | `/analytics-v2/geographic/heatmap`      | Heatmap data            |
| GET    | `/analytics-v2/trends`                  | Incident trends         |
| GET    | `/analytics-v2/trends/categories`       | Category trends         |
| GET    | `/analytics-v2/compare/districts`       | Compare districts       |
| GET    | `/analytics-v2/compare/periods`         | Compare time periods    |
| GET    | `/analytics-v2/verification`            | Verification stats      |
| GET    | `/analytics-v2/devices`                 | Device stats            |
| GET    | `/analytics-v2/hotspots`                | Hotspot stats           |
| GET    | `/analytics-v2/response-time`           | Response time stats     |
| GET    | `/analytics-v2/daily`                   | Daily statistics        |
| POST   | `/analytics-v2/daily/generate`          | Generate daily stats    |
| POST   | `/analytics-v2/export`                  | Export analytics        |

---

## Notifications (`/api/notifications-v2`)

Notification management.

### Authenticated Endpoints (User's Own)

| Method | Endpoint                          | Description           |
| ------ | --------------------------------- | --------------------- |
| GET    | `/notifications-v2`               | Get my notifications  |
| GET    | `/notifications-v2/unread-count`  | Get unread count      |
| GET    | `/notifications-v2/<id>`          | Get notification      |
| PUT    | `/notifications-v2/<id>/read`     | Mark as read          |
| PUT    | `/notifications-v2/read-all`      | Mark all as read      |
| PUT    | `/notifications-v2/read-multiple` | Mark multiple as read |
| DELETE | `/notifications-v2/<id>`          | Delete notification   |

### Admin Endpoints (Send Notifications Permission)

| Method | Endpoint                          | Description               |
| ------ | --------------------------------- | ------------------------- |
| POST   | `/notifications-v2/send`          | Send notification         |
| POST   | `/notifications-v2/broadcast`     | Broadcast to users        |
| GET    | `/notifications-v2/admin/all`     | List all notifications    |
| GET    | `/notifications-v2/admin/stats`   | Get stats                 |
| POST   | `/notifications-v2/admin/cleanup` | Cleanup old notifications |

---

## Audit (`/api/audit`)

Activity logging and audit trail.

### Authenticated Endpoints (View Audit Logs Permission)

| Method | Endpoint                                 | Description          |
| ------ | ---------------------------------------- | -------------------- |
| GET    | `/audit/activities`                      | Get activity logs    |
| GET    | `/audit/activities/<log_id>`             | Get log details      |
| GET    | `/audit/activities/user/<user_id>`       | User's activities    |
| GET    | `/audit/activities/resource/<type>/<id>` | Resource activities  |
| GET    | `/audit/data-changes`                    | Get data change logs |
| GET    | `/audit/data-changes/<change_id>`        | Get change details   |
| GET    | `/audit/stats`                           | Get audit statistics |
| POST   | `/audit/cleanup`                         | Cleanup old logs     |

---

## Feedback (`/api/feedback`)

App feedback management.

### Public Endpoints (Mobile App)

| Method | Endpoint                        | Description           |
| ------ | ------------------------------- | --------------------- |
| POST   | `/feedback`                     | Submit feedback       |
| GET    | `/feedback/track/<feedback_id>` | Track feedback status |

### Admin Endpoints (Authenticated)

| Method | Endpoint                         | Description             |
| ------ | -------------------------------- | ----------------------- |
| GET    | `/feedback`                      | List all feedback       |
| GET    | `/feedback/<feedback_id>`        | Get feedback details    |
| PUT    | `/feedback/<feedback_id>`        | Update feedback         |
| PUT    | `/feedback/<feedback_id>/status` | Update status           |
| DELETE | `/feedback/<feedback_id>`        | Delete feedback         |
| GET    | `/feedback/stats`                | Get feedback statistics |

---

## API Management (`/api/api-management`)

API key and rate limiting management.

### Admin Endpoints (Manage API Permission)

| Method | Endpoint                                   | Description        |
| ------ | ------------------------------------------ | ------------------ |
| GET    | `/api-management/keys`                     | List API keys      |
| GET    | `/api-management/keys/<key_id>`            | Get key details    |
| POST   | `/api-management/keys`                     | Create API key     |
| PUT    | `/api-management/keys/<key_id>`            | Update key         |
| DELETE | `/api-management/keys/<key_id>`            | Revoke key         |
| POST   | `/api-management/keys/<key_id>/regenerate` | Regenerate key     |
| GET    | `/api-management/requests`                 | Get request logs   |
| GET    | `/api-management/requests/key/<key_id>`    | Key's request logs |
| GET    | `/api-management/stats`                    | Get API statistics |
| POST   | `/api-management/validate`                 | Validate API key   |

---

## Settings (`/api/settings`)

System configuration management.

### Authenticated Endpoints

| Method | Endpoint                  | Description            |
| ------ | ------------------------- | ---------------------- |
| GET    | `/settings`               | Get all settings       |
| GET    | `/settings/categories`    | Get setting categories |
| GET    | `/settings/<setting_key>` | Get setting value      |

### Admin Endpoints (Manage Settings Permission)

| Method | Endpoint                  | Description              |
| ------ | ------------------------- | ------------------------ |
| PUT    | `/settings/<setting_key>` | Update setting           |
| PUT    | `/settings`               | Update multiple settings |
| POST   | `/settings`               | Create setting           |
| DELETE | `/settings/<setting_key>` | Delete setting           |
| POST   | `/settings/initialize`    | Initialize defaults      |

---

## Response Formats

### Success Response

```json
{
  "message": "Operation successful",
  "data": { ... }
}
```

### Error Response

```json
{
  "error": "Error description",
  "code": "error_code"
}
```

### Paginated Response

```json
{
  "items": [ ... ],
  "total": 100,
  "page": 1,
  "per_page": 20,
  "pages": 5
}
```

---

## Status Codes

| Code | Description           |
| ---- | --------------------- |
| 200  | Success               |
| 201  | Created               |
| 400  | Bad Request           |
| 401  | Unauthorized          |
| 403  | Forbidden             |
| 404  | Not Found             |
| 500  | Internal Server Error |

---

## Rate Limiting

API requests are rate-limited based on the API key or IP address:

- Mobile app: 100 requests/minute
- Admin dashboard: 200 requests/minute

---

## Contact

For API support, contact: api-support@rnp.gov.rw
