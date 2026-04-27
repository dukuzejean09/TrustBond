import React, { useEffect, useState } from 'react';
import api from '../../api/client';

// Cache bust: v20260405-1518 - Fixed sectorId -> stationId

const summarizeCaseAiSuggestion = (reports, selectedIds) => {
  const chosen = (reports || []).filter((r) => selectedIds.has(String(r.report_id)));
  if (!chosen.length) return null;

  const verifications = chosen
    .map((r) => ({ report: r, iv: r.incident_verification }))
    .filter((item) => item.iv && typeof item.iv === 'object');

  if (!verifications.length) {
    return {
      title: 'No AI case suggestion yet',
      verdict: 'INSUFFICIENT',
      reason: 'The selected reports do not yet have enough AI incident-verification detail to summarize the case.',
      metrics: [],
    };
  }

  const counts = { ACCEPTED: 0, REVIEW: 0, REJECTED: 0 };
  let totalScore = 0;
  let strongestReason = '';
  let strongestScore = -1;
  const themes = new Map();

  verifications.forEach(({ report, iv }) => {
    const decision = String(iv.decision || iv.label || 'REVIEW').toUpperCase();
    if (decision in counts) counts[decision] += 1;
    const score = Number(iv.final_score ?? (Number(iv.trust_score) <= 1 ? Number(iv.trust_score) * 100 : iv.trust_score) ?? 0);
    if (Number.isFinite(score)) totalScore += score;
    const reason = String(iv.reason || iv.final_verdict_reason || iv.reasoning || '').trim();
    if (reason && score > strongestScore) {
      strongestScore = score;
      strongestReason = reason;
    }
    const typeName = String(report.incident_type_name || 'Incident').trim();
    themes.set(typeName, (themes.get(typeName) || 0) + 1);
  });

  const primaryTheme = [...themes.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] || 'incident activity';
  const averageScore = Math.round(totalScore / verifications.length);
  const verdict =
    counts.ACCEPTED >= Math.max(counts.REVIEW, counts.REJECTED)
      ? 'ACCEPTED'
      : counts.REJECTED > counts.ACCEPTED
        ? 'REJECTED'
        : 'REVIEW';

  const verdictText =
    verdict === 'ACCEPTED'
      ? `The selected reports likely describe a connected ${primaryTheme.toLowerCase()} pattern.`
      : verdict === 'REJECTED'
        ? `The selected reports do not yet form a reliable ${primaryTheme.toLowerCase()} case pattern.`
        : `The selected reports suggest a possible ${primaryTheme.toLowerCase()} pattern, but the evidence is mixed.`;

  return {
    title: 'AI Case Suggestion',
    verdict,
    reason: strongestReason || verdictText,
    summary: verdictText,
    metrics: [
      { label: 'Accepted', value: counts.ACCEPTED },
      { label: 'Review', value: counts.REVIEW },
      { label: 'Rejected', value: counts.REJECTED },
      { label: 'Avg score', value: `${averageScore}%` },
    ],
  };
};

const NewCaseModal = ({ isOpen, onClose, onCreated, initialReportId }) => {
  const [title, setTitle] = useState('');
  const [incidentTypes, setIncidentTypes] = useState([]);
  const [incidentTypeId, setIncidentTypeId] = useState('');
  const [priority, setPriority] = useState('high');
  const [assignedToId, setAssignedToId] = useState('');
  const [officers, setOfficers] = useState([]);
  const [availableReports, setAvailableReports] = useState([]);
  const [selectedReportIds, setSelectedReportIds] = useState(new Set());
  // Simplified: Only use station-based filtering
  const [stationId, setStationId] = useState('');
  const [stations, setStations] = useState([]);
  const [notes, setNotes] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isOpen) return;
    let cancelled = false;
    setTitle('');
    setIncidentTypeId('');
    setPriority('high');
    setAssignedToId('');
    setAvailableReports([]);
    setSelectedReportIds(
      initialReportId ? new Set([String(initialReportId)]) : new Set(),
    );
    setNotes('');
    setStationId('');
    setError('');
    setSaving(false);

    const load = async () => {
      try {
        console.log('Loading incident types, officers, and stations...');
        const [types, offs, sts] = await Promise.all([
          api.get('/api/v1/incident-types'),
          api.get('/api/v1/police-users/options'),
          api.get('/api/v1/stations'),
        ]);
        if (cancelled) return;
        console.log('Loaded data:', { types, offs, sts });
        
        // If no incident types loaded, add some common ones as fallback
        if (!types || types.length === 0) {
          console.log('No incident types found, adding fallback types');
          const fallbackTypes = [
            { incident_type_id: 1, type_name: 'Theft', is_active: true },
            { incident_type_id: 2, type_name: 'Assault', is_active: true },
            { incident_type_id: 3, type_name: 'Burglary', is_active: true },
            { incident_type_id: 4, type_name: 'Vandalism', is_active: true },
            { incident_type_id: 5, type_name: 'Fraud', is_active: true },
          ];
          setIncidentTypes(fallbackTypes);
        } else {
          setIncidentTypes(types);
        }
        
        setOfficers(offs || []);
        setStations((sts && sts.items) ? sts.items : []);
      } catch (error) {
        console.error('Failed to load data:', error);
        if (cancelled) return;
        setIncidentTypes([]);
        setOfficers([]);
        setStations([]);
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const aiSuggestion = summarizeCaseAiSuggestion(availableReports, selectedReportIds);

  const submit = async () => {
    if (!title.trim()) {
      setError('Case title is required.');
      return;
    }
    setSaving(true);
    setError('');
    const ids = Array.from(selectedReportIds);

    const payload = {
      title: title.trim() || null,
      description: notes.trim() || null,
      incident_type_id: incidentTypeId ? Number(incidentTypeId) : null,
      priority: priority || 'medium',
      report_ids: ids,
      assigned_to_id: assignedToId ? Number(assignedToId) : null,
      location_id: stationId ? Number(stationId) : null,
    };

    try {
      await api.post('/api/v1/cases', payload);
      onCreated?.();
      onClose?.();
    } catch (e) {
      setError(e?.message || 'Failed to create case.');
    } finally {
      setSaving(false);
    }
  };

  const toggleReportSelected = (id) => {
    setSelectedReportIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  // When station is chosen, load available reports for that station
  const loadReportsForStation = async (stationId) => {
    console.log('Loading reports for station:', stationId, 'incident type:', incidentTypeId);
    setAvailableReports([]);
    setSelectedReportIds(
      initialReportId ? new Set([String(initialReportId)]) : new Set(),
    );
    if (!stationId) return;
    
    try {
      const params = new URLSearchParams();
      params.append('station_id', stationId);
      if (incidentTypeId) {
        params.append('incident_type_id', incidentTypeId);
      }
      
      const url = `/api/v1/cases/available-reports?${params.toString()}`;
      console.log('Fetching reports from:', url);
      
      const res = await api.get(url);
      console.log('Reports response:', res);
      console.log('Number of reports:', res?.length || 0);
      if (res && res.length > 0) {
        console.log('Sample report:', res[0]);
        console.log('Report verification statuses:');
      res.forEach(r => {
        console.log(`Report ${r.report_id}:`, {
          verification_status: r.verification_status,
          rule_status: r.rule_status,
          status: r.status,
          incident_type_id: r.incident_type_id
        });
      });
      }
      setAvailableReports(res || []);
      
      // If modal was opened from a specific report, keep it pre-selected if present.
      if (initialReportId) {
        const found = (res || []).some(
          (r) => String(r.report_id) === String(initialReportId),
        );
        if (found) {
          setSelectedReportIds(new Set([String(initialReportId)]));
        }
      }
    } catch (error) {
      console.error('Failed to load reports:', error);
      setAvailableReports([]);
    }
  };

  const loadOfficersForLocation = async (stationId) => {
    try {
      console.log('Loading officers for station:', stationId);
      const path = stationId
        ? `/api/v1/police-users/options?station_id=${stationId}`
        : '/api/v1/police-users/options';
      const res = await api.get(path);
      console.log('Officers loaded:', res);
      setOfficers(res || []);
      if (assignedToId && !(res || []).some((o) => String(o.police_user_id) === String(assignedToId))) {
        setAssignedToId('');
      }
    } catch (error) {
      console.error('Failed to load officers:', error);
      setOfficers([]);
      setAssignedToId('');
    }
  };

  return (
    <div className="modal-overlay open" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <div className="modal-title">Create New Case</div>
          <div className="modal-close" onClick={onClose}>✕</div>
        </div>

        {error && (
          <div className="alert alert-danger" style={{ marginBottom: '10px' }}>
            <span className="alert-icon">!</span>
            <div>{error}</div>
          </div>
        )}
        
        <div className="input-group">
          <div className="input-label">Case Title *</div>
          <input
            className="input"
            placeholder="e.g. Muhoza Market Assault Series"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        </div>
        
        <div className="form-grid">
          <div className="input-group">
            <div className="input-label">Incident Type</div>
            <select
              className="select"
              value={incidentTypeId}
              onChange={(e) => {
                const val = e.target.value;
                setIncidentTypeId(val);
                // Reload reports with new incident type filter
                if (stationId) {
                  loadReportsForStation(stationId);
                }
              }}
            >
              <option value="">— Select type —</option>
              {(incidentTypes || []).map((t) => (
                <option key={t.incident_type_id} value={t.incident_type_id}>
                  {t.type_name}
                </option>
              ))}
            </select>
          </div>
          <div className="input-group">
            <div className="input-label">Priority *</div>
            <select
              className="select"
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
            >
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
          <div className="input-group">
            <div className="input-label">Station (Case Location)</div>
            <select
              className="select"
              value={stationId}
              onChange={(e) => {
                const val = e.target.value;
                console.log('Station selected:', val);
                setStationId(val);
                loadReportsForStation(val);
                loadOfficersForLocation(val);
              }}
            >
              <option value="">— Select station —</option>
              {(stations || []).map((s) => (
                <option key={s.station_id} value={s.station_id}>
                  {s.station_name}
                </option>
              ))}
            </select>
          </div>
        </div>
        
        <div className="input-group">
          <div className="input-label">Assign Officer</div>
          <select
            className="select"
            value={assignedToId}
            onChange={(e) => setAssignedToId(e.target.value)}
          >
            <option value="">Unassigned (assignment handled separately)</option>
            {(officers || []).map((o) => (
              <option key={o.police_user_id} value={o.police_user_id}>
                {o.first_name} {o.last_name}
              </option>
            ))}
          </select>
        </div>
        
        <div className="input-group">
          <div className="input-label">Link Reports in Station</div>
          {!stationId && (
            <div style={{ fontSize: '11px', color: 'var(--muted)' }}>
              Select a <strong>Station</strong> first to see unassigned reports in that station
              {incidentTypeId && ` for the selected incident type`}.
            </div>
          )}
          {stationId && (
            <div style={{ fontSize: '11px', color: 'var(--muted)', marginBottom: '4px' }}>
              Showing unassigned reports in selected station
              {incidentTypeId && ` for incident type: ${incidentTypes.find(t => t.incident_type_id === Number(incidentTypeId))?.type_name}`}
            </div>
          )}
          {stationId && (
            <div
              style={{
                maxHeight: '180px',
                overflowY: 'auto',
                border: '1px solid var(--border-subtle)',
                borderRadius: '8px',
                padding: '6px 8px',
                marginTop: '4px',
              }}
            >
              {availableReports.length === 0 && (
                <div style={{ fontSize: '11px', color: 'var(--muted)' }}>
                  No unassigned reports found for this sector.
                </div>
              )}
              {(availableReports || []).map((r) => (
                <label
                  key={r.report_id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    fontSize: '11px',
                    marginBottom: '4px',
                  }}
                >
                  <input
                    type="checkbox"
                    checked={selectedReportIds.has(String(r.report_id))}
                    onChange={() => toggleReportSelected(String(r.report_id))}
                  />
                  <span style={{ fontFamily: 'monospace' }}>
                    {r.report_number || String(r.report_id).slice(0, 8)}
                  </span>
                  <span style={{ color: 'var(--muted)' }}>
                    · {r.incident_type_name || 'Incident'} ·{' '}
                    {r.village_name || 'Unknown'}
                  </span>
                </label>
              ))}
            </div>
          )}
        </div>

        {aiSuggestion && (
          <div
            style={{
              marginBottom: '12px',
              padding: '12px',
              borderRadius: '8px',
              background:
                aiSuggestion.verdict === 'ACCEPTED'
                  ? 'rgba(76, 175, 80, 0.12)'
                  : aiSuggestion.verdict === 'REJECTED'
                    ? 'rgba(244, 67, 54, 0.12)'
                    : 'rgba(255, 152, 0, 0.12)',
              border:
                aiSuggestion.verdict === 'ACCEPTED'
                  ? '1px solid rgba(76, 175, 80, 0.35)'
                  : aiSuggestion.verdict === 'REJECTED'
                    ? '1px solid rgba(244, 67, 54, 0.35)'
                    : '1px solid rgba(255, 152, 0, 0.35)',
            }}
          >
            <div style={{ fontSize: '12px', fontWeight: 700, marginBottom: '6px' }}>
              {aiSuggestion.title}
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text)', lineHeight: 1.5, marginBottom: '8px' }}>
              {aiSuggestion.summary || aiSuggestion.reason}
            </div>
            {aiSuggestion.reason && (
              <div style={{ fontSize: '11px', color: 'var(--muted)', marginBottom: '8px' }}>
                {aiSuggestion.reason}
              </div>
            )}
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              {aiSuggestion.metrics.map((metric) => (
                <div
                  key={metric.label}
                  style={{
                    padding: '6px 8px',
                    borderRadius: '6px',
                    background: 'rgba(255,255,255,0.45)',
                    fontSize: '11px',
                  }}
                >
                  <strong>{metric.value}</strong> {metric.label}
                </div>
              ))}
            </div>
          </div>
        )}
        
        <div className="input-group">
          <div className="input-label">Notes</div>
          <textarea
            rows="3"
            placeholder="Initial case notes..."
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          ></textarea>
        </div>
        
        <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
          <button className="btn btn-outline" onClick={onClose} disabled={saving}>Cancel</button>
          <button className="btn btn-primary" onClick={submit} disabled={saving}>
            {saving ? 'Creating…' : 'Create Case'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default NewCaseModal;
