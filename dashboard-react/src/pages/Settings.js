import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import "../styles/Settings.css";

const Settings = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState("profile");
  const [profile, setProfile] = useState({
    fullName: user?.fullName || "",
    email: user?.email || "",
    phone: user?.phone || "",
    district: user?.district || "",
  });
  const [password, setPassword] = useState({
    current: "",
    newPassword: "",
    confirm: "",
  });
  const [notifications, setNotifications] = useState({
    emailAlerts: true,
    pushNotifications: true,
    weeklyDigest: false,
    criticalOnly: false,
  });
  const [saving, setSaving] = useState(false);

  const handleProfileSave = async () => {
    setSaving(true);
    // Simulate API call
    setTimeout(() => {
      setSaving(false);
      alert("Profile updated successfully!");
    }, 1000);
  };

  const handlePasswordChange = async () => {
    if (password.newPassword !== password.confirm) {
      alert("Passwords do not match!");
      return;
    }
    if (password.newPassword.length < 8) {
      alert("Password must be at least 8 characters!");
      return;
    }
    setSaving(true);
    setTimeout(() => {
      setSaving(false);
      setPassword({ current: "", newPassword: "", confirm: "" });
      alert("Password changed successfully!");
    }, 1000);
  };

  const handleNotificationsSave = async () => {
    setSaving(true);
    setTimeout(() => {
      setSaving(false);
      alert("Notification preferences saved!");
    }, 1000);
  };

  return (
    <div className="settings-page">
      <div className="page-header">
        <h1>
          <i className="fas fa-cog"></i> Settings
        </h1>
      </div>

      <div className="settings-container">
        <div className="settings-sidebar">
          <nav>
            <button
              className={activeTab === "profile" ? "active" : ""}
              onClick={() => setActiveTab("profile")}
            >
              <i className="fas fa-user"></i> Profile
            </button>
            <button
              className={activeTab === "password" ? "active" : ""}
              onClick={() => setActiveTab("password")}
            >
              <i className="fas fa-lock"></i> Password
            </button>
            <button
              className={activeTab === "notifications" ? "active" : ""}
              onClick={() => setActiveTab("notifications")}
            >
              <i className="fas fa-bell"></i> Notifications
            </button>
            <button
              className={activeTab === "system" ? "active" : ""}
              onClick={() => setActiveTab("system")}
            >
              <i className="fas fa-sliders-h"></i> System
            </button>
          </nav>
        </div>

        <div className="settings-content">
          {/* Profile Settings */}
          {activeTab === "profile" && (
            <div className="settings-section">
              <h2>Profile Settings</h2>
              <p className="section-description">
                Update your personal information
              </p>

              <div className="form-grid">
                <div className="form-group">
                  <label>Full Name</label>
                  <input
                    type="text"
                    value={profile.fullName}
                    onChange={(e) =>
                      setProfile({ ...profile, fullName: e.target.value })
                    }
                    placeholder="Your full name"
                  />
                </div>
                <div className="form-group">
                  <label>Email Address</label>
                  <input
                    type="email"
                    value={profile.email}
                    onChange={(e) =>
                      setProfile({ ...profile, email: e.target.value })
                    }
                    placeholder="your@email.com"
                    disabled
                  />
                  <span className="help-text">Email cannot be changed</span>
                </div>
                <div className="form-group">
                  <label>Phone Number</label>
                  <input
                    type="tel"
                    value={profile.phone}
                    onChange={(e) =>
                      setProfile({ ...profile, phone: e.target.value })
                    }
                    placeholder="+250 xxx xxx xxx"
                  />
                </div>
                <div className="form-group">
                  <label>District</label>
                  <input
                    type="text"
                    value={profile.district}
                    onChange={(e) =>
                      setProfile({ ...profile, district: e.target.value })
                    }
                    placeholder="Your district"
                  />
                </div>
              </div>

              <div className="form-actions">
                <button
                  className="btn btn-primary"
                  onClick={handleProfileSave}
                  disabled={saving}
                >
                  {saving ? (
                    <>
                      <i className="fas fa-spinner fa-spin"></i> Saving...
                    </>
                  ) : (
                    "Save Changes"
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Password Settings */}
          {activeTab === "password" && (
            <div className="settings-section">
              <h2>Change Password</h2>
              <p className="section-description">
                Ensure your account is secure with a strong password
              </p>

              <div className="form-stack">
                <div className="form-group">
                  <label>Current Password</label>
                  <input
                    type="password"
                    value={password.current}
                    onChange={(e) =>
                      setPassword({ ...password, current: e.target.value })
                    }
                    placeholder="Enter current password"
                  />
                </div>
                <div className="form-group">
                  <label>New Password</label>
                  <input
                    type="password"
                    value={password.newPassword}
                    onChange={(e) =>
                      setPassword({ ...password, newPassword: e.target.value })
                    }
                    placeholder="Enter new password"
                  />
                  <span className="help-text">Minimum 8 characters</span>
                </div>
                <div className="form-group">
                  <label>Confirm New Password</label>
                  <input
                    type="password"
                    value={password.confirm}
                    onChange={(e) =>
                      setPassword({ ...password, confirm: e.target.value })
                    }
                    placeholder="Confirm new password"
                  />
                </div>
              </div>

              <div className="form-actions">
                <button
                  className="btn btn-primary"
                  onClick={handlePasswordChange}
                  disabled={saving}
                >
                  {saving ? (
                    <>
                      <i className="fas fa-spinner fa-spin"></i> Changing...
                    </>
                  ) : (
                    "Change Password"
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Notification Settings */}
          {activeTab === "notifications" && (
            <div className="settings-section">
              <h2>Notification Preferences</h2>
              <p className="section-description">
                Control how you receive notifications
              </p>

              <div className="toggle-list">
                <div className="toggle-item">
                  <div className="toggle-info">
                    <h4>Email Alerts</h4>
                    <p>Receive email notifications for important updates</p>
                  </div>
                  <label className="toggle-switch">
                    <input
                      type="checkbox"
                      checked={notifications.emailAlerts}
                      onChange={(e) =>
                        setNotifications({
                          ...notifications,
                          emailAlerts: e.target.checked,
                        })
                      }
                    />
                    <span className="slider"></span>
                  </label>
                </div>

                <div className="toggle-item">
                  <div className="toggle-info">
                    <h4>Push Notifications</h4>
                    <p>Receive push notifications in your browser</p>
                  </div>
                  <label className="toggle-switch">
                    <input
                      type="checkbox"
                      checked={notifications.pushNotifications}
                      onChange={(e) =>
                        setNotifications({
                          ...notifications,
                          pushNotifications: e.target.checked,
                        })
                      }
                    />
                    <span className="slider"></span>
                  </label>
                </div>

                <div className="toggle-item">
                  <div className="toggle-info">
                    <h4>Weekly Digest</h4>
                    <p>Receive a weekly summary of activity</p>
                  </div>
                  <label className="toggle-switch">
                    <input
                      type="checkbox"
                      checked={notifications.weeklyDigest}
                      onChange={(e) =>
                        setNotifications({
                          ...notifications,
                          weeklyDigest: e.target.checked,
                        })
                      }
                    />
                    <span className="slider"></span>
                  </label>
                </div>

                <div className="toggle-item">
                  <div className="toggle-info">
                    <h4>Critical Alerts Only</h4>
                    <p>Only receive notifications for critical alerts</p>
                  </div>
                  <label className="toggle-switch">
                    <input
                      type="checkbox"
                      checked={notifications.criticalOnly}
                      onChange={(e) =>
                        setNotifications({
                          ...notifications,
                          criticalOnly: e.target.checked,
                        })
                      }
                    />
                    <span className="slider"></span>
                  </label>
                </div>
              </div>

              <div className="form-actions">
                <button
                  className="btn btn-primary"
                  onClick={handleNotificationsSave}
                  disabled={saving}
                >
                  {saving ? (
                    <>
                      <i className="fas fa-spinner fa-spin"></i> Saving...
                    </>
                  ) : (
                    "Save Preferences"
                  )}
                </button>
              </div>
            </div>
          )}

          {/* System Settings */}
          {activeTab === "system" && (
            <div className="settings-section">
              <h2>System Information</h2>
              <p className="section-description">
                Application details and configuration
              </p>

              <div className="info-list">
                <div className="info-item">
                  <label>Application</label>
                  <span>TrustBond Crime Reporting System</span>
                </div>
                <div className="info-item">
                  <label>Version</label>
                  <span>1.0.0</span>
                </div>
                <div className="info-item">
                  <label>Environment</label>
                  <span>Development</span>
                </div>
                <div className="info-item">
                  <label>API Endpoint</label>
                  <span>http://localhost:5000/api</span>
                </div>
                <div className="info-item">
                  <label>User Role</label>
                  <span>{user?.role || "Unknown"}</span>
                </div>
                <div className="info-item">
                  <label>Session ID</label>
                  <span>
                    {localStorage.getItem("token")?.substring(0, 20)}...
                  </span>
                </div>
              </div>

              <div className="danger-zone">
                <h3>Danger Zone</h3>
                <p>These actions are irreversible. Proceed with caution.</p>
                <button
                  className="btn btn-danger"
                  onClick={() => {
                    if (
                      window.confirm(
                        "Are you sure you want to clear all local data?",
                      )
                    ) {
                      localStorage.clear();
                      window.location.reload();
                    }
                  }}
                >
                  <i className="fas fa-trash"></i> Clear Local Data
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Settings;
