import React, { useEffect, useState } from 'react';
import api from '../../api/client';
import './HotspotDetails.css';

const HotspotDetails = ({ hotspotId, wsRefreshKey }) => {
  const [hotspot, setHotspot] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentEvidenceIndex, setCurrentEvidenceIndex] = useState(0);

  useEffect(() => {
    const loadHotspotDetails = async () => {
      try {
        setLoading(true);
        const response = await api.get(`/api/v1/public/hotspots/${hotspotId}`);
        setHotspot(response);
        setError(null);
      } catch {
        setError('Failed to load hotspot details');
      } finally {
        setLoading(false);
      }
    };

    if (hotspotId) {
      loadHotspotDetails();
    } else {
      setLoading(false);
    }
  }, [hotspotId]);

  const getRiskColor = (riskLevel) => {
    switch (riskLevel) {
      case 'high': return '#dc3545';
      case 'medium': return '#fd7e14';
      case 'low': return '#28a745';
      default: return '#6c757d';
    }
  };

  const getRiskIcon = (riskLevel) => {
    switch (riskLevel) {
      case 'high': return '🔴';
      case 'medium': return '🟡';
      case 'low': return '🟢';
      default: return '⚪';
    }
  };

  const handlePrevEvidence = () => {
    if (hotspot?.evidence_files?.length > 0) {
      setCurrentEvidenceIndex((prev) => 
        prev === 0 ? hotspot.evidence_files.length - 1 : prev - 1
      );
    }
  };

  const handleNextEvidence = () => {
    if (hotspot?.evidence_files?.length > 0) {
      setCurrentEvidenceIndex((prev) => 
        prev === hotspot.evidence_files.length - 1 ? 0 : prev + 1
      );
    }
  };

  if (loading) {
    return (
      <div className="hotspot-details-loading">
        <div className="loading-spinner"></div>
        <p>Loading hotspot details...</p>
      </div>
    );
  }

  if (error || !hotspot) {
    return (
      <div className="hotspot-details-error">
        <div className="error-icon">⚠️</div>
        <h2>Error</h2>
        <p>{error || 'Hotspot not found'}</p>
        <button className="btn btn-primary" onClick={() => window.location.href = '/hotspots'}>
          Back to Hotspots
        </button>
      </div>
    );
  }

  return (
    <div className="hotspot-details-container">
      {/* Header */}
      <div className="hotspot-header">
        <button className="btn btn-back" onClick={() => window.location.href = '/hotspots'}>
          ← Back to Hotspots
        </button>
        <div className="header-content">
          <h1 className="hotspot-title">Hotspot #{hotspot.hotspot_id}</h1>
          <div className="risk-badge" style={{ backgroundColor: getRiskColor(hotspot.risk_level) }}>
            <span className="risk-icon">{getRiskIcon(hotspot.risk_level)}</span>
            <span className="risk-text">{hotspot.risk_level.toUpperCase()} RISK</span>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="hotspot-content new-layout">
        
        {/* Card 1: Hotspot Overview */}
        <div className="detail-card overview-card">
          <div className="card-header">
            <h2>📊 Hotspot Overview</h2>
          </div>
          <div className="card-content overview-grid">
            <div className="overview-section">
              <h3>Incident Details</h3>
              <div className="info-item">
                <label>Incident Type</label>
                <value>{hotspot.incident_type_name || 'Unknown'}</value>
              </div>
              <div className="info-item">
                <label>First Detected</label>
                <value>{new Date(hotspot.detected_at).toLocaleString()}</value>
              </div>
              <div className="info-item">
                <label>Total Reports</label>
                <value className="highlight">{hotspot.incident_count}</value>
              </div>
              <div className="info-item">
                <label>Time Window</label>
                <value>{hotspot.time_window_hours} hours window</value>
              </div>
            </div>

            <div className="overview-section">
              <h3>Location Information</h3>
              <div className="info-item">
                <label>Center Coordinates</label>
                <value>{hotspot.center_lat}, {hotspot.center_long}</value>
              </div>
              <div className="info-item">
                <label>Coverage Radius</label>
                <value>{hotspot.radius_meters}m</value>
              </div>
              <div className="map-placeholder map-mini">
                <div className="map-icon">🗺️</div>
                <small>Map view available in standard map view</small>
              </div>
            </div>

            <div className="overview-section full-width">
              <h3>Risk Assessment</h3>
              <div className="risk-level-display">
                <div className="risk-circle" style={{ backgroundColor: getRiskColor(hotspot.risk_level) }}>
                  <span className="risk-emoji">{getRiskIcon(hotspot.risk_level)}</span>
                </div>
                <div className="risk-info">
                  <h4>{hotspot.risk_level.toUpperCase()} RISK</h4>
                  <p>{
                    hotspot.risk_level === 'high' ? 'High incident density and strong credibility indicators. Priority response needed.' :
                    hotspot.risk_level === 'medium' ? 'Moderate density. Requires active monitoring.' :
                    'Provisional cluster. Requires further observation.'
                  }</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Card 2: Evidence Carousel */}
        <div className="detail-card evidence-card">
          <div className="card-header">
            <h2>📁 Evidence Vault ({hotspot.evidence_files?.length || 0} Files)</h2>
          </div>
          <div className="card-content">
            {hotspot.evidence_files && hotspot.evidence_files.length > 0 ? (
              <div className="evidence-carousel">
                <button className="carousel-btn left-btn" onClick={handlePrevEvidence}>&lt;</button>
                
                <div className="carousel-content">
                  <div className="carousel-slide">
                    <div className="carousel-header">
                      <span className="file-type-badge">
                        {hotspot.evidence_files[currentEvidenceIndex].file_type === 'photo' ? '📷 PHOTO' : '🎥 VIDEO'}
                      </span>
                      <span className="file-indexer">
                        {currentEvidenceIndex + 1} of {hotspot.evidence_files.length}
                      </span>
                    </div>

                    <div className="carousel-media">
                      {hotspot.evidence_files[currentEvidenceIndex].file_type === 'photo' ? (
                        <img 
                          src={hotspot.evidence_files[currentEvidenceIndex].cloudinary_url || hotspot.evidence_files[currentEvidenceIndex].file_url} 
                          alt="Evidence Capture"
                          onError={(e) => {
                            e.target.style.display = 'none';
                            e.target.nextSibling.style.display = 'flex';
                          }}
                        />
                      ) : (
                        <video controls src={hotspot.evidence_files[currentEvidenceIndex].cloudinary_url || hotspot.evidence_files[currentEvidenceIndex].file_url} />
                      )}
                      <div className="media-fallback" style={{display: 'none'}}>
                        📷 Media not available
                      </div>
                    </div>

                    <div className="carousel-footer">
                      <div className="detail-row">
                        <label>Date Captured:</label>
                        <value>{hotspot.evidence_files[currentEvidenceIndex].captured_at ? new Date(hotspot.evidence_files[currentEvidenceIndex].captured_at).toLocaleString() : 'Unknown'}</value>
                      </div>
                      <div className="detail-row">
                        <label>File Size:</label>
                        <value>{hotspot.evidence_files[currentEvidenceIndex].file_size ? `${(hotspot.evidence_files[currentEvidenceIndex].file_size / 1024 / 1024).toFixed(2)} MB` : 'Unknown'}</value>
                      </div>
                      {hotspot.evidence_files[currentEvidenceIndex].quality_label && (
                        <div className="detail-row">
                          <label>AI Quality Evaluation:</label>
                          <value className={`quality-badge quality-${hotspot.evidence_files[currentEvidenceIndex].quality_label}`}>
                            {hotspot.evidence_files[currentEvidenceIndex].quality_label.toUpperCase()}
                          </value>
                        </div>
                      )}
                      {hotspot.evidence_files[currentEvidenceIndex].duration && (
                        <div className="detail-row">
                          <label>Clip Duration:</label>
                          <value>{hotspot.evidence_files[currentEvidenceIndex].duration}s</value>
                        </div>
                      )}
                      {hotspot.evidence_files[currentEvidenceIndex].media_latitude && hotspot.evidence_files[currentEvidenceIndex].media_longitude && (
                        <div className="detail-row">
                          <label>GPS Location:</label>
                          <value>{parseFloat(hotspot.evidence_files[currentEvidenceIndex].media_latitude).toFixed(6)}, {parseFloat(hotspot.evidence_files[currentEvidenceIndex].media_longitude).toFixed(6)}</value>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                <button className="carousel-btn right-btn" onClick={handleNextEvidence}>&gt;</button>
              </div>
            ) : (
              <div className="no-evidence">
                <div className="no-evidence-icon">📁</div>
                <p>No evidence files available</p>
                <small>Evidence files will appear here when reports in this area contain photos or videos</small>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default HotspotDetails;
