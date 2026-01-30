import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "../styles/Login.css";

const Login = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || "/dashboard";

  // Redirect if already authenticated
  React.useEffect(() => {
    if (isAuthenticated) {
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, from]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    const result = await login(email, password);

    if (result.success) {
      navigate(from, { replace: true });
    } else {
      setError(result.error);
    }

    setLoading(false);
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-branding">
          <div className="logo">
            <div className="logo-icon">
              <i className="fas fa-shield-halved"></i>
            </div>
            <div className="logo-text">
              <span className="trust">Trust</span>
              <span className="bond">Bond</span>
              <small>Rwanda National Police</small>
            </div>
          </div>

          <p>
            Secure Crime Reporting & Community Safety Platform. Empowering
            citizens and law enforcement to build safer communities together.
          </p>

          <ul className="features">
            <li>
              <i className="fas fa-check"></i>
              <span>Real-time crime reporting</span>
            </li>
            <li>
              <i className="fas fa-check"></i>
              <span>Anonymous submission option</span>
            </li>
            <li>
              <i className="fas fa-check"></i>
              <span>AI-powered trust scoring</span>
            </li>
            <li>
              <i className="fas fa-check"></i>
              <span>Crime hotspot detection</span>
            </li>
            <li>
              <i className="fas fa-check"></i>
              <span>End-to-end encryption</span>
            </li>
          </ul>
        </div>

        <div className="login-form-section">
          <h2>Welcome Back</h2>
          <p className="subtitle">Sign in to access your dashboard</p>

          {error && (
            <div className="login-error">
              <i className="fas fa-exclamation-circle"></i>
              {error}
            </div>
          )}

          <form className="login-form" onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="email">Email Address</label>
              <div className="input-group">
                <i className="fas fa-envelope"></i>
                <input
                  type="email"
                  id="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@rnp.gov.rw"
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>
              <div className="input-group">
                <i className="fas fa-lock"></i>
                <input
                  type="password"
                  id="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  required
                />
              </div>
            </div>

            <button type="submit" className="btn-login" disabled={loading}>
              {loading ? (
                <>
                  <i className="fas fa-spinner fa-spin"></i> Signing in...
                </>
              ) : (
                <>
                  <i className="fas fa-sign-in-alt"></i> Sign In
                </>
              )}
            </button>
          </form>

          <div className="demo-credentials">
            <h4>
              <i className="fas fa-info-circle"></i> Demo Credentials
            </h4>
            <p>
              Email: <code>admin@rnp.gov.rw</code>
            </p>
            <p>
              Password: <code>admin123</code>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
