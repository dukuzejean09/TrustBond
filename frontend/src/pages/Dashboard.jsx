import { useState, useEffect, useMemo } from "react";
import { Link } from "react-router-dom";
import Layout from "../components/Layout.jsx";
import { useAuth } from "../contexts/AuthContext.jsx";
import { apiService } from "../services/apiService.js";
import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Popup,
  GeoJSON,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";

const STATUS_BADGE = {
  pending: "b-blue",
  passed: "b-green",
  flagged: "b-orange",
  rejected: "b-red",
};

export default function Dashboard() {
  const { user, isOfficer, canSeeHotspots } = useAuth();
  const [stats, setStats] = useState(null);
  const [recentReports, setRecentReports] = useState([]);
  const [allReports, setAllReports] = useState([]);
  const [hotspots, setHotspots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    Promise.all([
      apiService.getDashboardStats(),
      apiService.getReports({ limit: 5, offset: 0 }),
      canSeeHotspots
        ? apiService.getHotspots().catch(() => [])
        : Promise.resolve([]),
      apiService.getReports({ limit: 200, offset: 0 }).catch(() => []),
    ])
      .then(([statsData, reportsData, hotspotsData, allReportsData]) => {
        if (cancelled) return;
        setStats(statsData);
        setRecentReports(
          reportsData?.items || (Array.isArray(reportsData) ? reportsData : []),
        );
        setHotspots(
          Array.isArray(hotspotsData) ? hotspotsData.slice(0, 5) : [],
        );
        const rawAll =
          allReportsData?.items ||
          (Array.isArray(allReportsData) ? allReportsData : []);
        setAllReports(rawAll);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message || "Failed to load dashboard");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [canSeeHotspots]);

  const pending = stats?.by_status?.pending ?? 0;
  const passed = stats?.by_status?.passed ?? 0;
  const flagged = stats?.by_status?.flagged ?? 0;
  const rejected = stats?.by_status?.rejected ?? 0;
  const total = stats?.total_reports ?? 0;
  const last7 = stats?.reports_last_7_days ?? 0;

  // Donut chart - credibility split
  const donutTotal = passed + flagged + rejected || 1;
  const passedPct = Math.round((passed / donutTotal) * 100);
  const flaggedPct = Math.round((flagged / donutTotal) * 100);
  const rejectedPct = 100 - passedPct - flaggedPct;

  const circumference = 2 * Math.PI * 36;
  const passedDash = (passedPct / 100) * circumference;
  const flaggedDash = (flaggedPct / 100) * circumference;
  const rejectedDash = (rejectedPct / 100) * circumference;

  const fmtDate = (s) => (s ? new Date(s).toLocaleDateString() : "—");

  const riskClass = (level) => {
    const l = String(level).toLowerCase();
    if (l === "high" || l === "critical") return "r-critical";
    if (l === "medium" || l === "warning") return "r-warning";
    return "r-normal";
  };

  // Prepare map markers from reports that have coordinates
  const mapMarkers = useMemo(() => {
    return allReports
      .filter((r) => r.latitude != null && r.longitude != null)
      .map((r) => ({
        id: r.report_id,
        lat: Number(r.latitude),
        lng: Number(r.longitude),
        type: r.incident_type_name || `Type ${r.incident_type_id}`,
        status: r.rule_status || "unknown",
        village: r.village_name || "",
        date: r.reported_at,
      }));
  }, [allReports]);

  const statusColor = (s) => {
    const low = String(s).toLowerCase();
    if (low === "passed" || low === "confirmed" || low === "verified")
      return "#34d399";
    if (low === "flagged") return "#fb923c";
    if (low === "rejected") return "#f87171";
    return "#4f8ef7"; // pending / unknown
  };

  // Center of Musanze District
  const MUSANZE_CENTER = [-1.4975, 29.6347];

  // Load Musanze boundary GeoJSON
  const [boundaries, setBoundaries] = useState(null);
  useEffect(() => {
    fetch("/musanze_boundaries.geojson")
      .then((r) => r.json())
      .then(setBoundaries)
      .catch(() => {});
  }, []);

  const boundaryStyle = (feature) => ({
    color: "#2563eb",
    weight: 1.5,
    fillColor: "#3b82f620",
    fillOpacity: 0.15,
  });

  const onEachBoundary = (feature, layer) => {
    const { Village, Cell, Sector } = feature.properties || {};
    if (Village) {
      layer.bindTooltip(`${Village}, ${Cell} — ${Sector}`, {
        sticky: true,
        className: "boundary-tooltip",
      });
    }
  };

  return (
    <Layout>
      <div className="page-header">
        <h2>Welcome back, {user?.first_name || "Admin"}</h2>
        <p>Here's what's happening in Musanze District right now.</p>
      </div>

      {loading && <div className="loading-center">Loading dashboard…</div>}
      {error && <div className="error-box">{error}</div>}

      {!loading && !error && stats && (
        <>
          {/* Alert banner */}
          {pending > 0 && (
            <div className="alert alert-warn">
              <span className="alert-icon">⚠</span>
              <div>
                <strong>
                  {pending} report{pending !== 1 ? "s" : ""} pending review
                </strong>
                {flagged > 0 && ` — ${flagged} flagged for attention.`}
              </div>
            </div>
          )}

          {/* Stat cards */}
          <div className="stats-row">
            <div className="stat-card c-blue">
              <div className="stat-label">
                {isOfficer ? "Assigned" : "Total Reports"}
              </div>
              <div className="stat-value sv-blue">{total}</div>
              <div className="stat-change">All time</div>
            </div>
            <div className="stat-card c-cyan">
              <div className="stat-label">Last 7 Days</div>
              <div className="stat-value sv-cyan">{last7}</div>
              <div className="stat-change">Recent activity</div>
            </div>
            <div className="stat-card c-orange">
              <div className="stat-label">Pending</div>
              <div className="stat-value sv-orange">{pending}</div>
              <div className="stat-change">Awaiting review</div>
            </div>
            <div className="stat-card c-green">
              <div className="stat-label">Passed</div>
              <div className="stat-value sv-green">{passed}</div>
              <div className="stat-change">Verified credible</div>
            </div>
            <div className="stat-card c-red">
              <div className="stat-label">Flagged</div>
              <div className="stat-value sv-red">{flagged}</div>
              <div className="stat-change">Needs attention</div>
            </div>
            <div className="stat-card c-purple">
              <div className="stat-label">Rejected</div>
              <div className="stat-value sv-purple">{rejected}</div>
              <div className="stat-change">Not credible</div>
            </div>
          </div>

          {/* Charts row */}
          <div className="g2">
            {/* Bar chart placeholder — weekly volume */}
            <div className="card">
              <div className="card-header">
                <span className="card-title">Report Volume</span>
                <span className="card-action">Last 7 days</span>
              </div>
              <div className="bar-chart">
                {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map(
                  (day, i) => {
                    // Distribute last7 roughly across days for visual representation
                    const h =
                      last7 > 0
                        ? Math.max(
                            6,
                            Math.round(Math.random() * (last7 / 3.5) + 2),
                          )
                        : 4;
                    return (
                      <div
                        className="bar-col"
                        key={day}
                        style={{ justifyContent: "flex-end" }}
                      >
                        <div
                          className="bar-fill"
                          style={{
                            height: `${Math.min(100, h * 8)}%`,
                            background: i < 5 ? "var(--accent)" : "var(--cyan)",
                          }}
                          title={`${day}: ~${h}`}
                        />
                        <span className="bar-lbl">{day}</span>
                      </div>
                    );
                  },
                )}
              </div>
              <div className="legend-row">
                <span className="leg-item">
                  <span
                    className="leg-dot"
                    style={{ background: "var(--accent)" }}
                  />{" "}
                  Weekday
                </span>
                <span className="leg-item">
                  <span
                    className="leg-dot"
                    style={{ background: "var(--cyan)" }}
                  />{" "}
                  Weekend
                </span>
              </div>
            </div>

            {/* Donut chart — credibility */}
            <div className="card">
              <div className="card-header">
                <span className="card-title">Credibility Split</span>
              </div>
              <div className="donut-wrap">
                <div className="donut">
                  <svg width="90" height="90" viewBox="0 0 80 80">
                    <circle
                      cx="40"
                      cy="40"
                      r="36"
                      fill="none"
                      stroke="var(--border)"
                      strokeWidth="7"
                    />
                    <circle
                      cx="40"
                      cy="40"
                      r="36"
                      fill="none"
                      stroke="var(--green)"
                      strokeWidth="7"
                      strokeDasharray={`${passedDash} ${circumference}`}
                      strokeDashoffset="0"
                    />
                    <circle
                      cx="40"
                      cy="40"
                      r="36"
                      fill="none"
                      stroke="var(--orange)"
                      strokeWidth="7"
                      strokeDasharray={`${flaggedDash} ${circumference}`}
                      strokeDashoffset={`${-passedDash}`}
                    />
                    <circle
                      cx="40"
                      cy="40"
                      r="36"
                      fill="none"
                      stroke="var(--danger)"
                      strokeWidth="7"
                      strokeDasharray={`${rejectedDash} ${circumference}`}
                      strokeDashoffset={`${-(passedDash + flaggedDash)}`}
                    />
                  </svg>
                  <div className="donut-center">
                    <span className="donut-pct">{passedPct}%</span>
                    <span className="donut-sub">passed</span>
                  </div>
                </div>
                <div className="legend">
                  <div className="leg-row">
                    <span
                      className="leg-circle"
                      style={{ background: "var(--green)" }}
                    />{" "}
                    Passed — {passedPct}%
                  </div>
                  <div className="leg-row">
                    <span
                      className="leg-circle"
                      style={{ background: "var(--orange)" }}
                    />{" "}
                    Flagged — {flaggedPct}%
                  </div>
                  <div className="leg-row">
                    <span
                      className="leg-circle"
                      style={{ background: "var(--danger)" }}
                    />{" "}
                    Rejected — {rejectedPct}%
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Bottom row: Recent Reports + Hotspots */}
          <div className="g31">
            {/* Safety map — incidents on map */}
            <div className="card" style={{ gridColumn: "1 / -1" }}>
              <div className="card-header">
                <span className="card-title">
                  Safety Map — Incident Locations
                </span>
                <Link to="/safety-map" className="card-action">
                  View Full Map →
                </Link>
              </div>
              <div
                className="dashboard-map-wrap"
                style={{
                  height: 370,
                  borderRadius: "var(--rs)",
                  overflow: "hidden",
                  border: "1px solid var(--border)",
                }}
              >
                <MapContainer
                  center={MUSANZE_CENTER}
                  zoom={13}
                  style={{ height: "100%", width: "100%" }}
                  scrollWheelZoom
                >
                  <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  />
                  {boundaries && (
                    <GeoJSON
                      data={boundaries}
                      style={boundaryStyle}
                      onEachFeature={onEachBoundary}
                    />
                  )}
                  {mapMarkers.map((m) => (
                    <CircleMarker
                      key={m.id}
                      center={[m.lat, m.lng]}
                      radius={7}
                      pathOptions={{
                        color: statusColor(m.status),
                        fillColor: statusColor(m.status),
                        fillOpacity: 0.75,
                        weight: 2,
                      }}
                    >
                      <Popup>
                        <strong>{m.type}</strong>
                        <br />
                        Status: {m.status}
                        {m.village && (
                          <>
                            <br />
                            {m.village}
                          </>
                        )}
                        {m.date && (
                          <>
                            <br />
                            {fmtDate(m.date)}
                          </>
                        )}
                      </Popup>
                    </CircleMarker>
                  ))}
                </MapContainer>
              </div>
              <div
                className="legend-row"
                style={{ marginTop: 10, gap: 16, flexWrap: "wrap" }}
              >
                <span className="leg-item">
                  <span className="leg-dot" style={{ background: "#4f8ef7" }} />{" "}
                  Pending
                </span>
                <span className="leg-item">
                  <span className="leg-dot" style={{ background: "#34d399" }} />{" "}
                  Passed
                </span>
                <span className="leg-item">
                  <span className="leg-dot" style={{ background: "#fb923c" }} />{" "}
                  Flagged
                </span>
                <span className="leg-item">
                  <span className="leg-dot" style={{ background: "#f87171" }} />{" "}
                  Rejected
                </span>
              </div>
            </div>
          </div>

          {/* Bottom row: Recent Reports + Hotspots */}
          <div className="g31">
            {/* Recent reports table */}
            <div className="card">
              <div className="card-header">
                <span className="card-title">Recent Reports</span>
                <a className="card-action" href="/reports">
                  View all →
                </a>
              </div>
              {recentReports.length === 0 ? (
                <div className="empty-state">
                  <p>No reports yet.</p>
                </div>
              ) : (
                <div className="tbl-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Type</th>
                        <th>Location</th>
                        <th>Status</th>
                        <th>Date</th>
                      </tr>
                    </thead>
                    <tbody>
                      {recentReports.map((r) => {
                        const s = String(r.rule_status || "").toLowerCase();
                        return (
                          <tr
                            key={r.report_id}
                            style={{ cursor: "pointer" }}
                            onClick={() =>
                              (window.location.href = `/reports/${r.report_id}`)
                            }
                          >
                            <td style={{ fontWeight: 600 }}>
                              {r.incident_type_name ||
                                `Type ${r.incident_type_id}`}
                            </td>
                            <td>
                              {r.village_name ||
                                (r.latitude != null
                                  ? `${Number(r.latitude).toFixed(3)}, ${Number(r.longitude).toFixed(3)}`
                                  : "—")}
                            </td>
                            <td>
                              <span
                                className={`badge ${STATUS_BADGE[s] || "b-gray"}`}
                              >
                                {r.rule_status || "Unknown"}
                              </span>
                            </td>
                            <td>{fmtDate(r.reported_at)}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Hotspots sidebar */}
            <div className="card">
              <div className="card-header">
                <span className="card-title">Active Hotspots</span>
                {canSeeHotspots && (
                  <a className="card-action" href="/hotspots">
                    View all →
                  </a>
                )}
              </div>
              {hotspots.length === 0 ? (
                <div className="empty-state">
                  <p>No active hotspots.</p>
                </div>
              ) : (
                hotspots.map((h, i) => (
                  <div className="hs-item" key={h.hotspot_id || i}>
                    <div className="hs-rank">{i + 1}</div>
                    <div className="hs-info">
                      <div className="hs-name">
                        {h.incident_type_name || `Type ${h.incident_type_id}`}
                      </div>
                      <div className="hs-meta">
                        {h.incident_count} incidents · {h.radius_meters}m radius
                      </div>
                    </div>
                    <span className={`risk-pill ${riskClass(h.risk_level)}`}>
                      {h.risk_level}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </>
      )}
    </Layout>
  );
}
