import React, { useState, useEffect } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import { Line, Bar, Doughnut } from "react-chartjs-2";
import { analyticsAPI, dashboardAPI } from "../services/api";
import StatCard from "../components/StatCard";
import "../styles/Analytics.css";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
);

const Analytics = () => {
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState("30");
  const [trendsData, setTrendsData] = useState(null);
  const [categoryData, setCategoryData] = useState(null);
  const [districtData, setDistrictData] = useState(null);
  const [officerData, setOfficerData] = useState([]);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    loadAnalytics();
  }, [dateRange]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const [
        overviewRes,
        trendsRes,
        statsRes,
        officerRes,
        categoryRes,
        districtRes,
      ] = await Promise.all([
        analyticsAPI.getOverview(parseInt(dateRange)),
        analyticsAPI.getTrends({ days: parseInt(dateRange) }),
        dashboardAPI.getStats(),
        dashboardAPI.getOfficerPerformance(),
        dashboardAPI.getReportsByCategory(),
        dashboardAPI.getReportsByDistrict(),
      ]);

      // Set trends data from API
      setTrendsData({
        dailyTrend: trendsRes.data.reportTrends || [],
        resolutionTrend: trendsRes.data.resolutionTrends || [],
        categoryTrends: trendsRes.data.categoryTrends || {},
      });

      // Merge stats from both endpoints
      setStats({
        ...statsRes.data,
        ...overviewRes.data.performance,
        avgResponseTime: overviewRes.data.performance?.avgResolutionHours || 0,
        activeHotspots: 0, // Will be updated from ML API if needed
      });

      setOfficerData(officerRes.data.data || []);

      // Process category data from dashboard API
      if (categoryRes.data?.data) {
        const catObj = {};
        categoryRes.data.data.forEach((item) => {
          catObj[item.category] = item.count;
        });
        setCategoryData(catObj);
      }

      // Process district data from dashboard API
      if (districtRes.data?.data) {
        const distObj = {};
        districtRes.data.data.forEach((item) => {
          distObj[item.district] = item.count;
        });
        setDistrictData(distObj);
      }
    } catch (error) {
      console.error("Error loading analytics:", error);
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

  // Chart configurations - Use RNP colors
  const trendChartData = {
    labels:
      trendsData?.dailyTrend?.map((d) => {
        const date = new Date(d.period);
        return date.toLocaleDateString("en-US", {
          month: "short",
          day: "numeric",
        });
      }) || [],
    datasets: [
      {
        label: "Reports",
        data: trendsData?.dailyTrend?.map((d) => d.count) || [],
        fill: true,
        backgroundColor: "rgba(13, 27, 76, 0.1)",
        borderColor: "#0d1b4c",
        tension: 0.4,
      },
    ],
  };

  const categoryChartData = {
    labels: categoryData ? Object.keys(categoryData).map(formatCategory) : [],
    datasets: [
      {
        data: categoryData ? Object.values(categoryData) : [],
        backgroundColor: [
          "#0d1b4c",
          "#ffb800",
          "#1e3a6e",
          "#10b981",
          "#f59e0b",
          "#ef4444",
          "#3b82f6",
          "#9b59b6",
          "#1abc9c",
          "#e91e63",
          "#00bcd4",
          "#795548",
        ],
      },
    ],
  };

  const districtChartData = {
    labels: districtData ? Object.keys(districtData) : [],
    datasets: [
      {
        label: "Reports by District",
        data: districtData ? Object.values(districtData) : [],
        backgroundColor: "rgba(13, 27, 76, 0.8)",
        borderColor: "#0d1b4c",
        borderWidth: 1,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "bottom",
      },
    },
  };

  const barOptions = {
    ...chartOptions,
    indexAxis: "y",
    plugins: {
      legend: {
        display: false,
      },
    },
  };

  if (loading) {
    return (
      <div className="analytics-page loading">
        <i className="fas fa-spinner fa-spin"></i> Loading analytics...
      </div>
    );
  }

  return (
    <div className="analytics-page">
      <div className="page-header">
        <h1>
          <i className="fas fa-chart-line"></i> Analytics Dashboard
        </h1>
        <div className="controls">
          <select
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value)}
          >
            <option value="7">Last 7 Days</option>
            <option value="30">Last 30 Days</option>
            <option value="90">Last 90 Days</option>
            <option value="365">Last Year</option>
          </select>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="stats-grid">
        <StatCard
          title="Total Reports"
          value={stats?.totalReports || 0}
          icon="fa-file-alt"
          color="primary"
        />
        <StatCard
          title="Resolution Rate"
          value={`${stats?.resolutionRate?.toFixed(1) || 0}%`}
          icon="fa-check-circle"
          color="success"
        />
        <StatCard
          title="Avg. Response Time"
          value={`${stats?.avgResponseTime?.toFixed(1) || 0}h`}
          icon="fa-clock"
          color="warning"
        />
        <StatCard
          title="Active Hotspots"
          value={stats?.activeHotspots || 0}
          icon="fa-fire"
          color="danger"
        />
      </div>

      {/* Charts Grid */}
      <div className="charts-grid">
        <div className="chart-card large">
          <h3>Report Trends</h3>
          <div className="chart-container">
            <Line data={trendChartData} options={chartOptions} />
          </div>
        </div>

        <div className="chart-card">
          <h3>Category Distribution</h3>
          <div className="chart-container">
            <Doughnut data={categoryChartData} options={chartOptions} />
          </div>
        </div>

        <div className="chart-card">
          <h3>Reports by District</h3>
          <div className="chart-container">
            <Bar data={districtChartData} options={barOptions} />
          </div>
        </div>
      </div>

      {/* Officer Performance */}
      <div className="performance-section">
        <h3>
          <i className="fas fa-trophy"></i> Top Performing Officers
        </h3>
        <div className="officer-cards">
          {officerData.slice(0, 5).map((officer, index) => (
            <div key={officer.id} className={`officer-card rank-${index + 1}`}>
              <div className="rank-badge">{index + 1}</div>
              <div className="officer-info">
                <h4>{officer.name}</h4>
                <p className="badge-number">
                  {officer.badgeNumber || "No Badge"}
                </p>
              </div>
              <div className="officer-stats">
                <div className="stat">
                  <span className="value">{officer.resolvedCases || 0}</span>
                  <span className="label">Resolved</span>
                </div>
                <div className="stat">
                  <span className="value">{officer.assignedCases || 0}</span>
                  <span className="label">Assigned</span>
                </div>
                <div className="stat">
                  <span className="value">
                    {officer.avgResponseTime?.toFixed(1) || 0}h
                  </span>
                  <span className="label">Avg Response</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Insights */}
      <div className="insights-section">
        <h3>
          <i className="fas fa-lightbulb"></i> Key Insights
        </h3>
        <div className="insights-grid">
          <div className="insight-card">
            <i className="fas fa-trending-up"></i>
            <div>
              <h4>Trend Analysis</h4>
              <p>
                Crime reports have{" "}
                {trendsData?.trend === "increasing" ? "increased" : "decreased"}{" "}
                over the selected period.
              </p>
            </div>
          </div>
          <div className="insight-card">
            <i className="fas fa-map-marker-alt"></i>
            <div>
              <h4>Hotspot Activity</h4>
              <p>
                {stats?.activeHotspots || 0} active crime hotspots require
                attention.
              </p>
            </div>
          </div>
          <div className="insight-card">
            <i className="fas fa-user-shield"></i>
            <div>
              <h4>Team Performance</h4>
              <p>
                Officers have resolved {stats?.resolvedReports || 0} cases this
                period.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics;
