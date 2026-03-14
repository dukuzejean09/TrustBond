import { useState, useEffect, useMemo, useCallback } from "react";
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
  useMap,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";
import "./SafetyMap.css";

const STATUS_COLORS = {
  pending: "#4f8ef7",
  classified: "#34d399",
  passed: "#34d399",
  confirmed: "#34d399",
  verified: "#34d399",
  flagged: "#fb923c",
  rejected: "#f87171",
};

const STATUS_LABELS = {
  pending: "Pending",
  classified: "Classified",
  passed: "Classified",
  confirmed: "Classified",
  verified: "Classified",
  flagged: "Flagged",
  rejected: "Rejected",
};

const MUSANZE_CENTER = [-1.4975, 29.6347];

function MapZoomControls() {
  const map = useMap();
  return (
    <div className="map-zoom-controls">
      <button onClick={() => map.zoomIn()} title="Zoom in">
        +
      </button>
      <button onClick={() => map.zoomOut()} title="Zoom out">
        −
      </button>
      <button
        onClick={() => map.setView(MUSANZE_CENTER, 13)}
        title="Reset view"
      >
        ⌂
      </button>
    </div>
  );
}

export default function SafetyMap() {
  const { canSeeHotspots } = useAuth();
  const [reports, setReports] = useState([]);
  const [hotspots, setHotspots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState("classified");
  const [typeFilter, setTypeFilter] = useState("all");
  const [selectedReport, setSelectedReport] = useState(null);

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
    fillOpacity: 0.12,
  });

  const onEachBoundary = (feature, layer) => {
    const { Village, Cell, Sector } = feature.properties || {};
    if (Village) {
      layer.bindTooltip(`${Village}, ${Cell} \u2014 ${Sector}`, {
        sticky: true,
        className: "boundary-tooltip",
      });
    }
  };

  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    Promise.all([
      apiService.getPublicMapIncidents({ limit: 1000 }).catch(() => []),
      canSeeHotspots
        ? apiService.getHotspots().catch(() => [])
        : Promise.resolve([]),
    ])
      .then(([reportsData, hotspotsData]) => {
        if (cancelled) return;
        setReports(Array.isArray(reportsData) ? reportsData : []);
        setHotspots(Array.isArray(hotspotsData) ? hotspotsData : []);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message || "Failed to load data");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [canSeeHotspots]);

  const incidentTypes = useMemo(() => {
    const types = new Set();
    reports.forEach((r) => {
      if (r.incident_type_name) types.add(r.incident_type_name);
    });
    return Array.from(types).sort();
  }, [reports]);

  const filteredMarkers = useMemo(() => {
    return reports
      .filter((r) => r.latitude != null && r.longitude != null)
      .filter((r) => {
        if (statusFilter !== "all") {
          const s = String(r.rule_status || "").toLowerCase();
          if (s !== statusFilter) return false;
        }
        if (typeFilter !== "all") {
          if (r.incident_type_name !== typeFilter) return false;
        }
        return true;
      })
      .map((r) => ({
        id: r.report_id,
        lat: Number(r.latitude),
        lng: Number(r.longitude),
        type: r.incident_type_name || `Type ${r.incident_type_id}`,
        status: r.rule_status || "unknown",
        village: r.village_name || "",
        cell: r.cell_name || "",
        sector: r.sector_name || "",
        date: r.reported_at,
        description: r.description || "",
        credibilityScore: r.credibility_score,
      }));
  }, [reports, statusFilter, typeFilter]);

  const statusColor = useCallback((s) => {
    const low = String(s).toLowerCase();
    return STATUS_COLORS[low] || "#4f8ef7";
  }, []);

  const fmtDate = (s) =>
    s
      ? new Date(s).toLocaleDateString("en-US", {
          month: "short",
          day: "numeric",
          year: "numeric",
          hour: "2-digit",
          minute: "2-digit",
        })
      : "—";

  // Statistics
  const stats = useMemo(() => {
    const total = filteredMarkers.length;
    const byStatus = {};
    filteredMarkers.forEach((m) => {
      const s = String(m.status).toLowerCase();
      byStatus[s] = (byStatus[s] || 0) + 1;
    });
    return { total, byStatus };
  }, [filteredMarkers]);

  return (
    <Layout>
      <div className="safety-map-page">
        {/* Header */}
        <div className="smp-header">
          <div className="smp-header-left">
            <h2>Safety Map</h2>
            <p>
              Interactive incident map of Musanze District —{" "}
              {filteredMarkers.length} incidents plotted
            </p>
          </div>
          <Link to="/dashboard" className="smp-back-btn">
            ← Dashboard
          </Link>
        </div>

        {/* Filters bar */}
        <div className="smp-filters">
          <div className="smp-filter-group">
            <label>Status</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="all">All Statuses</option>
              <option value="classified">Classified</option>
            </select>
          </div>
          <div className="smp-filter-group">
            <label>Incident Type</label>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
            >
              <option value="all">All Types</option>
              {incidentTypes.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
          <div className="smp-stat-chips">
            <span className="smp-chip c-total">{stats.total} total</span>
            {Object.entries(stats.byStatus).map(([s, count]) => (
              <span
                key={s}
                className="smp-chip"
                style={{
                  background: `${statusColor(s)}18`,
                  color: statusColor(s),
                  borderColor: `${statusColor(s)}40`,
                }}
              >
                {count} {STATUS_LABELS[s] || s}
              </span>
            ))}
          </div>
        </div>

        {/* Map + sidebar layout */}
        <div className="smp-body">
          {/* Main map */}
          <div className="smp-map-container">
            {loading && <div className="smp-loading">Loading map data…</div>}
            {error && <div className="smp-error">{error}</div>}
            {!loading && !error && (
              <MapContainer
                center={MUSANZE_CENTER}
                zoom={13}
                style={{ height: "100%", width: "100%" }}
                scrollWheelZoom
                zoomControl={false}
              >
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                <MapZoomControls />
                {boundaries && (
                  <GeoJSON
                    data={boundaries}
                    style={boundaryStyle}
                    onEachFeature={onEachBoundary}
                  />
                )}
                {filteredMarkers.map((m) => (
                  <CircleMarker
                    key={m.id}
                    center={[m.lat, m.lng]}
                    radius={selectedReport === m.id ? 11 : 7}
                    pathOptions={{
                      color: statusColor(m.status),
                      fillColor: statusColor(m.status),
                      fillOpacity: selectedReport === m.id ? 0.95 : 0.7,
                      weight: selectedReport === m.id ? 3 : 2,
                    }}
                    eventHandlers={{
                      click: () => setSelectedReport(m.id),
                    }}
                  >
                    <Popup>
                      <div className="smp-popup">
                        <strong>{m.type}</strong>
                        <span
                          className="smp-popup-status"
                          style={{
                            background: statusColor(m.status),
                          }}
                        >
                          {m.status}
                        </span>
                        {m.village && (
                          <div className="smp-popup-loc">
                            {m.village}
                            {m.cell ? `, ${m.cell}` : ""}
                            {m.sector ? ` — ${m.sector}` : ""}
                          </div>
                        )}
                        {m.description && (
                          <div className="smp-popup-desc">
                            {m.description.slice(0, 120)}
                            {m.description.length > 120 ? "…" : ""}
                          </div>
                        )}
                        <div className="smp-popup-date">{fmtDate(m.date)}</div>
                        <Link
                          to={`/reports/${m.id}`}
                          className="smp-popup-link"
                        >
                          View full report →
                        </Link>
                      </div>
                    </Popup>
                  </CircleMarker>
                ))}
              </MapContainer>
            )}

            {/* Legend */}
            <div className="smp-legend">
              <div className="smp-legend-title">Status Legend</div>
              {Object.entries(STATUS_COLORS)
                .slice(0, 4)
                .map(([status, color]) => (
                  <div className="smp-legend-item" key={status}>
                    <span
                      className="smp-legend-dot"
                      style={{ background: color }}
                    />
                    {STATUS_LABELS[status] || status}
                  </div>
                ))}
            </div>
          </div>

          {/* Sidebar: incident list */}
          <div className="smp-sidebar">
            <div className="smp-sidebar-header">
              <h3>Incidents ({filteredMarkers.length})</h3>
            </div>
            <div className="smp-sidebar-list">
              {filteredMarkers.length === 0 ? (
                <div className="smp-sidebar-empty">
                  No incidents match the current filters.
                </div>
              ) : (
                filteredMarkers.map((m) => (
                  <div
                    key={m.id}
                    className={`smp-incident-card${selectedReport === m.id ? " selected" : ""}`}
                    onClick={() => setSelectedReport(m.id)}
                  >
                    <div className="smp-ic-header">
                      <span className="smp-ic-type">{m.type}</span>
                      <span
                        className="smp-ic-status"
                        style={{
                          background: `${statusColor(m.status)}20`,
                          color: statusColor(m.status),
                        }}
                      >
                        {m.status}
                      </span>
                    </div>
                    {m.village && (
                      <div className="smp-ic-loc">
                        {m.village}
                        {m.sector ? ` · ${m.sector}` : ""}
                      </div>
                    )}
                    <div className="smp-ic-date">{fmtDate(m.date)}</div>
                    <Link
                      to={`/reports/${m.id}`}
                      className="smp-ic-link"
                      onClick={(e) => e.stopPropagation()}
                    >
                      Details →
                    </Link>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
