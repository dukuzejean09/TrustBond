import React, { useState, useEffect } from "react";
import DataTable from "../components/DataTable";
import Pagination from "../components/Pagination";
import Modal from "../components/Modal";
import { dashboardAPI } from "../services/api";
import "../styles/Officers.css";

const Officers = () => {
  const [officers, setOfficers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [selectedOfficer, setSelectedOfficer] = useState(null);
  const [detailModalOpen, setDetailModalOpen] = useState(false);

  useEffect(() => {
    loadOfficers();
  }, [currentPage]);

  const loadOfficers = async () => {
    try {
      setLoading(true);
      const response = await dashboardAPI.getOfficerPerformance();
      const allOfficers = response.data.data || [];

      // Client-side pagination
      const perPage = 15;
      const startIndex = (currentPage - 1) * perPage;
      const paginatedOfficers = allOfficers.slice(
        startIndex,
        startIndex + perPage,
      );

      setOfficers(paginatedOfficers);
      setTotalPages(Math.ceil(allOfficers.length / perPage) || 1);
    } catch (error) {
      console.error("Error loading officers:", error);
    } finally {
      setLoading(false);
    }
  };

  const viewOfficer = (officer) => {
    setSelectedOfficer(officer);
    setDetailModalOpen(true);
  };

  const getPerformanceLevel = (resolved, assigned) => {
    if (assigned === 0) return { level: "new", label: "New" };
    const rate = (resolved / assigned) * 100;
    if (rate >= 80) return { level: "excellent", label: "Excellent" };
    if (rate >= 60) return { level: "good", label: "Good" };
    if (rate >= 40) return { level: "average", label: "Average" };
    return { level: "needs-improvement", label: "Needs Improvement" };
  };

  const columns = [
    {
      header: "Officer",
      render: (row) => (
        <div className="officer-cell">
          <div className="avatar">{row.name?.charAt(0) || "O"}</div>
          <div>
            <strong>{row.name}</strong>
            <span className="badge-number">
              {row.badgeNumber || "No Badge"}
            </span>
          </div>
        </div>
      ),
    },
    { header: "Email", accessor: "email" },
    {
      header: "District",
      accessor: "district",
      render: (row) => row.district || "-",
    },
    {
      header: "Cases Assigned",
      render: (row) => (
        <span className="stat-value">{row.assignedCases || 0}</span>
      ),
    },
    {
      header: "Cases Resolved",
      render: (row) => (
        <span className="stat-value success">{row.resolvedCases || 0}</span>
      ),
    },
    {
      header: "Avg Response",
      render: (row) => (
        <span
          className={`response-time ${row.avgResponseTime < 24 ? "fast" : row.avgResponseTime < 48 ? "normal" : "slow"}`}
        >
          {row.avgResponseTime?.toFixed(1) || 0}h
        </span>
      ),
    },
    {
      header: "Performance",
      render: (row) => {
        const perf = getPerformanceLevel(row.resolvedCases, row.assignedCases);
        return (
          <span className={`badge-performance ${perf.level}`}>
            {perf.label}
          </span>
        );
      },
    },
    {
      header: "Actions",
      render: (row) => (
        <button
          className="action-btn view"
          onClick={(e) => {
            e.stopPropagation();
            viewOfficer(row);
          }}
        >
          <i className="fas fa-eye"></i>
        </button>
      ),
    },
  ];

  // Calculate stats
  const totalOfficers = officers.length;
  const totalAssigned = officers.reduce(
    (sum, o) => sum + (o.assignedCases || 0),
    0,
  );
  const totalResolved = officers.reduce(
    (sum, o) => sum + (o.resolvedCases || 0),
    0,
  );
  const avgResponse =
    officers.length > 0
      ? officers.reduce((sum, o) => sum + (o.avgResponseTime || 0), 0) /
        officers.length
      : 0;

  return (
    <div className="officers-page">
      <div className="page-header">
        <h1>
          <i className="fas fa-user-shield"></i> Police Officers
        </h1>
      </div>

      {/* Stats Summary */}
      <div className="officer-stats-summary">
        <div className="stat-box">
          <i className="fas fa-users"></i>
          <div>
            <span className="value">{totalOfficers}</span>
            <span className="label">Total Officers</span>
          </div>
        </div>
        <div className="stat-box">
          <i className="fas fa-folder-open"></i>
          <div>
            <span className="value">{totalAssigned}</span>
            <span className="label">Cases Assigned</span>
          </div>
        </div>
        <div className="stat-box">
          <i className="fas fa-check-double"></i>
          <div>
            <span className="value">{totalResolved}</span>
            <span className="label">Cases Resolved</span>
          </div>
        </div>
        <div className="stat-box">
          <i className="fas fa-clock"></i>
          <div>
            <span className="value">{avgResponse.toFixed(1)}h</span>
            <span className="label">Avg Response</span>
          </div>
        </div>
      </div>

      <div className="table-card full-width">
        <div className="card-body">
          <DataTable
            columns={columns}
            data={officers}
            loading={loading}
            onRowClick={viewOfficer}
          />
        </div>
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={setCurrentPage}
        />
      </div>

      {/* Officer Detail Modal */}
      <Modal
        isOpen={detailModalOpen}
        onClose={() => setDetailModalOpen(false)}
        title="Officer Details"
        size="medium"
      >
        {selectedOfficer && (
          <div className="officer-detail">
            <div className="officer-header">
              <div className="avatar large">
                {selectedOfficer.name?.charAt(0) || "O"}
              </div>
              <div>
                <h2>{selectedOfficer.name}</h2>
                <p className="badge-number">
                  {selectedOfficer.badgeNumber || "No Badge Number"}
                </p>
                <p className="email">{selectedOfficer.email}</p>
              </div>
            </div>

            <div className="detail-stats">
              <div className="stat-card">
                <i className="fas fa-folder-open"></i>
                <span className="value">
                  {selectedOfficer.assignedCases || 0}
                </span>
                <span className="label">Assigned</span>
              </div>
              <div className="stat-card">
                <i className="fas fa-check-circle"></i>
                <span className="value">
                  {selectedOfficer.resolvedCases || 0}
                </span>
                <span className="label">Resolved</span>
              </div>
              <div className="stat-card">
                <i className="fas fa-clock"></i>
                <span className="value">
                  {selectedOfficer.avgResponseTime?.toFixed(1) || 0}h
                </span>
                <span className="label">Avg Response</span>
              </div>
              <div className="stat-card">
                <i className="fas fa-percentage"></i>
                <span className="value">
                  {selectedOfficer.assignedCases > 0
                    ? (
                        (selectedOfficer.resolvedCases /
                          selectedOfficer.assignedCases) *
                        100
                      ).toFixed(0)
                    : 0}
                  %
                </span>
                <span className="label">Resolution Rate</span>
              </div>
            </div>

            <div className="detail-info">
              <div className="info-item">
                <label>District</label>
                <span>{selectedOfficer.district || "Not Assigned"}</span>
              </div>
              <div className="info-item">
                <label>Performance</label>
                <span
                  className={`badge-performance ${getPerformanceLevel(selectedOfficer.resolvedCases, selectedOfficer.assignedCases).level}`}
                >
                  {
                    getPerformanceLevel(
                      selectedOfficer.resolvedCases,
                      selectedOfficer.assignedCases,
                    ).label
                  }
                </span>
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default Officers;
