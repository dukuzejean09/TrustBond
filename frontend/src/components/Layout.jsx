import { useState, useEffect, useRef, useMemo } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext.jsx";
import { apiService } from "../services/apiService.js";
import "./Layout.css";

const PAGE_TITLES = {
  "/dashboard": "Dashboard",
  "/reports": "Reports",
  "/safety-map": "Safety Map",
  "/users": "Users",
  "/incident-types": "Incident Types",
  "/hotspots": "Hotspots",
  "/audit": "Audit Log",
  "/change-password": "Change Password",
  "/notifications": "Notifications",
};

export default function Layout({ children }) {
  const {
    user,
    logout,
    isAdmin,
    canManageUsers,
    canSeeHotspots,
    canSeeAudit,
    isOfficer,
  } = useAuth();
  const canManageIncidentTypes = isAdmin;
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [darkMode, setDarkMode] = useState(true);
  const [notifOpen, setNotifOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const notifRef = useRef(null);

  // Determine page title
  const pageTitle = useMemo(() => {
    if (location.pathname.startsWith("/reports/")) return "Report Detail";
    for (const [path, title] of Object.entries(PAGE_TITLES)) {
      if (
        location.pathname === path ||
        location.pathname.startsWith(path + "/")
      )
        return title;
    }
    return "Dashboard";
  }, [location.pathname]);

  // Light/dark mode
  useEffect(() => {
    document.body.classList.toggle("light-mode", !darkMode);
  }, [darkMode]);

  // Notifications
  useEffect(() => {
    apiService
      .getUnreadNotificationCount()
      .then((r) => setUnreadCount(r.unread_count ?? 0))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (notifOpen) {
      apiService
        .getNotifications({ limit: 20 })
        .then((list) => setNotifications(Array.isArray(list) ? list : []))
        .catch(() => setNotifications([]));
    }
  }, [notifOpen]);

  useEffect(() => {
    function handleClickOutside(e) {
      if (notifRef.current && !notifRef.current.contains(e.target))
        setNotifOpen(false);
    }
    if (notifOpen) document.addEventListener("click", handleClickOutside);
    return () => document.removeEventListener("click", handleClickOutside);
  }, [notifOpen]);

  // Close sidebar on route change (mobile)
  useEffect(() => {
    setSidebarOpen(false);
  }, [location.pathname]);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };
  const handleMarkRead = async (id) => {
    try {
      await apiService.markNotificationRead(id);
      setUnreadCount((c) => Math.max(0, c - 1));
      setNotifications((prev) =>
        prev.map((n) =>
          n.notification_id === id ? { ...n, is_read: true } : n,
        ),
      );
    } catch (_) {}
  };

  const fmtDate = (s) => (s ? new Date(s).toLocaleString() : "");
  const today = new Date().toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
  const initials = user
    ? `${(user.first_name || "")[0] || ""}${(user.last_name || "")[0] || ""}`.toUpperCase()
    : "U";

  const isActive = (path) =>
    path === "/reports"
      ? location.pathname === "/reports"
      : location.pathname === path || location.pathname.startsWith(path + "/");

  return (
    <div className="layout">
      {/* Sidebar */}
      <aside className={`sidebar${sidebarOpen ? " open" : ""}`}>
        <div className="sidebar-logo">
          <div className="logo-icon">
            <img src="/logo.jpeg" alt="TrustBond" />
          </div>
          <div>
            <div className="logo-text">TrustBond</div>
            <div className="logo-sub">Police Portal</div>
          </div>
        </div>

        <div className="sidebar-scroll">
          {/* Overview */}
          <div className="nav-section">
            <div className="nav-label">Overview</div>
            <Link
              to="/dashboard"
              className={`nav-item${isActive("/dashboard") ? " active" : ""}`}
            >
              <span className="nav-dot" />{" "}
              <span className="nav-text">Dashboard</span>
            </Link>
          </div>

          {/* Operations */}
          <div className="nav-section">
            <div className="nav-label">Operations</div>
            <Link
              to="/reports"
              className={`nav-item${isActive("/reports") || location.pathname.startsWith("/reports/") ? " active" : ""}`}
            >
              <span className="nav-dot" />{" "}
              <span className="nav-text">
                {isOfficer ? "My Assignments" : "Reports"}
              </span>
              {unreadCount > 0 && (
                <span className="nav-badge">
                  {unreadCount > 99 ? "99+" : unreadCount}
                </span>
              )}
            </Link>
            <Link
              to="/safety-map"
              className={`nav-item${isActive("/safety-map") ? " active" : ""}`}
            >
              <span className="nav-dot" />{" "}
              <span className="nav-text">Safety Map</span>
            </Link>
            {canSeeHotspots && (
              <Link
                to="/hotspots"
                className={`nav-item${isActive("/hotspots") ? " active" : ""}`}
              >
                <span className="nav-dot" />{" "}
                <span className="nav-text">Hotspots</span>
              </Link>
            )}
          </div>

          {/* Management */}
          {(canManageUsers || canManageIncidentTypes || canSeeAudit) && (
            <div className="nav-section">
              <div className="nav-label">Management</div>
              {canManageUsers && (
                <Link
                  to="/users"
                  className={`nav-item${isActive("/users") ? " active" : ""}`}
                >
                  <span className="nav-dot" />{" "}
                  <span className="nav-text">Users</span>
                </Link>
              )}
              {canManageIncidentTypes && (
                <Link
                  to="/incident-types"
                  className={`nav-item${isActive("/incident-types") ? " active" : ""}`}
                >
                  <span className="nav-dot" />{" "}
                  <span className="nav-text">Incident Types</span>
                </Link>
              )}
              {canSeeAudit && (
                <Link
                  to="/audit"
                  className={`nav-item${isActive("/audit") ? " active" : ""}`}
                >
                  <span className="nav-dot" />{" "}
                  <span className="nav-text">Audit Log</span>
                </Link>
              )}
            </div>
          )}

          {/* Account */}
          <div className="nav-section">
            <div className="nav-label">Account</div>
            <Link
              to="/change-password"
              className={`nav-item${isActive("/change-password") ? " active" : ""}`}
            >
              <span className="nav-dot" />{" "}
              <span className="nav-text">Change Password</span>
            </Link>
          </div>
        </div>

        <div className="sidebar-footer">
          <div className="user-card">
            <div className="avatar">{initials}</div>
            <div style={{ overflow: "hidden" }}>
              <div className="user-name">
                {user?.first_name} {user?.last_name}
              </div>
              <div className="user-role-label">{user?.role}</div>
            </div>
          </div>
        </div>
      </aside>

      {/* Mobile overlay */}
      <div
        className={`sb-overlay${sidebarOpen ? " open" : ""}`}
        onClick={() => setSidebarOpen(false)}
      />

      {/* Main area */}
      <div className="main-area">
        <header className="topbar">
          <button
            className="hamburger"
            onClick={() => setSidebarOpen((o) => !o)}
          >
            &#9776;
          </button>
          <div className="page-title">{pageTitle}</div>
          <div className="tb-actions" ref={notifRef}>
            <button
              className="mode-toggle"
              onClick={() => setDarkMode((d) => !d)}
            >
              {darkMode ? "☀ Light" : "🌙 Dark"}
            </button>
            <div className="tb-chip">{today}</div>
            <button
              className="notif-btn"
              onClick={() => setNotifOpen((o) => !o)}
            >
              🔔{" "}
              {unreadCount > 0 && (
                <span className="notif-count">
                  {unreadCount > 99 ? "99+" : unreadCount}
                </span>
              )}
              {unreadCount > 0 && <span className="notif-dot" />}
            </button>
            {notifOpen && (
              <div className="notif-dropdown">
                <div className="notif-dd-header">Notifications</div>
                {notifications.length === 0 ? (
                  <div className="notif-dd-empty">No notifications</div>
                ) : (
                  <ul className="notif-dd-list">
                    {notifications.map((n) => (
                      <li
                        key={n.notification_id}
                        className={`notif-dd-item${n.is_read ? " read" : ""}`}
                        onClick={() => {
                          if (!n.is_read) handleMarkRead(n.notification_id);
                          if (
                            n.related_entity_type === "report" &&
                            n.related_entity_id
                          ) {
                            navigate(`/reports/${n.related_entity_id}`);
                            setNotifOpen(false);
                          }
                        }}
                      >
                        <div className="notif-dd-title">{n.title}</div>
                        {n.message && (
                          <div className="notif-dd-msg">{n.message}</div>
                        )}
                        <div className="notif-dd-date">
                          {fmtDate(n.created_at)}
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
            <button className="logout-btn" onClick={handleLogout}>
              Logout
            </button>
          </div>
        </header>

        <div className="content">{children}</div>
      </div>
    </div>
  );
}
