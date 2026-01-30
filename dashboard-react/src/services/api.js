import axios from "axios";

const API_BASE_URL =
  process.env.REACT_APP_API_URL || "http://localhost:5000/api";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("authToken");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("authToken");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  },
);

// Auth API
export const authAPI = {
  login: (email, password) =>
    api.post("/auth/admin/login", { email, password }),
  getCurrentUser: () => api.get("/auth/me"),
  changePassword: (currentPassword, newPassword) =>
    api.post("/auth/change-password", { currentPassword, newPassword }),
};

// Dashboard API
export const dashboardAPI = {
  getStats: () => api.get("/dashboard/stats"),
  getReportsByCategory: () => api.get("/dashboard/reports-by-category"),
  getReportsByStatus: () => api.get("/dashboard/reports-by-status"),
  getReportsByDistrict: () => api.get("/dashboard/reports-by-district"),
  getReportsTrend: () => api.get("/dashboard/reports-trend"),
  getRecentReports: () => api.get("/dashboard/recent-reports"),
  getOfficerPerformance: () => api.get("/dashboard/officer-performance"),
  getActivityLogs: (params) => api.get("/analytics/activity-logs", { params }),
};

// Reports API
export const reportsAPI = {
  getReports: (params) => api.get("/reports", { params }),
  getReport: (id) => api.get(`/reports/${id}`),
  updateReport: (id, data) => api.put(`/reports/${id}`, data),
  assignReport: (reportId, officerId) =>
    api.post(`/reports/${reportId}/assign`, { officer_id: officerId }),
  getComments: (reportId) => api.get(`/reports/${reportId}/comments`),
  addComment: (reportId, data) =>
    api.post(`/reports/${reportId}/comments`, data),
};

// Users API
export const usersAPI = {
  getUsers: (params) => api.get("/users", { params }),
  getUser: (id) => api.get(`/users/${id}`),
  getOfficers: () => api.get("/users/officers"),
  createOfficer: (data) => api.post("/users/create-officer", data),
  updateUser: (id, data) => api.put(`/users/${id}`, data),
  deleteUser: (id) => api.delete(`/users/${id}`),
};

// Alerts API
export const alertsAPI = {
  getAlerts: (params) => api.get("/alerts/all", { params }),
  getAlert: (id) => api.get(`/alerts/${id}`),
  createAlert: (data) => api.post("/alerts", data),
  updateAlert: (id, data) => api.put(`/alerts/${id}`, data),
  deactivateAlert: (id) => api.post(`/alerts/${id}/cancel`),
  deleteAlert: (id) => api.delete(`/alerts/${id}`),
};

// ML & Hotspots API
export const mlAPI = {
  getHotspots: (params) => api.get("/ml/hotspots", { params }),
  getTrustScore: (reportId) => api.get(`/ml/trust-score/${reportId}`),
  verifyReport: (reportId) => api.post(`/ml/verify/${reportId}`),
};

// Analytics API
export const analyticsAPI = {
  getOverview: (days = 30) =>
    api.get("/analytics/overview", { params: { days } }),
  getTrends: (params) => api.get("/analytics/trends", { params }),
  getGeographic: (days = 30) =>
    api.get("/analytics/geographic", { params: { days } }),
  getActivityLogs: (params) => api.get("/analytics/activity-logs", { params }),
};

// Notifications API
export const notificationsAPI = {
  getNotifications: (params) => api.get("/notifications", { params }),
  markAsRead: (ids) => api.post("/notifications/mark-read", { ids }),
  getUnreadCount: () => api.get("/notifications/unread-count"),
};

export default api;
