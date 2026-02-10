import React, { useState, useEffect, useRef } from "react";
import { Outlet, NavLink, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { notificationsAPI } from "../services/api";
import Toast from "./Toast";
import "../styles/Layout.css";

const Layout = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [toast, setToast] = useState(null);
  const userMenuRef = useRef(null);
  const notificationRef = useRef(null);

  useEffect(() => {
    loadNotifications();
    // Close dropdowns on outside click
    const handleClickOutside = (event) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target)) {
        setUserMenuOpen(false);
      }
      if (
        notificationRef.current &&
        !notificationRef.current.contains(event.target)
      ) {
        setNotificationsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const loadNotifications = async () => {
    try {
      const response = await notificationsAPI.getNotifications({ limit: 5 });
      setNotifications(response.data.notifications || []);
      setUnreadCount(response.data.unreadCount || 0);
    } catch (error) {
      console.error("Error loading notifications:", error);
    }
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const showToast = (message, type = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const navItems = [
    { path: "/dashboard", icon: "fa-chart-line", label: "Dashboard" },
    { path: "/reports", icon: "fa-file-alt", label: "Reports" },
    { path: "/alerts", icon: "fa-bell", label: "Alerts" },
    { path: "/hotspots", icon: "fa-map-marked-alt", label: "Crime Hotspots" },
    { path: "/analytics", icon: "fa-chart-bar", label: "Analytics" },
    { path: "/officers", icon: "fa-users", label: "Officers" },
    { path: "/users", icon: "fa-user-group", label: "Citizens" },
    { path: "/activity", icon: "fa-history", label: "Activity Log" },
    { path: "/settings", icon: "fa-cog", label: "Settings" },
  ];

  const formatRole = (role) => {
    const roles = {
      super_admin: "Super Admin",
      admin: "Administrator",
      officer: "Police Officer",
      citizen: "Citizen",
    };
    return roles[role] || role;
  };

  const getPageTitle = () => {
    const path = location.pathname;
    const item = navItems.find((nav) => nav.path === path);
    return item ? item.label : "Dashboard";
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className={`sidebar ${sidebarCollapsed ? "collapsed" : ""}`}>
        <div className="sidebar-header">
          <div className="logo">
            <div className="logo-icon">
              <i className="fas fa-shield-halved"></i>
            </div>
            {!sidebarCollapsed && (
              <div className="logo-text">
                <span className="trust">Trust</span>
                <span className="bond">Bond</span>
                <small>Rwanda National Police</small>
              </div>
            )}
          </div>
        </div>

        <nav className="sidebar-nav">
          <ul>
            {navItems.map((item) => (
              <li key={item.path} className="nav-item">
                <NavLink
                  to={item.path}
                  className={({ isActive }) => (isActive ? "active" : "")}
                >
                  <i className={`fas ${item.icon}`}></i>
                  {!sidebarCollapsed && <span>{item.label}</span>}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        <div className="sidebar-footer">
          <button className="logout-btn" onClick={handleLogout}>
            <i className="fas fa-sign-out-alt"></i>
            {!sidebarCollapsed && <span>Logout</span>}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className={`main-content ${sidebarCollapsed ? "expanded" : ""}`}>
        {/* Top Bar */}
        <header className="topbar">
          <button
            className="menu-toggle"
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          >
            <i className="fas fa-bars"></i>
          </button>

          <h1 className="page-title">{getPageTitle()}</h1>

          <div className="topbar-right">
            <div className="search-box">
              <i className="fas fa-search"></i>
              <input type="text" placeholder="Search reports, users..." />
            </div>

            <div className="notifications" ref={notificationRef}>
              <button
                className="notification-btn"
                onClick={() => setNotificationsOpen(!notificationsOpen)}
              >
                <i className="fas fa-bell"></i>
                {unreadCount > 0 && (
                  <span className="badge">{unreadCount}</span>
                )}
              </button>
              {notificationsOpen && (
                <div className="notification-dropdown">
                  <div className="notification-header">
                    <h4>Notifications</h4>
                    <button onClick={() => {}}>Mark all read</button>
                  </div>
                  <div className="notification-items">
                    {notifications.length === 0 ? (
                      <div className="empty-notifications">
                        No notifications
                      </div>
                    ) : (
                      notifications.map((notif, index) => (
                        <div
                          key={index}
                          className={`notification-item ${notif.read ? "" : "unread"}`}
                        >
                          <i className="fas fa-info-circle"></i>
                          <div className="notification-content">
                            <p>{notif.message}</p>
                            <small>{notif.createdAt}</small>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>

            <div
              className="user-profile"
              ref={userMenuRef}
              onClick={() => setUserMenuOpen(!userMenuOpen)}
            >
              <div className="avatar">
                <i className="fas fa-user"></i>
              </div>
              <div className="user-info">
                <span className="user-name">
                  {user?.firstName || "Admin"} {user?.lastName || ""}
                </span>
                <span className="user-role">{formatRole(user?.role)}</span>
              </div>
              <i className="fas fa-chevron-down"></i>

              {userMenuOpen && (
                <div className="user-dropdown show">
                  <a href="#profile">
                    <i className="fas fa-user"></i> Profile
                  </a>
                  <NavLink to="/settings">
                    <i className="fas fa-cog"></i> Settings
                  </NavLink>
                  <hr />
                  <button onClick={handleLogout}>
                    <i className="fas fa-sign-out-alt"></i> Logout
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Page Content */}
        <div className="page-content">
          <Outlet context={{ showToast }} />
        </div>
      </main>

      {/* Toast Notification */}
      {toast && <Toast message={toast.message} type={toast.type} />}
    </div>
  );
};

export default Layout;
