import React, { useState, useEffect } from "react";
import DataTable from "../components/DataTable";
import Pagination from "../components/Pagination";
import Modal from "../components/Modal";
import { alertsAPI } from "../services/api";
import "../styles/Alerts.css";

const Alerts = () => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [viewModalOpen, setViewModalOpen] = useState(false);

  const [newAlert, setNewAlert] = useState({
    title: "",
    description: "",
    alertType: "community_warning",
    severity: "medium",
    district: "",
    sector: "",
    expiresAt: "",
  });

  useEffect(() => {
    loadAlerts();
  }, [currentPage]);

  const loadAlerts = async () => {
    try {
      setLoading(true);
      const response = await alertsAPI.getAlerts({
        page: currentPage,
        per_page: 20,
      });
      setAlerts(response.data.alerts || []);
      setTotalPages(response.data.pages || 1);
    } catch (error) {
      console.error("Error loading alerts:", error);
    } finally {
      setLoading(false);
    }
  };

  const createAlert = async () => {
    try {
      await alertsAPI.createAlert(newAlert);
      setCreateModalOpen(false);
      setNewAlert({
        title: "",
        description: "",
        alertType: "community_warning",
        severity: "medium",
        district: "",
        sector: "",
        expiresAt: "",
      });
      loadAlerts();
    } catch (error) {
      console.error("Error creating alert:", error);
    }
  };

  const deactivateAlert = async (alertId) => {
    if (!window.confirm("Are you sure you want to deactivate this alert?"))
      return;
    try {
      await alertsAPI.deactivateAlert(alertId);
      loadAlerts();
    } catch (error) {
      console.error("Error deactivating alert:", error);
    }
  };

  const viewAlert = async (alert) => {
    try {
      const response = await alertsAPI.getAlert(alert.id);
      setSelectedAlert(response.data.alert);
      setViewModalOpen(true);
    } catch (error) {
      console.error("Error loading alert:", error);
    }
  };

  const formatAlertType = (type) => {
    const types = {
      community_warning: "Community Warning",
      crime_spike: "Crime Spike",
      missing_person: "Missing Person",
      wanted_suspect: "Wanted Suspect",
      emergency: "Emergency",
      public_advisory: "Public Advisory",
    };
    return types[type] || type;
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "-";
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const isExpired = (expiresAt) => {
    if (!expiresAt) return false;
    return new Date(expiresAt) < new Date();
  };

  const columns = [
    {
      header: "Alert",
      render: (row) => (
        <div className="alert-cell">
          <span className={`severity-indicator ${row.severity}`}></span>
          <strong>{row.title}</strong>
        </div>
      ),
    },
    {
      header: "Type",
      render: (row) => (
        <span className={`badge-type ${row.alertType}`}>
          {formatAlertType(row.alertType)}
        </span>
      ),
    },
    {
      header: "Severity",
      render: (row) => (
        <span className={`badge-severity ${row.severity}`}>{row.severity}</span>
      ),
    },
    {
      header: "District",
      accessor: "district",
      render: (row) => row.district || "All",
    },
    {
      header: "Status",
      render: (row) => (
        <span
          className={`badge-status ${row.isActive && !isExpired(row.expiresAt) ? "active" : "inactive"}`}
        >
          {row.isActive && !isExpired(row.expiresAt) ? "Active" : "Inactive"}
        </span>
      ),
    },
    { header: "Created", render: (row) => formatDate(row.createdAt) },
    {
      header: "Expires",
      render: (row) => (row.expiresAt ? formatDate(row.expiresAt) : "Never"),
    },
    {
      header: "Actions",
      render: (row) => (
        <div className="action-buttons">
          <button
            className="action-btn view"
            onClick={(e) => {
              e.stopPropagation();
              viewAlert(row);
            }}
          >
            <i className="fas fa-eye"></i>
          </button>
          {row.isActive && (
            <button
              className="action-btn delete"
              onClick={(e) => {
                e.stopPropagation();
                deactivateAlert(row.id);
              }}
            >
              <i className="fas fa-times-circle"></i>
            </button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="alerts-page">
      <div className="page-header">
        <h1>Alerts Management</h1>
        <button
          className="btn btn-primary"
          onClick={() => setCreateModalOpen(true)}
        >
          <i className="fas fa-plus"></i> Create Alert
        </button>
      </div>

      <div className="table-card full-width">
        <div className="card-body">
          <DataTable
            columns={columns}
            data={alerts}
            loading={loading}
            onRowClick={viewAlert}
          />
        </div>
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={setCurrentPage}
        />
      </div>

      {/* Create Alert Modal */}
      <Modal
        isOpen={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        title="Create New Alert"
        size="large"
      >
        <div className="form-grid">
          <div className="form-group">
            <label>Title *</label>
            <input
              type="text"
              value={newAlert.title}
              onChange={(e) =>
                setNewAlert({ ...newAlert, title: e.target.value })
              }
              placeholder="Alert title"
            />
          </div>
          <div className="form-group">
            <label>Alert Type *</label>
            <select
              value={newAlert.alertType}
              onChange={(e) =>
                setNewAlert({ ...newAlert, alertType: e.target.value })
              }
            >
              <option value="community_warning">Community Warning</option>
              <option value="crime_spike">Crime Spike</option>
              <option value="missing_person">Missing Person</option>
              <option value="wanted_suspect">Wanted Suspect</option>
              <option value="emergency">Emergency</option>
              <option value="public_advisory">Public Advisory</option>
            </select>
          </div>
          <div className="form-group">
            <label>Severity *</label>
            <select
              value={newAlert.severity}
              onChange={(e) =>
                setNewAlert({ ...newAlert, severity: e.target.value })
              }
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>
          <div className="form-group">
            <label>District</label>
            <input
              type="text"
              value={newAlert.district}
              onChange={(e) =>
                setNewAlert({ ...newAlert, district: e.target.value })
              }
              placeholder="e.g., Gasabo"
            />
          </div>
          <div className="form-group">
            <label>Sector</label>
            <input
              type="text"
              value={newAlert.sector}
              onChange={(e) =>
                setNewAlert({ ...newAlert, sector: e.target.value })
              }
              placeholder="e.g., Kacyiru"
            />
          </div>
          <div className="form-group">
            <label>Expires At</label>
            <input
              type="datetime-local"
              value={newAlert.expiresAt}
              onChange={(e) =>
                setNewAlert({ ...newAlert, expiresAt: e.target.value })
              }
            />
          </div>
          <div className="form-group full-width">
            <label>Description *</label>
            <textarea
              rows={4}
              value={newAlert.description}
              onChange={(e) =>
                setNewAlert({ ...newAlert, description: e.target.value })
              }
              placeholder="Detailed alert description..."
            />
          </div>
        </div>
        <div className="form-actions">
          <button
            className="btn btn-secondary"
            onClick={() => setCreateModalOpen(false)}
          >
            Cancel
          </button>
          <button className="btn btn-primary" onClick={createAlert}>
            Create Alert
          </button>
        </div>
      </Modal>

      {/* View Alert Modal */}
      <Modal
        isOpen={viewModalOpen}
        onClose={() => setViewModalOpen(false)}
        title="Alert Details"
        size="medium"
      >
        {selectedAlert && (
          <div className="alert-detail">
            <div className="alert-header">
              <h2>{selectedAlert.title}</h2>
              <div className="badges">
                <span className={`badge-severity ${selectedAlert.severity}`}>
                  {selectedAlert.severity}
                </span>
                <span className={`badge-type ${selectedAlert.alertType}`}>
                  {formatAlertType(selectedAlert.alertType)}
                </span>
              </div>
            </div>
            <p className="alert-description">{selectedAlert.description}</p>
            <div className="alert-meta">
              <div>
                <strong>District:</strong> {selectedAlert.district || "All"}
              </div>
              <div>
                <strong>Sector:</strong> {selectedAlert.sector || "All"}
              </div>
              <div>
                <strong>Created:</strong> {formatDate(selectedAlert.createdAt)}
              </div>
              <div>
                <strong>Expires:</strong>{" "}
                {selectedAlert.expiresAt
                  ? formatDate(selectedAlert.expiresAt)
                  : "Never"}
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default Alerts;
