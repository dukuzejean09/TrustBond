import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
import ErrorBoundary from "./components/ErrorBoundary.jsx";
import Login from "./pages/Login.jsx";
import ForgotPassword from "./pages/ForgotPassword.jsx";
import ResetPassword from "./pages/ResetPassword.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Reports from "./pages/Reports.jsx";
import ReportDetail from "./pages/ReportDetail.jsx";
import Users from "./pages/Users.jsx";
import Hotspots from "./pages/Hotspots.jsx";
import ChangePassword from "./pages/ChangePassword.jsx";
import AuditLog from "./pages/AuditLog.jsx";
import IncidentTypes from "./pages/IncidentTypes.jsx";
import SafetyMap from "./pages/SafetyMap.jsx";
import Stations from "./pages/Stations.jsx";
import CaseManagement from "./pages/CaseManagement.jsx";
import DeviceTrust from "./pages/DeviceTrust.jsx";
import SystemConfig from "./pages/SystemConfig.jsx";
import Notifications from "./pages/Notifications.jsx";
import "./App.css";
import "./pages/Pages.css";

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password" element={<ResetPassword />} />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/reports"
              element={
                <ProtectedRoute>
                  <Reports />
                </ProtectedRoute>
              }
            />
            <Route
              path="/reports/:id"
              element={
                <ProtectedRoute>
                  <ReportDetail />
                </ProtectedRoute>
              }
            />
            <Route
              path="/users"
              element={
                <ProtectedRoute>
                  <Users />
                </ProtectedRoute>
              }
            />
            <Route
              path="/incident-types"
              element={
                <ProtectedRoute>
                  <IncidentTypes />
                </ProtectedRoute>
              }
            />
            <Route
              path="/hotspots"
              element={
                <ProtectedRoute>
                  <Hotspots />
                </ProtectedRoute>
              }
            />
            <Route
              path="/change-password"
              element={
                <ProtectedRoute>
                  <ChangePassword />
                </ProtectedRoute>
              }
            />
            <Route
              path="/safety-map"
              element={
                <ProtectedRoute>
                  <SafetyMap />
                </ProtectedRoute>
              }
            />
            <Route
              path="/audit"
              element={
                <ProtectedRoute>
                  <AuditLog />
                </ProtectedRoute>
              }
            />
            <Route
              path="/stations"
              element={
                <ProtectedRoute>
                  <Stations />
                </ProtectedRoute>
              }
            />
            <Route
              path="/cases"
              element={
                <ProtectedRoute>
                  <CaseManagement />
                </ProtectedRoute>
              }
            />
            <Route
              path="/device-trust"
              element={
                <ProtectedRoute>
                  <DeviceTrust />
                </ProtectedRoute>
              }
            />
            <Route
              path="/system-config"
              element={
                <ProtectedRoute>
                  <SystemConfig />
                </ProtectedRoute>
              }
            />
            <Route
              path="/notifications"
              element={
                <ProtectedRoute>
                  <Notifications />
                </ProtectedRoute>
              }
            />
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
