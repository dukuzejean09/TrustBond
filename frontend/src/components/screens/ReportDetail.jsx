import React, { useEffect, useState } from 'react';
import api from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import { formatLocalDateTime } from '../../utils/dateTime';

const friendlyFlagReason = (reason) => {
  const m = {
    evidence_time_mismatch: 'Evidence was captured too long before the report was submitted.',
    stale_live_capture_timestamp: 'Live-capture evidence timestamp appears stale.',
    incident_description_mismatch: 'Description appears inconsistent with the selected incident type.',
    gibberish_description: 'Description looks meaningless or spammy and needs manual review.',
    ai_suspicious_review: 'AI marked this report as suspicious and requires human review.',
    ai_uncertain_review: 'AI result is uncertain and requires manual review.',
    ai_detected_fake: 'AI detected possible fake/manipulated evidence.',
    device_burst_reporting: 'Device submitted too many reports in a short period.',
    duplicate_description_recent: 'Description was repeatedly submitted from the same device.',
    no_description_with_evidence: 'Evidence was uploaded without enough description context.',
    minimal_description: 'Description is too short for reliable triage.',
    high_severity_incident: 'High-severity incident automatically requires manual review.',
  };
  if (!reason) return '';
  return m[reason] || reason.replaceAll('_', ' ');
};

// Verification helper functions
const isReportVerified = (report, mlPrediction) => {
  const status = (report.rule_status || '').toLowerCase();
  const hasOfficerConfirmed = report.reviews?.some(rv => (rv.decision || '').toLowerCase() === 'confirmed');
  
  if (hasOfficerConfirmed) {
    return true; // Officer-verified
  }
  
  if (status === 'passed') {
    // Check ML confidence
    if (mlPrediction && mlPrediction.trust_score !== null && mlPrediction.trust_score !== undefined) {
      const mlConfidence = parseFloat(mlPrediction.trust_score) || 0;
      return mlConfidence >= 80; // Auto-verified if ML confidence >= 80
    }
  }
  
  return false; // Not verified
};

const getVerificationStatus = (report, mlPrediction) => {
  const status = (report.rule_status || '').toLowerCase();
  const hasOfficerConfirmed = report.reviews?.some(rv => (rv.decision || '').toLowerCase() === 'confirmed');
  
  if (hasOfficerConfirmed) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '11px' }}>
        <span style={{ color: '#4caf50', fontWeight: 600 }}>Officer verified</span>
        <span style={{ color: '#666' }}>
          — Confirmed by {report.reviews.find(rv => (rv.decision || '').toLowerCase() === 'confirmed')?.reviewer_name || 'officer'}
        </span>
      </div>
    );
  }
  
  if (status === 'passed') {
    if (mlPrediction && mlPrediction.trust_score !== null && mlPrediction.trust_score !== undefined) {
      const mlConfidence = parseFloat(mlPrediction.trust_score) || 0;
      
      if (mlConfidence >= 80) {
        return (
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '11px' }}>
            <span style={{ color: '#4caf50', fontWeight: 600 }}>Auto-verified</span>
            <span style={{ color: '#666' }}>— ML confidence: {mlConfidence.toFixed(1)}%</span>
          </div>
        );
      } else {
        return (
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '11px' }}>
            <span style={{ color: '#ff9800', fontWeight: 600 }}>Low ML Confidence</span>
            <span style={{ color: '#666' }}>- Current: {mlConfidence.toFixed(1)}% (needs ≥80%)</span>
          </div>
        );
      }
    } else {
      return (
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '11px' }}>
          <span style={{ color: '#ff9800', fontWeight: 600 }}>No ML Analysis</span>
          <span style={{ color: '#666' }}>- Requires officer verification</span>
        </div>
      );
    }
  }
  
  if (status === 'pending') {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '11px' }}>
        <span style={{ color: '#ff9800', fontWeight: 600 }}>Pending Review</span>
        <span style={{ color: '#666' }}>- Needs officer assignment and confirmation</span>
      </div>
    );
  }
  
  if (status === 'flagged' || status === 'rejected') {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '11px' }}>
        <span style={{ color: '#f44336', fontWeight: 600 }}>{status === 'flagged' ? 'Flagged' : 'Rejected'}</span>
        <span style={{ color: '#666' }}>- Cannot contribute to hotspots</span>
      </div>
    );
  }
  
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '11px' }}>
      <span style={{ color: '#9e9e9e', fontWeight: 600 }}>Unknown Status</span>
      <span style={{ color: '#666' }}>- Status unclear</span>
    </div>
  );
};

const getVerificationRequirements = (report, mlPrediction) => {
  const status = (report.rule_status || '').toLowerCase();
  const hasOfficerConfirmed = report.reviews?.some(rv => (rv.decision || '').toLowerCase() === 'confirmed');
  
  if (hasOfficerConfirmed) {
    return null; // Already verified
  }
  
  if (status === 'passed') {
    if (mlPrediction && mlPrediction.trust_score !== null && mlPrediction.trust_score !== undefined) {
      const mlConfidence = parseFloat(mlPrediction.trust_score) || 0;
      
      if (mlConfidence < 80) {
        return (
          <div>
            <div style={{ marginBottom: '4px' }}>ML confidence too low ({mlConfidence.toFixed(1)}% &lt; 80%)</div>
            <div style={{ marginBottom: '4px' }}><strong>Option 1:</strong> Assign to officer for confirmation</div>
            <div><strong>Option 2:</strong> Wait for higher ML confidence (≥80%)</div>
          </div>
        );
      }
    } else {
      return (
        <div>
          <div style={{ marginBottom: '4px' }}>No ML analysis available</div>
          <div><strong>Required:</strong> Assign to officer for manual verification</div>
        </div>
      );
    }
  }
  
  if (status === 'pending') {
    return (
      <div>
        <div style={{ marginBottom: '4px' }}>Report status is "pending" (needs officer review)</div>
        <div><strong>Required:</strong> Assign to officer and get confirmation</div>
      </div>
    );
  }
  
  if (status === 'flagged' || status === 'rejected') {
    return (
      <div>
        <div style={{ marginBottom: '4px' }}>Report is {status} (cannot be verified)</div>
        <div><strong>Result:</strong> This report cannot contribute to hotspots</div>
      </div>
    );
  }
  
  return (
    <div>
      <div style={{ marginBottom: '4px' }}>Verification status unclear</div>
      <div><strong>Required:</strong> Assign to officer for review</div>
    </div>
  );
};

const ReportDetail = ({ goToScreen, openModal, reportId, wsRefreshKey }) => {
  const { user: me } = useAuth();
  const role = me?.role || 'officer';
  const canTriage = role === 'admin' || role === 'supervisor';

  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [savingDecision, setSavingDecision] = useState('');
  const [mlPrediction, setMlPrediction] = useState(null);
  const [mlLoading, setMlLoading] = useState(false);
  const [relatedReports, setRelatedReports] = useState([]);
  const [relatedLoading, setRelatedLoading] = useState(false);

  useEffect(() => {
    if (!reportId) {
      setError('No report selected.');
      setLoading(false);
      return;
    }
    let mounted = true;
    setLoading(true);

    const fetchReportData = () => {
      api
        .get(`/api/v1/reports/${reportId}`)
        .then((res) => {
          if (!mounted) return;
          setReport(res);
          setLoading(false);
        })
        .catch((err) => {
          if (!mounted) return;
          setError(err?.data?.detail || err?.message || 'Failed to load report.');
          setLoading(false);
        });
    };

    fetchReportData();

    return () => {
      mounted = false;
    };
  }, [reportId, wsRefreshKey]);

  // Load ML prediction for this report
  useEffect(() => {
    if (!report || !report.report_id || !report.device_id) return;
    let cancelled = false;
    setMlLoading(true);
    api
      .get(
        `/api/v1/devices/reports/${report.report_id}/prediction?device_id=${report.device_id}`,
      )
      .then((res) => {
        if (cancelled) return;
        setMlPrediction(res);
      })
      .catch(() => {
        if (cancelled) return;
        setMlPrediction(null);
      })
      .finally(() => {
        if (!cancelled) setMlLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [report]);

  // Load related reports
  useEffect(() => {
    if (!report || !report.report_id) return;
    let cancelled = false;
    setRelatedLoading(true);
    api
      .get(`/api/v1/reports/${report.report_id}/related`)
      .then((res) => {
        if (cancelled) return;
        setRelatedReports(res || []);
      })
      .catch(() => {
        if (cancelled) return;
        setRelatedReports([]);
      })
      .finally(() => {
        if (!cancelled) setRelatedLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [report]);

  const reload = async () => {
    if (!reportId) return;
    setLoading(true);
    setError('');
    try {
      const res = await api.get(`/api/v1/reports/${reportId}`);
      setReport(res);
    } catch (err) {
      setError(err?.data?.detail || err?.message || 'Failed to load report.');
    } finally {
      setLoading(false);
    }
  };

  const submitReview = async (decision) => {
    if (!reportId) return;
    setSavingDecision(decision);
    setError('');
    try {
      await api.post(`/api/v1/reports/${reportId}/reviews`, {
        decision,
        review_note: '',
      });
      await reload();
    } catch (e) {
      setError(e?.message || 'Failed to submit review.');
    } finally {
      setSavingDecision('');
    }
  };

  if (loading) {
    return (
      <div style={{ padding: 16, fontSize: 13, color: 'var(--muted)' }}>
        Loading report…
      </div>
    );
  }

  if (error || !report) {
    return (
      <div style={{ padding: 16 }}>
        <button
          className="btn btn-outline btn-sm"
          onClick={() => goToScreen('reports', 1)}
        >
          Back to Reports
        </button>
        <div style={{ marginTop: 12, color: 'var(--danger)', fontSize: 13 }}>
          {error || 'Report not found.'}
        </div>
      </div>
    );
  }

  const idLabel = report.report_number || String(report.report_id).slice(0, 8);
  const deviceShort = report.device_id ? String(report.device_id).slice(0, 4) : 'DEV';
  const trustScore = report.trust_score ?? 0;
  const trustFactors = report.trust_factors || {};
  const createdAt = formatLocalDateTime(report.reported_at);
  const assignments = report.assignments || [];
  const hasCase = report.case_id; // Assuming case_id is available
  
  // Status configuration
  const getStatusConfig = (status) => {
    const configs = {
      pending: { color: 'b-yellow', text: 'Pending Review' },
      passed: { color: 'b-green', text: 'Verified' },
      verified: { color: 'b-green', text: 'Verified' },
      flagged: { color: 'b-red', text: 'Flagged' },
      rejected: { color: 'b-red', text: 'Rejected' },
    };
    return configs[status] || { color: 'b-gray', text: 'Unknown' };
  };

  const statusConfig = getStatusConfig(report.status || report.rule_status);

  return (
    <>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          marginBottom: '16px',
          flexWrap: 'wrap',
        }}
      >
        <button
          className="btn btn-outline btn-sm"
          onClick={() => goToScreen('reports', 1)}
        >
          Back to Reports
        </button>
        <div
          style={{
            fontFamily: '"Syne", sans-serif',
            fontWeight: 800,
            fontSize: '18px',
          }}
        >
          Report {idLabel}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span
            className={`badge ${statusConfig.color}`}
            style={{ fontSize: '12px', padding: '4px 8px' }}
          >
            {statusConfig.text}
          </span>
          {hasCase && (
            <span className="badge b-blue" style={{ fontSize: '12px', padding: '4px 8px' }}>
              Linked to case
            </span>
          )}
        </div>
        <div
          style={{
            marginLeft: 'auto',
            display: 'flex',
            gap: '6px',
            flexWrap: 'wrap',
          }}
        >
          {canTriage && (
            <>
              {/* Review Status Buttons */}
              {report.status === 'pending' && (
                <>
                  <button
                    className="btn btn-success btn-sm"
                    onClick={() => submitReview('confirmed')}
                    disabled={!!savingDecision}
                    style={{ display: 'flex', alignItems: 'center', gap: 4 }}
                  >
                    {savingDecision === 'confirmed' ? 'Confirming…' : 'Verify report'}
                  </button>
                  <button
                    className="btn btn-danger btn-sm"
                    onClick={() => submitReview('rejected')}
                    disabled={!!savingDecision}
                    style={{ display: 'flex', alignItems: 'center', gap: 4 }}
                  >
                    {savingDecision === 'rejected' ? 'Flagging…' : 'Flag report'}
                  </button>
                </>
              )}
              
              {/* Already Reviewed Status */}
              {report.status !== 'pending' && (
                <button
                  className="btn btn-outline btn-sm"
                  disabled
                  style={{ display: 'flex', alignItems: 'center', gap: 4 }}
                >
                  Already {statusConfig.text.toLowerCase()}
                </button>
              )}

              {/* Assignment and Case Management */}
              <button
                className="btn btn-primary btn-sm"
                onClick={() => openModal('assign')}
                style={{ display: 'flex', alignItems: 'center', gap: 4 }}
              >
                Assign officer
              </button>
              
              {!hasCase ? (
                <button
                  className="btn btn-success btn-sm"
                  onClick={() => openModal('newCase')}
                  style={{ display: 'flex', alignItems: 'center', gap: 4 }}
                >
                  Create case
                </button>
              ) : (
                <button
                  className="btn btn-info btn-sm"
                  onClick={() => goToScreen('case-detail', report.case_id)}
                  style={{ display: 'flex', alignItems: 'center', gap: 4 }}
                >
                  View case
                </button>
              )}
              
              <button
                className="btn btn-warn btn-sm"
                onClick={() => openModal('linkCase')}
                style={{ display: 'flex', alignItems: 'center', gap: 4 }}
              >
                Link to existing case
              </button>
            </>
          )}
        </div>
      </div>

      <div className="detail-layout">
        <div className="detail-col">
          <div className="card">
            <div className="card-header">
              <div className="card-title">Incident Details</div>
            </div>
            {report.flag_reason && (
              <div
                style={{
                  margin: '0 14px 12px',
                  padding: '10px 12px',
                  borderRadius: 8,
                  background: 'rgba(255, 152, 0, 0.12)',
                  border: '1px solid rgba(255, 152, 0, 0.35)',
                  color: 'var(--text)',
                  fontSize: 12,
                }}
              >
                <strong>Review reason:</strong> {friendlyFlagReason(report.flag_reason)}
              </div>
            )}
            <div className="detail-grid">
              <div className="detail-field">
                <div className="dfl">Incident Type</div>
                <div className="dfv" style={{ color: 'var(--danger)' }}>
                  {report.incident_type_name || '—'}
                </div>
              </div>
              <div className="detail-field">
                <div className="dfl">Location</div>
                <div className="dfv">
                  {report.incident_village_name ||
                    report.village_name ||
                    '—'}
                </div>
              </div>
              <div className="detail-field">
                <div className="dfl">GPS Coords</div>
                <div
                  className="dfv"
                  style={{ fontSize: '11px', fontFamily: 'monospace' }}
                >
                  {report.latitude}, {report.longitude}
                </div>
              </div>
              <div className="detail-field">
                <div className="dfl">GPS Accuracy</div>
                <div className="dfv" style={{ fontSize: '12px' }}>
                  {report.gps_accuracy != null ? `${Number(report.gps_accuracy).toFixed(1)}m` : '—'}
                </div>
              </div>
              <div className="detail-field">
                <div className="dfl">Submitted At</div>
                <div className="dfv" style={{ fontSize: '12px' }}>
                  {createdAt}
                </div>
              </div>
              <div className="detail-field">
                <div className="dfl">Device</div>
                <div
                  className="dfv"
                  style={{ fontSize: '11px', fontFamily: 'monospace' }}
                >
                  {deviceShort}
                </div>
              </div>
            </div>
            <div
              style={{
                background: 'var(--surface2)',
                borderRadius: 'var(--rs)',
                padding: '11px',
                border: '1px solid var(--border2)',
              }}
            >
              <div
                style={{
                  fontSize: '10px',
                  color: 'var(--muted)',
                  marginBottom: '5px',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                }}
              >
                Description
              </div>
              <div style={{ fontSize: '12px', lineHeight: 1.6 }}>
                {report.description || 'No description.'}
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <div className="card-title">Reporter Context</div>
            </div>
            <div style={{ padding: '10px 14px', fontSize: 12 }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 10 }}>
                <div>
                  <div style={{ fontSize: 10, color: 'var(--muted)', fontWeight: 800, textTransform: 'uppercase' }}>Context tags</div>
                  <div style={{ marginTop: 6, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    {(report.context_tags || []).length ? (
                      (report.context_tags || []).map((t) => (
                        <span key={t} className="badge b-gray" style={{ fontSize: 10 }}>
                          {t}
                        </span>
                      ))
                    ) : (
                      <span style={{ color: 'var(--muted)' }}>—</span>
                    )}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: 10, color: 'var(--muted)', fontWeight: 800, textTransform: 'uppercase' }}>Motion</div>
                  <div style={{ marginTop: 6, color: 'var(--text)' }}>
                    Level: {report.motion_level || '—'}
                    <div style={{ marginTop: 4, color: 'var(--muted)' }}>
                      Speed: {report.movement_speed != null ? `${Number(report.movement_speed).toFixed(2)} m/s` : '—'}
                      {' · '}
                      Stationary: {report.was_stationary == null ? '—' : (report.was_stationary ? 'Yes' : 'No')}
                    </div>
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: 10, color: 'var(--muted)', fontWeight: 800, textTransform: 'uppercase' }}>Client metadata</div>
                  <div style={{ marginTop: 6, color: 'var(--muted)' }}>
                    App: <span style={{ color: 'var(--text)' }}>{report.app_version || '—'}</span>
                    <div style={{ marginTop: 4 }}>
                      Network: <span style={{ color: 'var(--text)' }}>{report.network_type || '—'}</span>
                      {' · '}
                      Battery: <span style={{ color: 'var(--text)' }}>{report.battery_level != null ? `${Number(report.battery_level).toFixed(0)}%` : '—'}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Verification Status Card */}
          <div className="card">
            <div className="card-header">
              <div className="card-title">Hotspot Verification Status</div>
              <span className={`badge ${isReportVerified(report, mlPrediction) ? 'b-green' : 'b-orange'}`}>
                {isReportVerified(report, mlPrediction) ? 'Verified' : 'Needs verification'}
              </span>
            </div>
            <div style={{ padding: '12px' }}>
              <div style={{ marginBottom: '12px' }}>
                <div style={{ fontSize: '12px', fontWeight: 600, marginBottom: '6px', color: 'var(--text)' }}>
                  Current Status:
                </div>
                {getVerificationStatus(report, mlPrediction)}
              </div>
              
              {!isReportVerified(report, mlPrediction) && (
                <div style={{ 
                  background: 'rgba(255, 152, 0, 0.1)', 
                  border: '1px solid rgba(255, 152, 0, 0.3)', 
                  borderRadius: '6px', 
                  padding: '10px' 
                }}>
                  <div style={{ fontSize: '11px', fontWeight: 600, marginBottom: '6px', color: '#f57c00' }}>
                    Requirements for hotspot eligibility:
                  </div>
                  <div style={{ fontSize: '11px', lineHeight: 1.5, color: '#666' }}>
                    {getVerificationRequirements(report, mlPrediction)}
                  </div>
                </div>
              )}
              
              {isReportVerified(report, mlPrediction) && (
                <div style={{ 
                  background: 'rgba(76, 175, 80, 0.1)', 
                  border: '1px solid rgba(76, 175, 80, 0.3)', 
                  borderRadius: '6px', 
                  padding: '10px' 
                }}>
                  <div style={{ fontSize: '11px', color: '#2e7d32' }}>
                    This report meets verification requirements and can contribute to hotspots.
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <div className="card-title">Evidence Attachments</div>
              <span className="badge b-blue">
                {report.evidence_files?.length || 0} files
              </span>
            </div>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
                gap: '20px',
                padding: '10px 0',
              }}
            >
              {(report.evidence_files || []).map((ef) => (
                <div
                  key={ef.evidence_id}
                  style={{
                    background: 'white',
                    borderRadius: '12px',
                    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)',
                    overflow: 'hidden',
                    border: '1px solid #e8e8e8',
                    transition: 'transform 0.3s ease, box-shadow 0.3s ease',
                    cursor: 'pointer',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateY(-4px)';
                    e.currentTarget.style.boxShadow = '0 8px 24px rgba(0, 0, 0, 0.12)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.08)';
                  }}
                >
                  {/* Media Container */}
                  <div style={{ position: 'relative', background: '#f8f9fa' }}>
                    {ef.file_type === 'photo' ? (
                      <>
                        <img
                          src={ef.cloudinary_url || ef.file_url}
                          alt="Evidence photo"
                          style={{
                            width: '100%',
                            height: '280px',
                            objectFit: 'cover',
                            display: 'block',
                          }}
                          onError={(e) => {
                            e.target.style.display = 'none';
                            e.target.nextSibling.style.display = 'flex';
                          }}
                        />
                        {/* Fallback */}
                        <div
                          style={{
                            display: 'none',
                            height: '280px',
                            alignItems: 'center',
                            justifyContent: 'center',
                            flexDirection: 'column',
                            background: '#f8f9fa',
                            color: '#666',
                          }}
                        >
                          <div style={{ fontSize: '48px', marginBottom: '8px' }}>Image</div>
                          <div style={{ fontSize: '14px' }}>Image not available</div>
                        </div>
                      </>
                    ) : (
                      <div style={{ position: 'relative' }}>
                        <video
                          controls
                          style={{
                            width: '100%',
                            height: '280px',
                            objectFit: 'cover',
                            display: 'block',
                          }}
                        >
                          <source src={ef.cloudinary_url || ef.file_url} type="video/mp4" />
                          Your browser does not support the video tag.
                        </video>
                      </div>
                    )}
                    
                    {/* Type Badge */}
                    <div
                      style={{
                        position: 'absolute',
                        top: '12px',
                        left: '12px',
                        background: 'rgba(0, 0, 0, 0.7)',
                        color: 'white',
                        padding: '4px 8px',
                        borderRadius: '6px',
                        fontSize: '11px',
                        fontWeight: '600',
                        backdropFilter: 'blur(4px)',
                      }}
                    >
                      {ef.file_type === 'photo' ? 'Photo' : 'Video'}
                    </div>
                    
                    {/* Quality Badge */}
                    {ef.ai_quality_label && (
                      <div
                        style={{
                          position: 'absolute',
                          top: '12px',
                          right: '12px',
                          background: ef.ai_quality_label === 'good' ? '#28a745' : 
                                     ef.ai_quality_label === 'fair' ? '#fd7e14' : '#dc3545',
                          color: 'white',
                          padding: '4px 8px',
                          borderRadius: '6px',
                          fontSize: '10px',
                          fontWeight: '600',
                          textTransform: 'uppercase',
                        }}
                      >
                        {ef.ai_quality_label}
                      </div>
                    )}
                  </div>
                  
                  {/* Content Section */}
                  <div style={{ padding: '16px' }}>
                    {/* File Info */}
                    <div style={{ marginBottom: '12px' }}>
                      <div style={{ fontSize: '13px', color: '#666', marginBottom: '4px' }}>
                        File Size: {ef.file_size ? `${(ef.file_size / 1024 / 1024).toFixed(2)} MB` : 'Unknown'}
                      </div>
                      {ef.duration && (
                        <div style={{ fontSize: '13px', color: '#666', marginBottom: '4px' }}>
                          Duration: {ef.duration}s
                        </div>
                      )}
                      <div style={{ fontSize: '12px', color: '#999' }}>
                        {formatLocalDateTime(ef.uploaded_at)}
                      </div>
                    </div>
                    
                    {/* Location Info */}
                    {ef.media_latitude && ef.media_longitude && (
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px', 
                        marginBottom: '12px',
                        fontSize: '12px',
                        color: '#666'
                      }}>
                        <span>
                          {ef.media_latitude != null && ef.media_longitude != null
                            ? `${parseFloat(ef.media_latitude).toFixed(6)}, ${parseFloat(ef.media_longitude).toFixed(6)}`
                            : 'Location not available'
                          }
                        </span>
                      </div>
                    )}
                    
                    {/* AI Analysis */}
                    {(ef.ai_quality_label || ef.blur_score || ef.tamper_score) && (
                      <div style={{ 
                        padding: '8px 0', 
                        borderTop: '1px solid #f0f0f0',
                        marginTop: '8px'
                      }}>
                        <div style={{ fontSize: '11px', fontWeight: '600', color: '#333', marginBottom: '4px' }}>
                          AI Analysis
                        </div>
                        {typeof ef.blur_score !== 'undefined' && ef.blur_score !== null && (
                          <div style={{ fontSize: '11px', color: '#666', marginBottom: '2px' }}>
                            Blur Score: {Number(ef.blur_score).toFixed(2)}
                          </div>
                        )}
                        {typeof ef.tamper_score !== 'undefined' && ef.tamper_score !== null && (
                          <div style={{ fontSize: '11px', color: '#666' }}>
                            Tamper Score: {Number(ef.tamper_score).toFixed(2)}
                          </div>
                        )}
                      </div>
                    )}
                    
                    {/* Live Capture Badge */}
                    {ef.is_live_capture && (
                      <div style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px',
                        background: '#e3f2fd',
                        color: '#1976d2',
                        padding: '4px 8px',
                        borderRadius: '4px',
                        fontSize: '11px',
                        fontWeight: '600',
                        marginTop: '8px'
                      }}>
                        <span>Live Capture</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {(!report.evidence_files ||
                report.evidence_files.length === 0) && (
                <div
                  style={{ fontSize: '12px', color: 'var(--muted)' }}
                >
                  No evidence uploaded.
                </div>
              )}
            </div>
          </div>

          {assignments.length > 0 && (
            <div className="card">
              <div className="card-header">
                <div className="card-title">Assignments</div>
                <span className="badge b-blue">
                  {assignments.length} active
                </span>
              </div>
              <div
                style={{
                  display: 'grid',
                  gap: '8px',
                }}
              >
                {assignments.map((a) => {
                  const isMine =
                    me?.police_user_id &&
                    a.police_user_id === me.police_user_id;
                  const statusBadge =
                    a.status === 'closed'
                      ? 'b-green'
                      : a.status === 'resolved'
                      ? 'b-green'
                      : a.status === 'investigating'
                      ? 'b-blue'
                      : 'b-orange';
                  const priorityBadge =
                    a.priority === 'high'
                      ? 'b-red'
                      : a.priority === 'medium'
                      ? 'b-orange'
                      : 'b-gray';
                  return (
                    <div
                      key={a.assignment_id}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '12px',
                        borderRadius: 'var(--rs)',
                        border: '1px solid var(--border2)',
                        background: isMine
                          ? 'rgba(79, 142, 247, 0.06)'
                          : 'var(--surface2)',
                        fontSize: '12px',
                      }}
                    >
                      <div style={{ flex: 1 }}>
                        <div
                          style={{
                            fontWeight: 600,
                            marginBottom: 4,
                            display: 'flex',
                            alignItems: 'center',
                            gap: 8,
                          }}
                        >
                          {a.officer_name || 'Officer'}
                          {isMine && (
                            <span
                              className="badge b-blue"
                              style={{ fontSize: '10px', padding: '2px 6px' }}
                            >
                              YOU
                            </span>
                          )}
                        </div>
                        
                        {/* Station and Badge Information */}
                        <div style={{ display: 'flex', gap: 12, marginBottom: 4, fontSize: '11px', color: 'var(--muted)' }}>
                          {a.badge_number && (
                            <span>Badge: {a.badge_number}</span>
                          )}
                          {a.station_name && (
                            <span>Station: {a.station_name}</span>
                          )}
                          {a.role && (
                            <span>Role: {a.role}</span>
                          )}
                        </div>
                        
                        {/* Assignment Timeline */}
                        <div style={{ fontSize: '11px', color: 'var(--muted)' }}>
                          Assigned: {formatLocalDateTime(a.assigned_at)}
                          {a.completed_at && (
                            <div style={{ marginTop: 2 }}>
                              Completed: {formatLocalDateTime(a.completed_at)}
                            </div>
                          )}
                        </div>
                        
                        {/* Assignment Note */}
                        {a.assignment_note && (
                          <div style={{ 
                            marginTop: 8, 
                            padding: '8px', 
                            background: 'rgba(255, 152, 0, 0.1)', 
                            border: '1px solid rgba(255, 152, 0, 0.3)', 
                            borderRadius: '4px',
                            fontSize: '11px'
                          }}>
                            <div style={{ fontWeight: 600, marginBottom: 2, color: '#f57c00' }}>
                              Assignment Note:
                            </div>
                            <div style={{ color: '#666', lineHeight: 1.4 }}>
                              {a.assignment_note}
                            </div>
                          </div>
                        )}
                      </div>
                      
                      <div
                        style={{
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'flex-end',
                          gap: 6,
                        }}
                      >
                        <span
                          className={`badge ${priorityBadge}`}
                          style={{ fontSize: '10px', textTransform: 'uppercase' }}
                        >
                          {a.priority} priority
                        </span>
                        <span
                          className={`badge ${statusBadge}`}
                          style={{ fontSize: '10px', textTransform: 'capitalize' }}
                        >
                          {a.status}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        <div className="detail-col">
          <div className="card">
            <div className="card-header">
              <div className="card-title">Trust Scores</div>
            </div>
            <div style={{ marginBottom: '12px' }}>
              {/* Report-level ML trust */}
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  marginBottom: '4px',
                }}
              >
                <span
                  style={{ fontSize: '11px', color: 'var(--muted)' }}
                >
                  Report Trust Score
                </span>
                <span
                  style={{
                    fontFamily: '"Syne", sans-serif',
                    fontWeight: 800,
                    fontSize: '17px',
                    color: 'var(--success)',
                  }}
                >
                  {mlPrediction
                    ? Math.round(mlPrediction.trust_score ?? 0)
                    : '—'}
                </span>
              </div>
              <div className="prog-bar" style={{ marginBottom: '8px' }}>
                <div
                  className="prog-fill"
                  style={{
                    width: `${
                      mlPrediction
                        ? Math.max(
                            0,
                            Math.min(
                              100,
                              mlPrediction.trust_score ?? 0,
                            ),
                          )
                        : 0
                    }%`,
                    background: 'var(--success)',
                  }}
                ></div>
              </div>

              {/* Device trust (from DB) */}
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  marginBottom: '4px',
                }}
              >
                <span
                  style={{ fontSize: '11px', color: 'var(--muted)' }}
                >
                  Device Trust Score
                </span>
                <span
                  style={{
                    fontFamily: '"Syne", sans-serif',
                    fontWeight: 800,
                    fontSize: '17px',
                    color: 'var(--success)',
                  }}
                >
                  {Math.round(trustScore)}
                </span>
              </div>
              <div className="prog-bar">
                <div
                  className="prog-fill"
                  style={{
                    width: `${Math.max(
                      0,
                      Math.min(100, trustScore),
                    )}%`,
                    background: 'var(--success)',
                  }}
                ></div>
              </div>
              {mlLoading && (
                <div
                  style={{
                    fontSize: '10px',
                    color: 'var(--muted)',
                    marginTop: 6,
                  }}
                >
                  Loading ML prediction…
                </div>
              )}
              {mlPrediction && !mlLoading && (
                <div
                  style={{
                    marginTop: 6,
                    fontSize: '10px',
                    color: 'var(--muted)',
                  }}
                >
                  <div>
                    Label:{' '}
                    <strong>{mlPrediction.prediction_label}</strong>{' '}
                    · Confidence{' '}
                    {Math.round((mlPrediction.confidence ?? 0) * 100)}%
                  </div>
                  <div>
                    Model: {mlPrediction.model_version}{' '}
                    {mlPrediction.evaluated_at &&
                      `· ${formatLocalDateTime(mlPrediction.evaluated_at)}`}
                  </div>
                </div>
              )}

              <div style={{ marginTop: 12 }}>
                <div style={{ fontSize: '12px', fontWeight: 800, marginBottom: 8 }}>
                  Credibility Breakdown
                </div>
                {trustFactors && Object.keys(trustFactors).length > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ fontSize: '11px', color: 'var(--muted)' }}>Content score</span>
                      <span style={{ fontSize: '11px', fontWeight: 800 }}>
                        {trustFactors.content_score ?? '—'}
                      </span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ fontSize: '11px', color: 'var(--muted)' }}>Location score</span>
                      <span style={{ fontSize: '11px', fontWeight: 800 }}>
                        {trustFactors.location_score ?? '—'}
                      </span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ fontSize: '11px', color: 'var(--muted)' }}>Cluster score</span>
                      <span style={{ fontSize: '11px', fontWeight: 800 }}>
                        {trustFactors.cluster_score ?? '—'}
                      </span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ fontSize: '11px', color: 'var(--muted)' }}>User behavior score</span>
                      <span style={{ fontSize: '11px', fontWeight: 800 }}>
                        {trustFactors.user_behavior_score ?? '—'}
                      </span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ fontSize: '11px', color: 'var(--muted)' }}>Community net votes</span>
                      <span style={{ fontSize: '11px', fontWeight: 800 }}>
                        {trustFactors.community_net_votes ?? '—'}
                      </span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ fontSize: '11px', color: 'var(--muted)' }}>Coordination penalty</span>
                      <span style={{ fontSize: '11px', fontWeight: 800 }}>
                        {trustFactors.coordination_penalty ?? '—'}
                      </span>
                    </div>
                  </div>
                ) : (
                  <div style={{ fontSize: '10px', color: 'var(--muted)' }}>No breakdown available yet.</div>
                )}
              </div>
            </div>
          </div>

          {/* Related reports card */}
          <div className="card">
            <div className="card-header">
              <div className="card-title">Related Reports</div>
            </div>
            <div style={{ padding: '10px 14px', fontSize: '12px' }}>
              {relatedLoading && (
                <div
                  style={{ fontSize: '12px', color: 'var(--muted)' }}
                >
                  Loading related reports…
                </div>
              )}
              {!relatedLoading && relatedReports.length === 0 && (
                <div
                  style={{ fontSize: '12px', color: 'var(--muted)' }}
                >
                  No similar reports found in the last few days.
                </div>
              )}
              {relatedReports.map((r) => (
                <div
                  key={r.report_id}
                  style={{
                    padding: '8px 0',
                    borderBottom: '1px solid var(--border2)',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      marginBottom: 2,
                    }}
                  >
                    <span
                      style={{
                        fontSize: '11px',
                        fontFamily: 'monospace',
                        color: 'var(--muted)',
                      }}
                    >
                      {r.report_number ||
                        String(r.report_id).slice(0, 8)}
                    </span>
                    <span
                      className={`badge ${
                        r.rule_status === 'passed'
                          ? 'b-green'
                          : r.rule_status === 'pending'
                          ? 'b-orange'
                          : 'b-red'
                      }`}
                      style={{ fontSize: '10px' }}
                    >
                      {r.rule_status}
                    </span>
                  </div>
                  <div style={{ fontSize: '11px' }}>
                    {r.incident_type_name || '—'} ·{' '}
                    {r.village_name || '—'}
                  </div>
                  <div
                    style={{
                      fontSize: '10px',
                      color: 'var(--muted)',
                      marginTop: 2,
                    }}
                  >
                    {formatLocalDateTime(r.reported_at)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default ReportDetail;