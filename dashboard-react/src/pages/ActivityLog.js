import React, { useState, useEffect } from "react";
import DataTable from "../components/DataTable";
import Pagination from "../components/Pagination";
import { dashboardAPI } from "../services/api";
import "../styles/ActivityLog.css";

const ActivityLog = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [actionFilter, setActionFilter] = useState("");

  useEffect(() => {
    loadLogs();
  }, [currentPage, actionFilter]);

  const loadLogs = async () => {
    try {
      setLoading(true);
      const params = { page: currentPage, per_page: 25 };
      if (actionFilter) params.action = actionFilter;

      const response = await dashboardAPI.getActivityLogs(params);
      setLogs(response.data.logs || []);
      setTotalPages(response.data.pages || 1);
    } catch (error) {
      console.error("Error loading activity logs:", error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "-";
    const date = new Date(dateStr);
    return date.toLocaleString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getActionIcon = (action) => {
    const icons = {
      login: "fa-sign-in-alt",
      logout: "fa-sign-out-alt",
      report_created: "fa-plus-circle",
      report_updated: "fa-edit",
      report_assigned: "fa-user-plus",
      report_resolved: "fa-check-circle",
      alert_created: "fa-bell",
      comment_added: "fa-comment",
      user_created: "fa-user-plus",
      user_updated: "fa-user-edit",
    };
    return icons[action] || "fa-history";
  };

  const getActionColor = (action) => {
    const colors = {
      login: "success",
      logout: "secondary",
      report_created: "primary",
      report_updated: "info",
      report_assigned: "warning",
      report_resolved: "success",
      alert_created: "danger",
      comment_added: "info",
      user_created: "primary",
      user_updated: "warning",
    };
    return colors[action] || "default";
  };

  const formatAction = (action) => {
    if (!action) return "-";
    return action
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  const columns = [
    {
      header: "Action",
      render: (row) => (
        <div className={`action-cell ${getActionColor(row.action)}`}>
          <i className={`fas ${getActionIcon(row.action)}`}></i>
          <span>{formatAction(row.action)}</span>
        </div>
      ),
    },
    {
      header: "User",
      render: (row) => (
        <div className="user-cell">
          {row.user ? (
            <>
              <span className="user-name">
                {row.user.fullName || row.user.email}
              </span>
              <span className="user-role">{row.user.role}</span>
            </>
          ) : (
            <span className="system">System</span>
          )}
        </div>
      ),
    },
    {
      header: "Details",
      render: (row) => (
        <div className="details-cell">
          {row.description ||
            (row.extraData
              ? JSON.stringify(row.extraData).substring(0, 50)
              : "-")}
        </div>
      ),
    },
    {
      header: "IP Address",
      render: (row) => (
        <code className="ip-address">{row.ipAddress || "-"}</code>
      ),
    },
    {
      header: "Timestamp",
      render: (row) => (
        <span className="timestamp">{formatDate(row.createdAt)}</span>
      ),
    },
  ];

  // Stats
  const todayLogs = logs.filter((log) => {
    const logDate = new Date(log.createdAt);
    const today = new Date();
    return logDate.toDateString() === today.toDateString();
  }).length;

  const loginCount = logs.filter((log) => log.action === "login").length;
  const reportActions = logs.filter((log) =>
    log.action?.startsWith("report_"),
  ).length;

  return (
    <div className="activity-log-page">
      <div className="page-header">
        <h1>
          <i className="fas fa-history"></i> Activity Log
        </h1>
        <div className="filters">
          <select
            value={actionFilter}
            onChange={(e) => {
              setActionFilter(e.target.value);
              setCurrentPage(1);
            }}
          >
            <option value="">All Actions</option>
            <option value="login">Login</option>
            <option value="logout">Logout</option>
            <option value="report_created">Report Created</option>
            <option value="report_updated">Report Updated</option>
            <option value="report_assigned">Report Assigned</option>
            <option value="report_resolved">Report Resolved</option>
            <option value="alert_created">Alert Created</option>
            <option value="comment_added">Comment Added</option>
          </select>
        </div>
      </div>

      {/* Stats Summary */}
      <div className="log-stats-summary">
        <div className="stat-box">
          <i className="fas fa-list"></i>
          <div>
            <span className="value">{logs.length}</span>
            <span className="label">Total Logs</span>
          </div>
        </div>
        <div className="stat-box today">
          <i className="fas fa-calendar-day"></i>
          <div>
            <span className="value">{todayLogs}</span>
            <span className="label">Today</span>
          </div>
        </div>
        <div className="stat-box logins">
          <i className="fas fa-sign-in-alt"></i>
          <div>
            <span className="value">{loginCount}</span>
            <span className="label">Logins</span>
          </div>
        </div>
        <div className="stat-box reports">
          <i className="fas fa-file-alt"></i>
          <div>
            <span className="value">{reportActions}</span>
            <span className="label">Report Actions</span>
          </div>
        </div>
      </div>

      <div className="table-card full-width">
        <div className="card-body">
          <DataTable columns={columns} data={logs} loading={loading} />
        </div>
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={setCurrentPage}
        />
      </div>
    </div>
  );
};

export default ActivityLog;
