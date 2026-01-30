import React, { useState, useEffect } from "react";
import DataTable from "../components/DataTable";
import Pagination from "../components/Pagination";
import Modal from "../components/Modal";
import { reportsAPI, dashboardAPI, mlAPI } from "../services/api";
import "../styles/Reports.css";

const Reports = () => {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [statusFilter, setStatusFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [selectedReport, setSelectedReport] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [trustScore, setTrustScore] = useState(null);
  const [officers, setOfficers] = useState([]);
  const [assignModalOpen, setAssignModalOpen] = useState(false);
  const [selectedOfficer, setSelectedOfficer] = useState("");

  useEffect(() => {
    loadReports();
    loadOfficers();
  }, [currentPage, statusFilter, categoryFilter]);

  const loadReports = async () => {
    try {
      setLoading(true);
      const response = await reportsAPI.getReports({
        page: currentPage,
        per_page: 20,
        status: statusFilter || undefined,
        category: categoryFilter || undefined,
      });
      setReports(response.data.reports || []);
      setTotalPages(response.data.pages || 1);
    } catch (error) {
      console.error("Error loading reports:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadOfficers = async () => {
    try {
      const response = await dashboardAPI.getOfficerPerformance();
      setOfficers(response.data.data || []);
    } catch (error) {
      console.error("Error loading officers:", error);
    }
  };

  const viewReport = async (report) => {
    try {
      const response = await reportsAPI.getReport(report.id);
      setSelectedReport(response.data.report);

      // Load trust score
      try {
        const trustRes = await mlAPI.getTrustScore(report.id);
        setTrustScore(trustRes.data.trustScore);
      } catch (e) {
        setTrustScore(null);
      }

      setModalOpen(true);
    } catch (error) {
      console.error("Error loading report:", error);
    }
  };

  const updateReportStatus = async (status) => {
    try {
      await reportsAPI.updateReport(selectedReport.id, { status });
      setSelectedReport({ ...selectedReport, status });
      loadReports();
    } catch (error) {
      console.error("Error updating status:", error);
    }
  };

  const assignOfficer = async () => {
    if (!selectedOfficer) return;
    try {
      await reportsAPI.assignReport(selectedReport.id, selectedOfficer);
      setAssignModalOpen(false);
      setSelectedOfficer("");
      loadReports();
    } catch (error) {
      console.error("Error assigning officer:", error);
    }
  };

  const formatCategory = (category) => {
    if (!category) return "-";
    return category
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  const formatStatus = (status) => {
    const statuses = {
      pending: "Pending",
      under_review: "Under Review",
      investigating: "Investigating",
      resolved: "Resolved",
      closed: "Closed",
      rejected: "Rejected",
    };
    return statuses[status] || status;
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "-";
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  const columns = [
    {
      header: "Report #",
      render: (row) => <strong>{row.reportNumber}</strong>,
    },
    {
      header: "Title",
      render: (row) =>
        row.title?.substring(0, 25) + (row.title?.length > 25 ? "..." : ""),
    },
    { header: "Category", render: (row) => formatCategory(row.category) },
    {
      header: "Priority",
      render: (row) => (
        <span className={`badge-priority ${row.priority}`}>{row.priority}</span>
      ),
    },
    {
      header: "Status",
      render: (row) => (
        <span className={`badge-status ${row.status}`}>
          {formatStatus(row.status)}
        </span>
      ),
    },
    {
      header: "District",
      accessor: "district",
      render: (row) => row.district || "-",
    },
    {
      header: "Source",
      render: (row) => (
        <span className={`badge-source ${row.source}`}>
          {row.source === "mobile" ? "📱 Mobile" : "👤 Registered"}
        </span>
      ),
    },
    { header: "Date", render: (row) => formatDate(row.createdAt) },
    {
      header: "Actions",
      render: (row) => (
        <div className="action-buttons">
          <button
            className="action-btn view"
            onClick={(e) => {
              e.stopPropagation();
              viewReport(row);
            }}
          >
            <i className="fas fa-eye"></i>
          </button>
        </div>
      ),
    },
  ];

  return (
    <div className="reports-page">
      <div className="page-header">
        <h1>Crime Reports</h1>
        <div className="filters">
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setCurrentPage(1);
            }}
          >
            <option value="">All Status</option>
            <option value="pending">Pending</option>
            <option value="under_review">Under Review</option>
            <option value="investigating">Investigating</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
          </select>
          <select
            value={categoryFilter}
            onChange={(e) => {
              setCategoryFilter(e.target.value);
              setCurrentPage(1);
            }}
          >
            <option value="">All Categories</option>
            <option value="theft">Theft</option>
            <option value="assault">Assault</option>
            <option value="robbery">Robbery</option>
            <option value="fraud">Fraud</option>
            <option value="vandalism">Vandalism</option>
            <option value="domestic_violence">Domestic Violence</option>
            <option value="cybercrime">Cybercrime</option>
            <option value="other">Other</option>
          </select>
        </div>
      </div>

      <div className="table-card full-width">
        <div className="card-body">
          <DataTable
            columns={columns}
            data={reports}
            loading={loading}
            onRowClick={viewReport}
          />
        </div>
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={setCurrentPage}
        />
      </div>

      {/* Report Detail Modal */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={`Report Details - ${selectedReport?.reportNumber}`}
        size="large"
      >
        {selectedReport && (
          <div className="report-detail">
            <div className="report-header">
              <div>
                <h2>{selectedReport.title}</h2>
                <span className={`badge-status ${selectedReport.status}`}>
                  {formatStatus(selectedReport.status)}
                </span>
                <span
                  className={`badge-priority ${selectedReport.priority}`}
                  style={{ marginLeft: 8 }}
                >
                  {selectedReport.priority}
                </span>
              </div>
              <span className={`badge-source ${selectedReport.source}`}>
                {selectedReport.source === "mobile"
                  ? "📱 Anonymous"
                  : "👤 Registered"}
              </span>
            </div>

            <div className="detail-grid">
              <div className="detail-section">
                <h4>
                  <i className="fas fa-info-circle"></i> Details
                </h4>
                <p>{selectedReport.description}</p>
              </div>

              <div className="detail-section">
                <h4>
                  <i className="fas fa-map-marker-alt"></i> Location
                </h4>
                <p>
                  {[
                    selectedReport.village,
                    selectedReport.cell,
                    selectedReport.sector,
                    selectedReport.district,
                    selectedReport.province,
                  ]
                    .filter(Boolean)
                    .join(", ") || "Not specified"}
                </p>
              </div>

              <div className="detail-section">
                <h4>
                  <i className="fas fa-calendar"></i> Incident Date
                </h4>
                <p>
                  {selectedReport.incidentDate
                    ? formatDate(selectedReport.incidentDate)
                    : "Not specified"}
                </p>
              </div>

              {trustScore && (
                <div className="detail-section trust-score">
                  <h4>
                    <i className="fas fa-shield-alt"></i> Trust Score
                  </h4>
                  <div
                    className={`trust-circle ${trustScore.score >= 0.7 ? "high" : trustScore.score >= 0.4 ? "medium" : "low"}`}
                  >
                    {Math.round(trustScore.score * 100)}%
                  </div>
                </div>
              )}
            </div>

            <div className="report-actions">
              <div className="action-group">
                <label>Update Status:</label>
                <select
                  value={selectedReport.status}
                  onChange={(e) => updateReportStatus(e.target.value)}
                >
                  <option value="pending">Pending</option>
                  <option value="under_review">Under Review</option>
                  <option value="investigating">Investigating</option>
                  <option value="resolved">Resolved</option>
                  <option value="closed">Closed</option>
                  <option value="rejected">Rejected</option>
                </select>
              </div>
              <button
                className="btn btn-secondary"
                onClick={() => setAssignModalOpen(true)}
              >
                <i className="fas fa-user-plus"></i> Assign Officer
              </button>
            </div>

            <div className="privacy-notice">
              <i className="fas fa-shield-alt"></i>
              <strong>Privacy Protected:</strong> Reporter identity is hidden to
              protect citizen privacy.
            </div>
          </div>
        )}
      </Modal>

      {/* Assign Officer Modal */}
      <Modal
        isOpen={assignModalOpen}
        onClose={() => setAssignModalOpen(false)}
        title="Assign Officer"
      >
        <div className="form-group">
          <label>Select Officer</label>
          <select
            value={selectedOfficer}
            onChange={(e) => setSelectedOfficer(e.target.value)}
          >
            <option value="">Select an officer...</option>
            {officers.map((officer) => (
              <option key={officer.id} value={officer.id}>
                {officer.name} ({officer.badgeNumber || "No Badge"}) -{" "}
                {officer.resolvedCases} resolved
              </option>
            ))}
          </select>
        </div>
        <div className="form-actions">
          <button
            className="btn btn-secondary"
            onClick={() => setAssignModalOpen(false)}
          >
            Cancel
          </button>
          <button className="btn btn-primary" onClick={assignOfficer}>
            Assign
          </button>
        </div>
      </Modal>
    </div>
  );
};

export default Reports;
