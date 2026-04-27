import React, { useEffect, useState } from 'react';
import api from '../../api/client';
import { useAuth } from '../../context/AuthContext';

const summarizeCaseAiSuggestion = (reports) => {
  const linked = (reports || []).filter(Boolean);
  if (!linked.length) return null;

  const verifications = linked
    .map((r) => ({ report: r, iv: r.incident_verification }))
    .filter((item) => item.iv && typeof item.iv === 'object');

  if (!verifications.length) {
    return {
      verdict: 'INSUFFICIENT',
      summary: 'Linked reports do not yet have enough AI reasoning to summarize this case.',
      reason: '',
      metrics: [],
    };
  }

  const counts = { ACCEPTED: 0, REVIEW: 0, REJECTED: 0 };
  let totalScore = 0;
  let bestReason = '';
  let bestScore = -1;

  verifications.forEach(({ iv }) => {
    const decision = String(iv.decision || iv.label || 'REVIEW').toUpperCase();
    if (decision in counts) counts[decision] += 1;
    const score = Number(iv.final_score ?? (Number(iv.trust_score) <= 1 ? Number(iv.trust_score) * 100 : iv.trust_score) ?? 0);
    if (Number.isFinite(score)) totalScore += score;
    const reason = String(iv.reason || iv.final_verdict_reason || iv.reasoning || '').trim();
    if (reason && score > bestScore) {
      bestReason = reason;
      bestScore = score;
    }
  });

  const averageScore = Math.round(totalScore / verifications.length);
  const verdict =
    counts.ACCEPTED >= Math.max(counts.REVIEW, counts.REJECTED)
      ? 'ACCEPTED'
      : counts.REJECTED > counts.ACCEPTED
        ? 'REJECTED'
        : 'REVIEW';

  const summary =
    verdict === 'ACCEPTED'
      ? 'AI suggests the linked reports describe a credible shared incident pattern.'
      : verdict === 'REJECTED'
        ? 'AI suggests the linked reports do not yet form a credible case pattern.'
        : 'AI suggests the linked reports may be related, but the pattern still needs officer review.';

  return {
    verdict,
    summary,
    reason: bestReason,
    metrics: [
      { label: 'Accepted', value: counts.ACCEPTED },
      { label: 'Review', value: counts.REVIEW },
      { label: 'Rejected', value: counts.REJECTED },
      { label: 'Avg score', value: `${averageScore}%` },
    ],
  };
};

const EditCaseModal = ({ isOpen, onClose, caseItem, onSaved }) => {
  const { user: me } = useAuth();
  const role = me?.role || 'officer';
  const isAdminOrSupervisor = role === 'admin' || role === 'supervisor';

  const [status, setStatus] = useState(caseItem?.status || 'open');
  const [priority, setPriority] = useState(caseItem?.priority || 'medium');
  const [description, setDescription] = useState(caseItem?.description || '');
  const [outcome, setOutcome] = useState(caseItem?.outcome || '');
  const [assignedToId, setAssignedToId] = useState(caseItem?.assigned_to_id || '');
  const [officers, setOfficers] = useState([]);
  const [linkedReports, setLinkedReports] = useState([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isOpen || !caseItem) return;
    setStatus(caseItem.status || 'open');
    setPriority(caseItem.priority || 'medium');
    setDescription(caseItem.description || '');
    setOutcome(caseItem.outcome || '');
    setAssignedToId(caseItem.assigned_to_id || '');
    setLinkedReports([]);
    setError('');
    setSaving(false);
  }, [isOpen, caseItem]);

  useEffect(() => {
    if (!isOpen || !caseItem?.case_id) return;
    let cancelled = false;
    api
      .get(`/api/v1/cases/${caseItem.case_id}/reports`)
      .then((res) => {
        if (cancelled) return;
        setLinkedReports(res || []);
      })
      .catch(() => {
        if (cancelled) return;
        setLinkedReports([]);
      });
    return () => {
      cancelled = true;
    };
  }, [isOpen, caseItem?.case_id]);

  // Load officer options for assignment when admin/supervisor.
  useEffect(() => {
    if (!isOpen || !isAdminOrSupervisor) return;
    let cancelled = false;
    
    // Get station_id from the assigned officer or case location
    const loadOfficers = async () => {
      try {
        let stationId = null;
        
        // First try to get station from currently assigned officer
        if (caseItem?.assigned_to_id) {
          // Get officer details to find their station
          const officerRes = await api.get(`/api/v1/police-users/${caseItem.assigned_to_id}`);
          if (officerRes?.station_id) {
            stationId = officerRes.station_id;
          }
        }
        
        // If no station from officer, try to get from case location
        if (!stationId && caseItem?.location_id) {
          // For now, we'll load all officers since we don't have station from location
          stationId = null;
        }
        
        const path = stationId
          ? `/api/v1/police-users/options?station_id=${stationId}`
          : '/api/v1/police-users/options';
        
        const res = await api.get(path);
        if (cancelled) return;
        setOfficers(res || []);
        
        // Make sure the currently assigned officer is in the list
        if (assignedToId && !(res || []).some((o) => String(o.police_user_id) === String(assignedToId))) {
          // If assigned officer not in list, add them
          const assignedOfficer = res?.find(o => String(o.police_user_id) === String(assignedToId));
          if (!assignedOfficer && caseItem?.assigned_to_name) {
            // Add the assigned officer to the list if they exist but weren't in the filtered results
            setOfficers(prev => [...prev, {
              police_user_id: caseItem.assigned_to_id,
              first_name: caseItem.assigned_to_name.split(' ')[0],
              last_name: caseItem.assigned_to_name.split(' ').slice(1).join(' '),
            }]);
          }
        }
      } catch (error) {
        console.error('Failed to load officers:', error);
        if (cancelled) return;
        setOfficers([]);
      }
    };
    
    loadOfficers();
    return () => {
      cancelled = true;
    };
  }, [isOpen, isAdminOrSupervisor, caseItem?.assigned_to_id, caseItem?.location_id]);

  if (!isOpen || !caseItem) return null;

  const aiSuggestion = summarizeCaseAiSuggestion(linkedReports);

  const submit = async () => {
    setSaving(true);
    setError('');
    const payload = {
      status,
      description,
      outcome,
      ...(isAdminOrSupervisor ? { priority, assigned_to_id: assignedToId || null } : {}),
    };
    try {
      await api.patch(`/api/v1/cases/${caseItem.case_id}`, payload);
      onSaved?.();
      onClose?.();
    } catch (e) {
      setError(e?.message || 'Failed to update case.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-overlay open" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <div className="modal-title">
            Update Case — {caseItem.case_number || String(caseItem.case_id).slice(0, 8)}
          </div>
          <div className="modal-close" onClick={onClose}>✕</div>
        </div>

        {error && (
          <div className="alert alert-danger" style={{ marginBottom: '10px' }}>
            <span className="alert-icon">!</span>
            <div>{error}</div>
          </div>
        )}

        <div className="form-grid" style={{ marginBottom: '12px' }}>
          <div className="input-group">
            <div className="input-label">Status</div>
            <select
              className="select"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
            >
              <option value="open">open</option>
              <option value="investigating">investigating</option>
              <option value="closed">closed</option>
            </select>
          </div>
          <div className="input-group">
            <div className="input-label">Priority</div>
            <select
              className="select"
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
              disabled={!isAdminOrSupervisor}
            >
              <option value="high">high</option>
              <option value="medium">medium</option>
              <option value="low">low</option>
            </select>
          </div>
          {isAdminOrSupervisor && (
            <div className="input-group">
              <div className="input-label">Assign Officer</div>
              <select
                className="select"
                value={assignedToId}
                onChange={(e) => setAssignedToId(e.target.value)}
              >
                <option value="">Unassigned</option>
                {officers.map((o) => (
                  <option key={o.police_user_id} value={o.police_user_id}>
                    {o.first_name} {o.last_name}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        <div className="input-group">
          <div className="input-label">Description / Progress Notes</div>
          <textarea
            rows="3"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Update investigation details..."
          ></textarea>
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
              AI Suggestion For This Case
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text)', lineHeight: 1.5, marginBottom: '8px' }}>
              {aiSuggestion.summary}
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
          <div className="input-label">Outcome</div>
          <textarea
            rows="2"
            value={outcome}
            onChange={(e) => setOutcome(e.target.value)}
            placeholder="Outcome (for closed cases)..."
          ></textarea>
        </div>

        <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end', marginTop: '10px' }}>
          <button className="btn btn-outline" onClick={onClose} disabled={saving}>
            Cancel
          </button>
          <button className="btn btn-primary" onClick={submit} disabled={saving}>
            {saving ? 'Saving…' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default EditCaseModal;

