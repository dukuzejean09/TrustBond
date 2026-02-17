import { useEffect, useState } from "react";
import { getReport } from "../lib/api";

export default function ReportModal({
  reportId,
  onClose,
}: {
  reportId: string | null;
  onClose: () => void;
}) {
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    console.log("ReportModal mounted", reportId);
    let active = true;
    if (!reportId) return () => console.log("ReportModal unmounted (no id)");
    setLoading(true);
    getReport(reportId)
      .then((r) => {
        if (active) setReport(r);
      })
      .catch(() => {
        if (active) setReport(null);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
      console.log("ReportModal unmounted", reportId);
    };
  }, [reportId]);

  if (!reportId) return null;
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <h3 style={{ margin: 0 }}>Report details</h3>
          <div style={{ fontSize: 12, color: "#94a3b8" }}>{reportId}</div>
        </div>
        <hr
          style={{
            border: "none",
            borderTop: "1px solid rgba(255,255,255,0.03)",
            margin: "10px 0",
          }}
        />
        {loading && <div className="small-muted">Loading...</div>}
        {!loading && report && (
          <div>
            <div style={{ marginBottom: 8 }}>
              <strong>Type:</strong>{" "}
              {report.incident_type?.type_name ?? report.incident_type_id}
            </div>
            <div style={{ marginBottom: 8 }}>
              <strong>Status:</strong> {report.rule_status}{" "}
              {report.is_flagged ? " • Flagged" : ""}
            </div>
            <div style={{ marginBottom: 8 }}>
              <strong>Reported at:</strong>{" "}
              {new Date(report.reported_at).toLocaleString()}
            </div>
            <div style={{ marginTop: 10 }}>
              <strong>Description</strong>
              <div className="small-muted">{report.description ?? "—"}</div>
            </div>

            <div style={{ marginTop: 12 }}>
              <strong>ML Predictions</strong>
              {report.ml_predictions?.length ? (
                <ul>
                  {report.ml_predictions.map((m: any) => (
                    <li key={m.prediction_id}>
                      {m.model_type} — {m.prediction_label ?? "n/a"} — conf{" "}
                      {m.confidence ?? "—"}
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="small-muted">No ML predictions</div>
              )}
            </div>

            <div style={{ marginTop: 12 }}>
              <strong>Assignments</strong>
              {report.assignments?.length ? (
                <ul>
                  {report.assignments.map((a: any) => (
                    <li key={a.assignment_id}>
                      {a.police_user_id} — {a.status} — {a.priority}
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="small-muted">No assignments</div>
              )}
            </div>
          </div>
        )}

        {!loading && !report && (
          <div className="small-muted">Unable to load report.</div>
        )}

        <div
          style={{ display: "flex", justifyContent: "flex-end", marginTop: 12 }}
        >
          <button className="button" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
