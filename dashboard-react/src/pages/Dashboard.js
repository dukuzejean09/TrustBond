import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import { Line, Doughnut } from "react-chartjs-2";
import StatCard from "../components/StatCard";
import DataTable from "../components/DataTable";
import { dashboardAPI } from "../services/api";
import "../styles/Dashboard.css";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
);

const Dashboard = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState({});
  const [recentReports, setRecentReports] = useState([]);
  const [trendData, setTrendData] = useState(null);
  const [categoryData, setCategoryData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);

      // Load stats
      const statsRes = await dashboardAPI.getStats();
      setStats(statsRes.data);

      // Load recent reports
      const reportsRes = await dashboardAPI.getRecentReports();
      setRecentReports(reportsRes.data.reports || []);

      // Load trend data
      const trendRes = await dashboardAPI.getReportsTrend();
      if (trendRes.data.data) {
        setTrendData({
          labels: trendRes.data.data.map((item) => {
            const date = new Date(item.date);
            return date.toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
            });
          }),
          datasets: [
            {
              label: "Reports",
              data: trendRes.data.data.map((item) => item.count),
              borderColor: "#0D1B4C",
              backgroundColor: "rgba(13, 27, 76, 0.1)",
              fill: true,
              tension: 0.4,
            },
          ],
        });
      }

      // Load category data
      const categoryRes = await dashboardAPI.getReportsByCategory();
      if (categoryRes.data.data) {
        const colors = [
          "#0D1B4C",
          "#FFB800",
          "#2196F3",
          "#4CAF50",
          "#FF9800",
          "#9C27B0",
          "#F44336",
        ];
        setCategoryData({
          labels: categoryRes.data.data.map((item) =>
            formatCategory(item.category),
          ),
          datasets: [
            {
              data: categoryRes.data.data.map((item) => item.count),
              backgroundColor: colors.slice(0, categoryRes.data.data.length),
            },
          ],
        });
      }
    } catch (error) {
      console.error("Error loading dashboard data:", error);
    } finally {
      setLoading(false);
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

  const reportColumns = [
    {
      header: "Report #",
      render: (row) => <strong>{row.reportNumber}</strong>,
    },
    {
      header: "Title",
      render: (row) =>
        row.title?.substring(0, 30) + (row.title?.length > 30 ? "..." : ""),
    },
    { header: "Category", render: (row) => formatCategory(row.category) },
    {
      header: "Status",
      render: (row) => (
        <span className={`badge-status ${row.status}`}>
          {formatStatus(row.status)}
        </span>
      ),
    },
    { header: "Date", render: (row) => formatDate(row.createdAt) },
  ];

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
    },
    scales: {
      y: { beginAtZero: true },
    },
  };

  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: "right" },
    },
  };

  return (
    <div className="dashboard-page">
      {/* Stats Cards */}
      <div className="stats-grid">
        <StatCard
          icon="fa-file-alt"
          iconColor="primary"
          value={stats.totalReports || 0}
          label="Total Reports"
          cardType="reports"
          subtitle={`${stats.reportsThisWeek || 0} this week`}
          onClick={() => navigate("/reports")}
        />
        <StatCard
          icon="fa-clock"
          iconColor="warning"
          value={stats.pendingReports || 0}
          label="Pending Review"
          cardType="pending"
          subtitle="Awaiting action"
        />
        <StatCard
          icon="fa-check-circle"
          iconColor="success"
          value={stats.resolvedReports || 0}
          label="Resolved Cases"
          cardType="resolved"
          subtitle={`${stats.resolutionRate || 0}% rate`}
        />
        <StatCard
          icon="fa-bell"
          iconColor="danger"
          value={stats.activeAlerts || 0}
          label="Active Alerts"
          cardType="alerts"
          subtitle="Requires attention"
          onClick={() => navigate("/alerts")}
        />
      </div>

      {/* Charts Row */}
      <div className="charts-grid">
        <div className="chart-card">
          <h3>
            <i className="fas fa-chart-line"></i> Reports Trend (Last 30 Days)
          </h3>
          <div className="chart-container">
            {trendData ? (
              <Line data={trendData} options={chartOptions} />
            ) : (
              <div className="loading-state">
                <div className="loading-spinner"></div>
                <p>Loading chart data...</p>
              </div>
            )}
          </div>
        </div>

        <div className="chart-card">
          <h3>
            <i className="fas fa-chart-pie"></i> Reports by Category
          </h3>
          <div className="chart-container">
            {categoryData ? (
              <Doughnut data={categoryData} options={doughnutOptions} />
            ) : (
              <div className="loading-state">
                <div className="loading-spinner"></div>
                <p>Loading chart data...</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Bottom Row */}
      <div className="content-grid">
        <div className="table-card">
          <h3>
            <i className="fas fa-list"></i> Recent Reports
          </h3>
          <DataTable
            columns={reportColumns}
            data={recentReports}
            loading={loading}
            onRowClick={(row) => navigate(`/reports?id=${row.id}`)}
          />
        </div>

        <div className="quick-stats-card">
          <h3>
            <i className="fas fa-tachometer-alt"></i> Quick Stats
          </h3>
          <div className="quick-stats-list">
            <div className="quick-stat-item highlight">
              <span className="label">Resolution Rate</span>
              <span className="value">{stats.resolutionRate || 0}%</span>
            </div>
            <div className="quick-stat-item">
              <span className="label">Reports This Week</span>
              <span className="value">{stats.reportsThisWeek || 0}</span>
            </div>
            <div className="quick-stat-item">
              <span className="label">Reports This Month</span>
              <span className="value">{stats.reportsThisMonth || 0}</span>
            </div>
            <div className="quick-stat-item gold">
              <span className="label">Active Officers</span>
              <span className="value">{stats.totalOfficers || 0}</span>
            </div>
            <div className="quick-stat-item">
              <span className="label">Registered Users</span>
              <span className="value">{stats.totalUsers || 0}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
