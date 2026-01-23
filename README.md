# TrustBond - Crime Reporting System

A comprehensive crime reporting system for the **Rwanda National Police (RNP)** that enables citizens to report incidents and law enforcement to manage cases efficiently.

![RNP Colors](https://img.shields.io/badge/Theme-RNP%20Official-0D1B4C?style=flat-square)
![Flutter](https://img.shields.io/badge/Mobile-Flutter-02569B?style=flat-square&logo=flutter)
![Node.js](https://img.shields.io/badge/Backend-Node.js-339933?style=flat-square&logo=node.js)

---

## 🏗️ Project Structure

```
TrustBond/
├── mobile/          # Flutter mobile app for citizens
├── dashboard/       # Flutter web app for law enforcement
├── backend/         # Node.js/Express REST API
└── README.md
```

---

## 📱 Mobile App (Citizens)

A Flutter-based mobile application for citizens to:

- Report crimes and incidents
- Upload evidence (photos, videos, audio)
- Track report status
- Receive alerts and notifications
- Access emergency contacts

### Setup

```bash
cd mobile
flutter pub get
flutter run
```

### Features

- 🔐 Secure authentication
- 📍 GPS location capture
- 📷 Evidence upload
- 📊 Report tracking
- 🔔 Push notifications
- 🌐 Offline support
- 🔒 Anonymous reporting

---

## 💻 Dashboard (Law Enforcement)

A Flutter web application for police officers and administrators to:

- View and manage reports
- Assign cases to officers
- Track investigation progress
- Generate analytics and reports
- Manage alerts and notifications

### Setup

```bash
cd dashboard
flutter pub get
flutter run -d chrome
```

### Features

- 📊 Real-time analytics dashboard
- 📋 Case management system
- 👮 Officer assignment
- 🗺️ Geographic mapping
- 📈 Statistics and reports
- 👥 User management

---

## ⚙️ Backend API

Node.js/Express REST API with MongoDB database.

### Setup

```bash
cd backend
npm install
cp .env.example .env
# Edit .env with your configuration
npm run dev
```

### Environment Variables

| Variable         | Description                 |
| ---------------- | --------------------------- |
| `PORT`           | Server port (default: 5000) |
| `MONGODB_URI`    | MongoDB connection string   |
| `JWT_SECRET`     | Secret key for JWT tokens   |
| `JWT_EXPIRES_IN` | Token expiration time       |

### API Endpoints

#### Authentication

| Method | Endpoint                    | Description          |
| ------ | --------------------------- | -------------------- |
| POST   | `/api/auth/register`        | Register new citizen |
| POST   | `/api/auth/login`           | Citizen login        |
| POST   | `/api/auth/dashboard/login` | Officer login        |

#### Reports

| Method | Endpoint                    | Description         |
| ------ | --------------------------- | ------------------- |
| POST   | `/api/reports`              | Submit new report   |
| GET    | `/api/reports/my-reports`   | Get user's reports  |
| GET    | `/api/reports/:id`          | Get report details  |
| GET    | `/api/reports/track/:id`    | Track report status |
| POST   | `/api/reports/:id/evidence` | Upload evidence     |

#### Dashboard (Officers)

| Method | Endpoint                            | Description     |
| ------ | ----------------------------------- | --------------- |
| GET    | `/api/dashboard/stats`              | Get statistics  |
| GET    | `/api/dashboard/reports`            | Get all reports |
| PATCH  | `/api/dashboard/reports/:id/status` | Update status   |
| PATCH  | `/api/dashboard/reports/:id/assign` | Assign officer  |

#### Alerts

| Method | Endpoint      | Description          |
| ------ | ------------- | -------------------- |
| GET    | `/api/alerts` | Get active alerts    |
| POST   | `/api/alerts` | Create alert (admin) |

---

## 🎨 Brand Guidelines

### Colors

| Color        | Hex       | Usage                 |
| ------------ | --------- | --------------------- |
| Primary Navy | `#0D1B4C` | Primary brand color   |
| Accent Gold  | `#FFB800` | Accent and highlights |
| Light Navy   | `#1E3A6E` | Secondary elements    |
| Dark Navy    | `#081230` | Dark backgrounds      |

### Status Colors

| Status      | Color  | Hex       |
| ----------- | ------ | --------- |
| Pending     | Orange | `#FF9800` |
| In Progress | Blue   | `#2196F3` |
| Resolved    | Green  | `#4CAF50` |
| Rejected    | Red    | `#F44336` |

---

## 🔒 Security Features

- JWT-based authentication
- Role-based access control (RBAC)
- Rate limiting
- Input validation
- Helmet security headers
- CORS configuration
- Password hashing (bcrypt)

---

## 👥 User Roles

| Role          | Access Level                       |
| ------------- | ---------------------------------- |
| `citizen`     | Submit reports, track status       |
| `officer`     | View assigned cases, update status |
| `supervisor`  | Assign officers, manage team       |
| `admin`       | Full system access                 |
| `super_admin` | System configuration               |

---

## 📝 License

© 2024 Rwanda National Police. All rights reserved.

---

## 🤝 Support

For technical support, contact the RNP IT Department.
