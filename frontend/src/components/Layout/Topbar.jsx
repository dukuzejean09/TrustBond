import React from "react";

const Topbar = ({
  currentScreen,
  titles,
  isLightMode,
  toggleMode,
  toggleSidebar,
  goToScreen,
}) => {
  const getCurrentDate = () => {
    const date = new Date();
    return date
      .toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      })
      .replace(",", "");
  };

  const getSectionLabel = () => {
    const sectionMap = {
      dashboard: "Overview",
      reports: "Operations",
      "report-detail": "Operations",
      "case-management": "Operations",
      hotspots: "Operations",
      "hotspot-details": "Operations",
      "safety-map": "Operations",
      "device-trust": "Intelligence",
      users: "Management",
      "incident-types": "Management",
      stations: "Management",
      "system-config": "Management",
      "audit-log": "Management",
      notifications: "Account",
      "active-sessions": "Management",
      "change-password": "Account",
    };
    return sectionMap[currentScreen] || "Overview";
  };

  return (
    <header id="topbar">
      <div className="topbar-brand-zone">
        <div className="topbar-brand-strip" aria-hidden="true"></div>
        <img className="topbar-brand-logo" src="/logo.jpeg" alt="TrustBond logo" />
        <div className="topbar-brand-copy">
          <div className="topbar-brand-name">TrustBond</div>
          <div className="topbar-brand-sub">Police Portal</div>
        </div>
      </div>

      <div className="topbar-main">
        <div id="hamburger" onClick={toggleSidebar}>
          ☰
        </div>

        <div className="topbar-center">
          <div className="tb-context">
            <div className="tb-page-title">{titles[currentScreen] || "Dashboard"}</div>
            <nav className="tb-breadcrumb" aria-label="Breadcrumb">
              <button
                type="button"
                className="tb-breadcrumb-link"
                onClick={() => goToScreen("dashboard", 0)}
              >
                Home
              </button>
              <span className="tb-breadcrumb-sep">›</span>
              <span className="tb-breadcrumb-link">{getSectionLabel()}</span>
              <span className="tb-breadcrumb-sep">›</span>
              <span className="tb-breadcrumb-current">
                {titles[currentScreen] || "Dashboard"}
              </span>
            </nav>
          </div>
        </div>

        <div className="topbar-right">
          <div className="tb-status-pill" title="All systems operational">
            <span className="tb-status-dot"></span>
            Operational
          </div>

          <div className="tb-chip tb-date-chip">{getCurrentDate()}</div>

          <button id="modeToggle" onClick={toggleMode}>
            {isLightMode ? "Dark Mode" : "Light Mode"}
          </button>

          <button
            type="button"
            className="tb-icon-btn"
            onClick={() => goToScreen("notifications", 11)}
            title="Notifications"
            aria-label="Notifications"
          >
            🔔
            <span className="tb-icon-btn-badge"></span>
          </button>
        </div>
      </div>

      <div className="tb-mobile-title">{titles[currentScreen] || "Dashboard"}</div>
    </header>
  );
};

export default Topbar;
