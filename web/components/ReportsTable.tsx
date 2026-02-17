import { useEffect } from "react";

type Report = {
  report_id: string;
  incident_type_id: number;
  reported_at: string;
  rule_status: string;
  is_flagged: boolean;
  description?: string;
};

export default function ReportsTable({
  reports,
  onView,
}: {
  reports: Report[];
  onView: (id: string) => void;
}) {
  useEffect(() => {
    console.log("ReportsTable mounted");
    return () => console.log("ReportsTable unmounted");
  }, []);

  return (
    <table className="table card">
      <thead>
        <tr>
          <th>Time</th>
          <th>ID</th>
          <th>Type</th>
          <th>Status</th>
          <th>Flagged</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {reports.map((r) => (
          <tr key={r.report_id}>
            <td>{new Date(r.reported_at).toLocaleString()}</td>
            <td style={{ fontFamily: "monospace", fontSize: 12 }}>
              {r.report_id.split("-")[0]}
            </td>
            <td>{r.incident_type_id}</td>
            <td>{r.rule_status}</td>
            <td>{r.is_flagged ? "Yes" : "No"}</td>
            <td style={{ textAlign: "right" }}>
              <button className="button" onClick={() => onView(r.report_id)}>
                View
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
