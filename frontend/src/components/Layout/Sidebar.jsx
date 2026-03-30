import React, { useState } from "react";

const Sidebar = ({
  isOpen,
  currentScreen,
  onNavigate,
  sidebarCounts = {},
  user,
  onLogout,
}) => {
  // Map detail screens back to their parent nav item for highlighting.
  const sidebarActiveScreen =
    currentScreen === "report-detail"
      ? "reports"
      : currentScreen === "hotspot-details"
        ? "hotspots"
        : currentScreen;

  const {
    reports: reportsBadge = 0,
    cases: casesBadge = 0,
    notifications: notificationsBadge = 0,
  } = sidebarCounts;

  const role = user?.role || "officer";

  const navItems = [
    {
      section: "Overview",
      items: [{ id: "dashboard", idx: 0, label: "Dashboard", icon: "ni-db" }],
    },
    {
      section: "Operations",
      items: [
        {
          id: "reports",
          idx: 1,
          label: "Reports",
          icon: "ni-rp",
          badge: reportsBadge,
        },
        {
          id: "case-management",
          idx: 3,
          label: "Case Management",
          icon: "ni-cm",
          badge: casesBadge,
        },
        { id: "hotspots", idx: 4, label: "Hotspots", icon: "ni-hs" },
        { id: "safety-map", idx: 5, label: "Safety Map", icon: "ni-mp" },
      ],
    },
    {
      section: "Intelligence",
      items: [
        // Device trust analytics – restricted to admin / supervisor
        ...(role === "admin" || role === "supervisor"
          ? [
              {
                id: "device-trust",
                idx: 6,
                label: "Device Trust",
                icon: "ni-dt",
              },
            ]
          : []),
      ],
    },
    {
      section: "Management",
      items: [
        ...(role === "admin"
          ? [
              { id: "users", idx: 7, label: "Users", icon: "ni-us" },
              {
                id: "incident-types",
                idx: 8,
                label: "Incident Types",
                icon: "ni-it",
              },
              { id: "stations", idx: 9, label: "Stations", icon: "ni-it" },
              {
                id: "system-config",
                idx: 10,
                label: "System Config",
                icon: "ni-dt",
              },
              { id: "audit-log", idx: 11, label: "Audit Log", icon: "ni-al" },
              {
                id: "active-sessions",
                idx: 13,
                label: "Active Sessions",
                icon: "ni-al",
              },
            ]
          : role === "supervisor"
            ? [
                { id: "users", idx: 7, label: "Users", icon: "ni-us" },
                { id: "stations", idx: 9, label: "Stations", icon: "ni-it" },
              ]
            : []),
      ],
    },
    {
      section: "Account",
      items: [
        {
          id: "change-password",
          idx: 11,
          label: "Change Password",
          icon: "ni-cp",
        },
        {
          id: "notifications",
          idx: 12,
          label: "Notifications",
          icon: "ni-nt",
          badge: notificationsBadge,
        },
      ],
    },
  ];

  const activeSection = navItems.find((section) =>
    section.items.some((it) => it.id === sidebarActiveScreen),
  )?.section;

  const [expandedSections, setExpandedSections] = useState(() => {
    // Collapse everything by default. Keep only the active section expanded.
    const s = new Set();
    if (activeSection) s.add(activeSection);
    return s;
  });

  const toggleSection = (sectionName) => {
    // Keep the currently-active section visible for usability.
    if (sectionName === activeSection) return;
    setExpandedSections((prev) => {
      const next = new Set(prev);
      if (next.has(sectionName)) next.delete(sectionName);
      else next.add(sectionName);
      return next;
    });
  };

  return (
    <aside id="sidebar" className={isOpen ? "open" : ""}>
      <nav>
        {navItems.map((section, idx) => (
          <div className="nav-section" key={idx}>
            <div
              className="nav-label nav-section-toggle"
              role="button"
              tabIndex={0}
              onClick={() => {
                if (section.items.length > 1) toggleSection(section.section);
              }}
              onKeyDown={(e) => {
                if (section.items.length <= 1) return;
                if (e.key === "Enter" || e.key === " ")
                  toggleSection(section.section);
              }}
              aria-expanded={
                section.items.length <= 1
                  ? true
                  : section.section === activeSection
                    ? true
                    : expandedSections.has(section.section)
              }
            >
              <span>{section.section}</span>
              {section.items.length > 1 && (
                <span className="nav-chevron" aria-hidden="true">
                  {section.section === activeSection ||
                  expandedSections.has(section.section)
                    ? "▾"
                    : "▸"}
                </span>
              )}
            </div>

            {(section.items.length <= 1 ||
              section.section === activeSection ||
              expandedSections.has(section.section)) &&
              section.items.map((item) => (
                <div
                  key={item.id}
                  className={`nav-item ${sidebarActiveScreen === item.id ? "active" : ""}`}
                  id={`nav-${item.idx}`}
                  onClick={() => onNavigate(item.id, item.idx)}
                >
                  <span className={`nav-icon ${item.icon}`}></span>
                  <span className="nav-text">{item.label}</span>
                  {item.badge && (
                    <span className="nav-badge">{item.badge}</span>
                  )}
                </div>
              ))}
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="user-card">
          <div className="avatar">
            {user?.first_name?.[0]?.toUpperCase() || "U"}
          </div>
          <div style={{ overflow: "hidden" }}>
            <div className="user-name">
              {user ? `${user.first_name} ${user.last_name}` : "User"}
            </div>
            <div className="user-role">
              {role === "admin"
                ? "Administrator"
                : role === "supervisor"
                  ? "Supervisor"
                  : "Officer"}
            </div>
          </div>
        </div>
        <button type="button" className="sidebar-signout" onClick={onLogout}>
          Sign Out
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
