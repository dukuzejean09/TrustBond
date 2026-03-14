// API configuration
const DEFAULT_API_BASE_URL = "https://trustbond-backend.onrender.com";

export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL
).replace(/\/$/, "");

export const formatApiLocation = () => API_BASE_URL;

export const API_ENDPOINTS = {
  auth: {
    login: `${API_BASE_URL}/api/v1/auth/login`,
    me: `${API_BASE_URL}/api/v1/auth/me`,
    changePassword: `${API_BASE_URL}/api/v1/auth/change-password`,
    forgotPassword: `${API_BASE_URL}/api/v1/auth/forgot-password`,
    resetPassword: `${API_BASE_URL}/api/v1/auth/reset-password`,
  },
  devices: {
    get: (id) => `${API_BASE_URL}/api/v1/devices/${id}`,
  },
  policeUsers: {
    list: `${API_BASE_URL}/api/v1/police-users`,
    options: `${API_BASE_URL}/api/v1/police-users/options`,
    create: `${API_BASE_URL}/api/v1/police-users`,
    update: (id) => `${API_BASE_URL}/api/v1/police-users/${id}`,
    get: (id) => `${API_BASE_URL}/api/v1/police-users/${id}`,
    delete: (id) => `${API_BASE_URL}/api/v1/police-users/${id}`,
  },
  reports: {
    list: `${API_BASE_URL}/api/v1/reports`,
    get: (id) => `${API_BASE_URL}/api/v1/reports/${id}`,
    assign: (id) => `${API_BASE_URL}/api/v1/reports/${id}/assign`,
    reviews: (id) => `${API_BASE_URL}/api/v1/reports/${id}/reviews`,
  },
  notifications: {
    list: `${API_BASE_URL}/api/v1/notifications`,
    unreadCount: `${API_BASE_URL}/api/v1/notifications/unread-count`,
    markRead: (id) => `${API_BASE_URL}/api/v1/notifications/${id}/read`,
  },
  auditLogs: {
    list: `${API_BASE_URL}/api/v1/audit-logs`,
  },
  stats: {
    dashboard: `${API_BASE_URL}/api/v1/stats/dashboard`,
  },
  hotspots: {
    list: `${API_BASE_URL}/api/v1/hotspots`,
    evidence: (id) => `${API_BASE_URL}/api/v1/hotspots/${id}/evidence`,
  },
  publicMap: {
    incidents: `${API_BASE_URL}/api/v1/public/map/incidents`,
  },
  locations: {
    list: `${API_BASE_URL}/api/v1/locations`,
  },
  incidentGroups: {
    list: `${API_BASE_URL}/api/v1/incident-groups`,
  },
  incidentTypes: {
    list: `${API_BASE_URL}/api/v1/incident-types`,
    get: (id) => `${API_BASE_URL}/api/v1/incident-types/${id}`,
    create: `${API_BASE_URL}/api/v1/incident-types`,
    update: (id) => `${API_BASE_URL}/api/v1/incident-types/${id}`,
  },
};
