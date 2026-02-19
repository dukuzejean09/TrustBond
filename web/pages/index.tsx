import { useEffect, useState } from "react";
import Image from "next/image";
import { useRouter } from "next/router";
import KpiCard from "../components/KpiCard";
import ReportsTable from "../components/ReportsTable";
import ReportModal from "../components/ReportModal";
import {
  getReportCount,
  getAssignments,
  getReports,
  getHotspots,
} from "../lib/api";

import logo from "./logo.png";

export default function Dashboard() {
  const router = useRouter();
  const [total, setTotal] = useState<number | null>(null);
  const [flagged, setFlagged] = useState<number | null>(null);
  const [pendingAssignments, setPendingAssignments] = useState<number | null>(
    null,
  );
  const [hotspots, setHotspots] = useState<any[]>([]);
  const [reports, setReports] = useState<any[]>([]);
  const [selectedReport, setSelectedReport] = useState<string | null>(null);

  useEffect(() => {
    console.log("Dashboard mounted");
    if (typeof window === "undefined")
      return () => console.log("Dashboard unmounted (ssr)");
    const token = localStorage.getItem("tb_token");
    if (!token) {
      router.push("/login");
      return () => console.log("Dashboard unmounted (redirect)");
    }

    let mounted = true;
    async function load() {
      try {
        const [t, f, a, r, hs] = await Promise.all([
          getReportCount(),
          getReportCount({ is_flagged: true }),
          getAssignments("pending"),
          getReports(1, 10),
          getHotspots(),
        ]);
        if (!mounted) return;
        setTotal(t);
        setFlagged(f);
        setPendingAssignments(Array.isArray(a) ? a.length : 0);
        setReports(r.reports ?? []);
        setHotspots(hs ?? []);
      } catch (err) {
        console.error(err);
      }
    }
    load();

    return () => {
      mounted = false;
      console.log("Dashboard unmounted");
    };
  }, [router]);

  function logout() {
    localStorage.removeItem("tb_token");
    router.push("/login");
  }

  return (
    <div className="container">
      <div className="header">
        <div
          className="brand"
          style={{ display: "flex", alignItems: "center", gap: 10 }}
        >
          <Image
            src={logo}
            alt="TrustBond Logo"
            width={36}
            height={36}
            style={{ borderRadius: 6 }}
          />
          <span>TrustBond — Dashboard</span>
        </div>
        <div className="controls">
          <div className="small-muted">Role: Admin</div>
          <button className="button" onClick={logout}>
            Logout
          </button>
        </div>
      </div>

      <div className="kpi-row">
        <KpiCard
          title="Total reports"
          value={total ?? "—"}
          subtitle="All time"
        />
        <KpiCard
          title="Flagged"
          value={flagged ?? "—"}
          subtitle="Requires review"
        />
        <KpiCard
          title="Assignments (pending)"
          value={pendingAssignments ?? "—"}
          subtitle="Officer workload"
        />
        <KpiCard
          title="Active hotspots"
          value={hotspots?.length ?? "—"}
          subtitle="Recluster to update"
        />
      </div>

      <div className="main-grid">
        <div>
          <div className="card">
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <strong>Recent reports</strong>
              <div className="small-muted">Latest 10</div>
            </div>
            <ReportsTable
              reports={reports}
              onView={(id) => setSelectedReport(id)}
            />
          </div>
        </div>

        <div>
          <div className="card" style={{ marginBottom: 12 }}>
            <strong>ML summary</strong>
            <div className="small-muted" style={{ marginTop: 8 }}>
              Model status: <span style={{ color: "#7dd3fc" }}>no data</span>
            </div>
            <div style={{ marginTop: 12 }} className="small-muted">
              Top predictions and confidence will appear here once the ML API is
              available.
            </div>
          </div>

          <div className="card">
            <strong>Assignments (recent)</strong>
            <div className="small-muted" style={{ marginTop: 8 }}>
              Open assignments are shown in the table
            </div>
            <div style={{ marginTop: 12 }} className="small-muted">
              Use the Report details modal to assign or change status.
            </div>
          </div>
        </div>
      </div>

      {selectedReport && (
        <ReportModal
          reportId={selectedReport}
          onClose={() => setSelectedReport(null)}
        />
      )}
    </div>
  );
}
