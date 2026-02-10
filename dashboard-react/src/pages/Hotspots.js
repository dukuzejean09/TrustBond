import React, { useState, useEffect } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import { mlAPI } from "../services/api";
import "leaflet/dist/leaflet.css";
import "../styles/Hotspots.css";

const Hotspots = () => {
  const [hotspots, setHotspots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState("");
  const [selectedSeverity, setSelectedSeverity] = useState("");

  // Rwanda center coordinates
  const rwandaCenter = [-1.9403, 29.8739];

  useEffect(() => {
    loadHotspots();
  }, [selectedCategory, selectedSeverity]);

  const loadHotspots = async () => {
    try {
      setLoading(true);
      const params = {};
      if (selectedCategory) params.category = selectedCategory;
      if (selectedSeverity) params.severity = selectedSeverity;

      const response = await mlAPI.getHotspots(params);
      setHotspots(response.data.hotspots || []);
    } catch (error) {
      console.error("Error loading hotspots:", error);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity) => {
    const colors = {
      low: "#28a745",
      medium: "#ffc107",
      high: "#fd7e14",
      critical: "#dc3545",
    };
    return colors[severity] || "#6c757d";
  };

  const getSeverityRadius = (severity, incidentCount) => {
    const baseRadius = {
      low: 15,
      medium: 25,
      high: 35,
      critical: 45,
    };
    const base = baseRadius[severity] || 20;
    return Math.min(base + (incidentCount || 0) * 2, 60);
  };

  const formatCategory = (category) => {
    if (!category) return "-";
    return category
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  const stats = {
    total: hotspots.length,
    critical: hotspots.filter((h) => h.severity === "critical").length,
    high: hotspots.filter((h) => h.severity === "high").length,
    medium: hotspots.filter((h) => h.severity === "medium").length,
    low: hotspots.filter((h) => h.severity === "low").length,
  };

  return (
    <div className="hotspots-page">
      <div className="page-header">
        <h1>
          <i className="fas fa-fire"></i> Crime Hotspots
        </h1>
        <div className="filters">
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
          >
            <option value="">All Categories</option>
            <option value="theft">Theft</option>
            <option value="assault">Assault</option>
            <option value="robbery">Robbery</option>
            <option value="fraud">Fraud</option>
            <option value="vandalism">Vandalism</option>
            <option value="domestic_violence">Domestic Violence</option>
            <option value="cybercrime">Cybercrime</option>
          </select>
          <select
            value={selectedSeverity}
            onChange={(e) => setSelectedSeverity(e.target.value)}
          >
            <option value="">All Severity</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>
      </div>

      <div className="hotspots-stats">
        <div className="stat-item total">
          <span className="stat-value">{stats.total}</span>
          <span className="stat-label">Total Hotspots</span>
        </div>
        <div className="stat-item critical">
          <span className="stat-value">{stats.critical}</span>
          <span className="stat-label">Critical</span>
        </div>
        <div className="stat-item high">
          <span className="stat-value">{stats.high}</span>
          <span className="stat-label">High</span>
        </div>
        <div className="stat-item medium">
          <span className="stat-value">{stats.medium}</span>
          <span className="stat-label">Medium</span>
        </div>
        <div className="stat-item low">
          <span className="stat-value">{stats.low}</span>
          <span className="stat-label">Low</span>
        </div>
      </div>

      <div className="map-container">
        {loading ? (
          <div className="loading-overlay">
            <i className="fas fa-spinner fa-spin"></i> Loading hotspots...
          </div>
        ) : (
          <MapContainer
            center={rwandaCenter}
            zoom={9}
            style={{ height: "100%", width: "100%" }}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {hotspots.map((hotspot, index) => (
              <CircleMarker
                key={hotspot.id || index}
                center={[
                  hotspot.latitude || -1.9403,
                  hotspot.longitude || 29.8739,
                ]}
                radius={getSeverityRadius(
                  hotspot.severity,
                  hotspot.incidentCount,
                )}
                pathOptions={{
                  color: getSeverityColor(hotspot.severity),
                  fillColor: getSeverityColor(hotspot.severity),
                  fillOpacity: 0.5,
                  weight: 2,
                }}
              >
                <Popup>
                  <div className="hotspot-popup">
                    <h4>{hotspot.district || "Unknown"}</h4>
                    <p>
                      <strong>Severity:</strong>{" "}
                      <span className={`severity ${hotspot.severity}`}>
                        {hotspot.severity}
                      </span>
                    </p>
                    <p>
                      <strong>Category:</strong>{" "}
                      {formatCategory(hotspot.category)}
                    </p>
                    <p>
                      <strong>Incidents:</strong> {hotspot.incidentCount || 0}
                    </p>
                    {hotspot.sector && (
                      <p>
                        <strong>Sector:</strong> {hotspot.sector}
                      </p>
                    )}
                    <p>
                      <strong>Risk Score:</strong>{" "}
                      {hotspot.riskScore?.toFixed(2) || "N/A"}
                    </p>
                  </div>
                </Popup>
              </CircleMarker>
            ))}
          </MapContainer>
        )}
      </div>

      <div className="legend">
        <h4>Legend</h4>
        <div className="legend-items">
          <div className="legend-item">
            <span className="legend-circle critical"></span>
            <span>Critical (Highest Risk)</span>
          </div>
          <div className="legend-item">
            <span className="legend-circle high"></span>
            <span>High Risk</span>
          </div>
          <div className="legend-item">
            <span className="legend-circle medium"></span>
            <span>Medium Risk</span>
          </div>
          <div className="legend-item">
            <span className="legend-circle low"></span>
            <span>Low Risk</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Hotspots;
