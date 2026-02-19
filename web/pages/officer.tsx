import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import Image from "next/image";
import ReportModal from "../components/ReportModal";
import { getAssignments } from "../lib/api";
import logo from "./logo.png";

export default function OfficerDashboard() {
  const router = useRouter();
  const [assignments, setAssignments] = useState<any[]>([]);
  const [selectedReport, setSelectedReport] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const rawToken = localStorage.getItem("tb_token");
    if (!rawToken) {
      router.push("/login");
      return;
    }

    let payload: any = null;
    try {
      payload = JSON.parse(
        atob(rawToken.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")),
      );
    } catch (err) {
      router.push("/login");
      return;
    }

    if (payload?.role !== "officer") {
      // redirect non-officers back to main dashboard
      router.push("/");
      return;
    }

    const policeUserId = Number(payload.sub);

    let mounted = true;
    async function load() {
      setLoading(true);
      try {
        const a = await getAssignments("pending", policeUserId);
        if (!mounted) return;
        setAssignments(Array.isArray(a) ? a : []);
      } catch (err) {
        console.error(err);
        setAssignments([]);
      } finally {
        setLoading(false);
      }
    }
    load();

    return () => {
      mounted = false;
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
          <span>TrustBond — Officer Dashboard</span>
        </div>
        <div className="controls">
          <div className="small-muted">Role: Officer</div>
          <button className="button" onClick={logout}>
            Logout
          </button>
        </div>
      </div>

      <div style={{ marginTop: 12 }}>
        <div className="card">
          <strong>My assignments (pending)</strong>
          <div className="small-muted" style={{ marginTop: 8 }}>
            {loading ? "Loading…" : `${assignments.length} open assignment(s)`}
          </div>
          <div style={{ marginTop: 12 }}>
            {assignments.length ? (
              <ul>
                {assignments.map((a) => (
                  <li key={a.assignment_id} style={{ marginBottom: 8 }}>
                    <strong>{a.priority ?? "--"}</strong> — {a.status}
                    <div className="small-muted" style={{ marginTop: 6 }}>
                      Report: {a.report_id}
                    </div>
                    <div style={{ marginTop: 6 }}>
                      <button
                        className="button"
                        onClick={() => setSelectedReport(a.report_id)}
                      >
                        View report
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="small-muted">No assignments assigned to you.</div>
            )}
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
