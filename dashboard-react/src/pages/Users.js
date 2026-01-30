import React, { useState, useEffect } from "react";
import DataTable from "../components/DataTable";
import Pagination from "../components/Pagination";
import Modal from "../components/Modal";
import { usersAPI } from "../services/api";
import "../styles/Users.css";

const Users = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [selectedUser, setSelectedUser] = useState(null);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [roleFilter, setRoleFilter] = useState("");

  useEffect(() => {
    loadUsers();
  }, [currentPage, roleFilter]);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const params = { page: currentPage, per_page: 20 };
      if (roleFilter) params.role = roleFilter;

      const response = await usersAPI.getUsers(params);
      setUsers(response.data.users || []);
      setTotalPages(response.data.pages || 1);
    } catch (error) {
      console.error("Error loading users:", error);
    } finally {
      setLoading(false);
    }
  };

  const viewUser = async (user) => {
    try {
      const response = await usersAPI.getUser(user.id);
      setSelectedUser(response.data.user);
      setDetailModalOpen(true);
    } catch (error) {
      console.error("Error loading user:", error);
    }
  };

  const toggleUserStatus = async (userId, currentStatus) => {
    try {
      await usersAPI.updateUser(userId, { isActive: !currentStatus });
      loadUsers();
    } catch (error) {
      console.error("Error updating user:", error);
    }
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

  const getRoleBadgeClass = (role) => {
    const classes = {
      admin: "admin",
      police_officer: "officer",
      citizen: "citizen",
    };
    return classes[role] || "default";
  };

  const formatRole = (role) => {
    const roles = {
      admin: "Administrator",
      police_officer: "Police Officer",
      citizen: "Citizen",
    };
    return roles[role] || role;
  };

  const columns = [
    {
      header: "User",
      render: (row) => (
        <div className="user-cell">
          <div className="avatar">
            {row.fullName?.charAt(0) || row.email?.charAt(0) || "U"}
          </div>
          <div>
            <strong>{row.fullName || "Unknown"}</strong>
            <span className="email">{row.email}</span>
          </div>
        </div>
      ),
    },
    {
      header: "Role",
      render: (row) => (
        <span className={`badge-role ${getRoleBadgeClass(row.role)}`}>
          {formatRole(row.role)}
        </span>
      ),
    },
    { header: "Phone", accessor: "phone", render: (row) => row.phone || "-" },
    {
      header: "District",
      accessor: "district",
      render: (row) => row.district || "-",
    },
    {
      header: "Status",
      render: (row) => (
        <span
          className={`badge-status ${row.isActive ? "active" : "inactive"}`}
        >
          {row.isActive ? "Active" : "Inactive"}
        </span>
      ),
    },
    { header: "Reports", render: (row) => row.reportsCount || 0 },
    { header: "Joined", render: (row) => formatDate(row.createdAt) },
    {
      header: "Actions",
      render: (row) => (
        <div className="action-buttons">
          <button
            className="action-btn view"
            onClick={(e) => {
              e.stopPropagation();
              viewUser(row);
            }}
          >
            <i className="fas fa-eye"></i>
          </button>
          <button
            className={`action-btn ${row.isActive ? "deactivate" : "activate"}`}
            onClick={(e) => {
              e.stopPropagation();
              toggleUserStatus(row.id, row.isActive);
            }}
          >
            <i className={`fas fa-${row.isActive ? "ban" : "check"}`}></i>
          </button>
        </div>
      ),
    },
  ];

  // Stats
  const totalUsers = users.length;
  const activeUsers = users.filter((u) => u.isActive).length;
  const adminCount = users.filter((u) => u.role === "admin").length;
  const officerCount = users.filter((u) => u.role === "police_officer").length;
  const citizenCount = users.filter((u) => u.role === "citizen").length;

  return (
    <div className="users-page">
      <div className="page-header">
        <h1>
          <i className="fas fa-users"></i> User Management
        </h1>
        <div className="filters">
          <select
            value={roleFilter}
            onChange={(e) => {
              setRoleFilter(e.target.value);
              setCurrentPage(1);
            }}
          >
            <option value="">All Roles</option>
            <option value="admin">Administrators</option>
            <option value="police_officer">Police Officers</option>
            <option value="citizen">Citizens</option>
          </select>
        </div>
      </div>

      {/* Stats Summary */}
      <div className="user-stats-summary">
        <div className="stat-box">
          <i className="fas fa-users"></i>
          <div>
            <span className="value">{totalUsers}</span>
            <span className="label">Total Users</span>
          </div>
        </div>
        <div className="stat-box active">
          <i className="fas fa-user-check"></i>
          <div>
            <span className="value">{activeUsers}</span>
            <span className="label">Active</span>
          </div>
        </div>
        <div className="stat-box admin">
          <i className="fas fa-user-shield"></i>
          <div>
            <span className="value">{adminCount}</span>
            <span className="label">Admins</span>
          </div>
        </div>
        <div className="stat-box officer">
          <i className="fas fa-user-tie"></i>
          <div>
            <span className="value">{officerCount}</span>
            <span className="label">Officers</span>
          </div>
        </div>
        <div className="stat-box citizen">
          <i className="fas fa-user"></i>
          <div>
            <span className="value">{citizenCount}</span>
            <span className="label">Citizens</span>
          </div>
        </div>
      </div>

      <div className="table-card full-width">
        <div className="card-body">
          <DataTable
            columns={columns}
            data={users}
            loading={loading}
            onRowClick={viewUser}
          />
        </div>
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={setCurrentPage}
        />
      </div>

      {/* User Detail Modal */}
      <Modal
        isOpen={detailModalOpen}
        onClose={() => setDetailModalOpen(false)}
        title="User Details"
        size="medium"
      >
        {selectedUser && (
          <div className="user-detail">
            <div className="user-header">
              <div className="avatar large">
                {selectedUser.fullName?.charAt(0) || "U"}
              </div>
              <div>
                <h2>{selectedUser.fullName || "Unknown"}</h2>
                <span
                  className={`badge-role ${getRoleBadgeClass(selectedUser.role)}`}
                >
                  {formatRole(selectedUser.role)}
                </span>
                <span
                  className={`badge-status ${selectedUser.isActive ? "active" : "inactive"}`}
                >
                  {selectedUser.isActive ? "Active" : "Inactive"}
                </span>
              </div>
            </div>

            <div className="detail-grid">
              <div className="detail-item">
                <label>
                  <i className="fas fa-envelope"></i> Email
                </label>
                <span>{selectedUser.email}</span>
              </div>
              <div className="detail-item">
                <label>
                  <i className="fas fa-phone"></i> Phone
                </label>
                <span>{selectedUser.phone || "Not provided"}</span>
              </div>
              <div className="detail-item">
                <label>
                  <i className="fas fa-map-marker-alt"></i> District
                </label>
                <span>{selectedUser.district || "Not specified"}</span>
              </div>
              <div className="detail-item">
                <label>
                  <i className="fas fa-calendar"></i> Joined
                </label>
                <span>{formatDate(selectedUser.createdAt)}</span>
              </div>
              {selectedUser.role === "police_officer" && (
                <>
                  <div className="detail-item">
                    <label>
                      <i className="fas fa-id-badge"></i> Badge Number
                    </label>
                    <span>{selectedUser.badgeNumber || "Not assigned"}</span>
                  </div>
                  <div className="detail-item">
                    <label>
                      <i className="fas fa-building"></i> Station
                    </label>
                    <span>{selectedUser.station || "Not assigned"}</span>
                  </div>
                </>
              )}
            </div>

            <div className="user-actions">
              <button
                className={`btn ${selectedUser.isActive ? "btn-danger" : "btn-success"}`}
                onClick={() => {
                  toggleUserStatus(selectedUser.id, selectedUser.isActive);
                  setDetailModalOpen(false);
                }}
              >
                <i
                  className={`fas fa-${selectedUser.isActive ? "ban" : "check"}`}
                ></i>
                {selectedUser.isActive ? "Deactivate User" : "Activate User"}
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default Users;
