import React, { useCallback, useMemo, useState, useEffect } from "react";
import { apiService } from "../../services/apiService";

const Notifications = () => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("all");
  const [working, setWorking] = useState(false);

  const load = useCallback(async (isActive = () => true) => {
    setLoading(true);
    setError("");
    try {
      const res = await apiService.getNotifications({ limit: 100 });
      if (isActive()) setItems(Array.isArray(res) ? res : []);
    } catch (e) {
      if (isActive()) setError(e?.message || "Failed to load notifications.");
    } finally {
      if (isActive()) setLoading(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    const isActive = () => active;
    load(isActive);
    return () => {
      active = false;
    };
  }, [load]);

  const filteredItems = useMemo(() => {
    if (filter === "unread") return items.filter((n) => !n.is_read);
    if (filter === "read") return items.filter((n) => n.is_read);
    return items;
  }, [items, filter]);

  const unread = items.filter((n) => !n.is_read).length;

  const markOneRead = async (id) => {
    try {
      await apiService.markNotificationRead(id);
      setItems((prev) =>
        prev.map((n) =>
          n.notification_id === id ? { ...n, is_read: true } : n,
        ),
      );
    } catch (e) {
      setError(e?.message || "Failed to mark notification as read.");
    }
  };

  const markAllRead = async () => {
    const unreadIds = items
      .filter((n) => !n.is_read)
      .map((n) => n.notification_id);
    if (!unreadIds.length) return;
    setWorking(true);
    setError("");
    try {
      await Promise.all(
        unreadIds.map((id) => apiService.markNotificationRead(id)),
      );
      setItems((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch (e) {
      setError(e?.message || "Failed to mark all notifications as read.");
    } finally {
      setWorking(false);
    }
  };

  const clearReadFromView = () => {
    setItems((prev) => prev.filter((n) => !n.is_read));
  };

  const typeBadgeClass = (type) => {
    const t = String(type || "info").toLowerCase();
    if (t === "hotspot") return "b-red";
    if (t === "assignment") return "b-orange";
    if (t === "report") return "b-green";
    return "b-blue";
  };

  return (
    <>
      <div className="page-header">
        <h2>Notifications</h2>
        <p>
          Live alerts for reports, assignments, hotspots, and system activity.
        </p>
      </div>

      <div className="notifications-summary-grid">
        <div className="card notifications-kpi">
          <span>Total</span>
          <strong>{items.length}</strong>
        </div>
        <div className="card notifications-kpi">
          <span>Unread</span>
          <strong style={{ color: "var(--danger)" }}>{unread}</strong>
        </div>
        <div className="card notifications-kpi">
          <span>Read</span>
          <strong>{Math.max(items.length - unread, 0)}</strong>
        </div>
      </div>

      <div className="g2-fixed">
        <div className="card">
          <div className="card-header">
            <div className="card-title">Notification Feed</div>
            <div style={{ display: "flex", gap: "6px" }}>
              <button
                className="btn btn-outline btn-sm"
                onClick={() => setFilter("all")}
              >
                All
              </button>
              <button
                className="btn btn-outline btn-sm"
                onClick={() => setFilter("unread")}
              >
                Unread
              </button>
              <button
                className="btn btn-outline btn-sm"
                onClick={() => setFilter("read")}
              >
                Read
              </button>
            </div>
          </div>

          {error && (
            <div className="error-box" style={{ marginBottom: 10 }}>
              {error}
            </div>
          )}

          {loading && (
            <div className="loading-center" style={{ minHeight: 140 }}>
              Loading notifications...
            </div>
          )}

          {!loading &&
            filteredItems.map((n) => (
              <div
                className={`notif-item ${n.is_read ? "is-read" : "is-unread"}`}
                key={n.notification_id}
              >
                <div
                  className="notif-icon-wrap"
                  style={{
                    background: n.is_read
                      ? "rgba(79,142,247,0.10)"
                      : "rgba(248,113,113,0.16)",
                  }}
                >
                  {String(n.type || "info")
                    .toUpperCase()
                    .slice(0, 3)}
                </div>
                <div className="notif-body">
                  <div className="notif-title-text">
                    {n.title || "Notification"}
                  </div>
                  <div className="notif-desc">
                    {n.message || "No details provided."}
                  </div>
                  <div className="notif-time">
                    {n.created_at
                      ? new Date(n.created_at).toLocaleString()
                      : "—"}
                  </div>
                </div>
                <div className="notifications-actions-col">
                  <span className={`badge ${typeBadgeClass(n.type)}`}>
                    {n.type || "info"}
                  </span>
                  {!n.is_read && (
                    <button
                      className="btn btn-outline btn-sm"
                      onClick={() => markOneRead(n.notification_id)}
                    >
                      Mark read
                    </button>
                  )}
                </div>
              </div>
            ))}

          {!filteredItems.length && !loading && (
            <div
              style={{
                fontSize: "12px",
                color: "var(--muted)",
                padding: "10px 14px",
              }}
            >
              No notifications in this view.
            </div>
          )}
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          <div className="card">
            <div className="card-header">
              <div className="card-title">Actions</div>
            </div>
            <div className="notif-actions-panel">
              <button
                className="btn btn-primary btn-sm"
                disabled={!unread || working}
                onClick={markAllRead}
              >
                {working ? "Updating..." : "Mark all unread as read"}
              </button>
              <button
                className="btn btn-outline btn-sm"
                onClick={clearReadFromView}
              >
                Clear read from view
              </button>
              <button className="btn btn-outline btn-sm" onClick={load}>
                Refresh feed
              </button>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <div className="card-title">Notification Summary</div>
            </div>
            <div className="status-row">
              <span>Unread</span>
              <strong style={{ color: "var(--danger)" }}>{unread}</strong>
            </div>
            <div className="status-row">
              <span>Total loaded</span>
              <strong>{items.length}</strong>
            </div>
            <div className="status-row">
              <span>Current filter</span>
              <strong>{filter}</strong>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Notifications;
