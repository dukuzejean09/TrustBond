import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import { login, adminExists, bootstrapAdmin } from "../lib/api";

export default function Login() {
  const router = useRouter();
  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("password");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [noUsers, setNoUsers] = useState<boolean | null>(null);
  const [setupMode, setSetupMode] = useState(false);
  const [creating, setCreating] = useState(false);
  const [setupError, setSetupError] = useState<string | null>(null);
  const [firstName, setFirstName] = useState("Admin");
  const [lastName, setLastName] = useState("User");

  useEffect(() => {
    let mounted = true;
    adminExists()
      .then((r: any) => {
        if (!mounted) return;
        setNoUsers(!r.exists);
      })
      .catch(() => setNoUsers(false));
    return () => (mounted = false);
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const resp: any = await login(email, password);
      localStorage.setItem("tb_token", resp.access_token);
      router.push("/");
    } catch (err: any) {
      setError(err?.message || "Login failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleBootstrap(e: React.FormEvent) {
    e.preventDefault();
    setSetupError(null);
    setCreating(true);
    try {
      await bootstrapAdmin({
        first_name: firstName,
        last_name: lastName,
        email,
        password,
        role: "admin",
      });
      // auto-login after successful bootstrap
      const tokenResp: any = await login(email, password);
      localStorage.setItem("tb_token", tokenResp.access_token);
      router.push("/");
    } catch (err: any) {
      setSetupError(err?.message || "Failed to create admin");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div
      style={{
        display: "flex",
        minHeight: "100vh",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <div className="card" style={{ width: 420 }}>
        <div style={{ marginBottom: 12 }} className="brand">
          TrustBond — Dashboard
        </div>

        {noUsers === null ? (
          <div className="small-muted" style={{ marginBottom: 12 }}>
            Checking system state…
          </div>
        ) : null}

        {noUsers && (
          <div style={{ marginBottom: 12 }} className="card">
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <strong>First-time setup</strong>
              <div className="small-muted">No users found</div>
            </div>
            {!setupMode ? (
              <div style={{ marginTop: 8 }}>
                <div className="small-muted">
                  Create the first admin account to manage the system.
                </div>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "flex-end",
                    marginTop: 12,
                  }}
                >
                  <button className="button" onClick={() => setSetupMode(true)}>
                    Create admin
                  </button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleBootstrap} style={{ marginTop: 8 }}>
                <label className="small-muted">First name</label>
                <input
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  style={{
                    width: "100%",
                    padding: 8,
                    marginTop: 6,
                    borderRadius: 6,
                  }}
                />
                <label className="small-muted" style={{ marginTop: 8 }}>
                  Last name
                </label>
                <input
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  style={{
                    width: "100%",
                    padding: 8,
                    marginTop: 6,
                    borderRadius: 6,
                  }}
                />
                <label className="small-muted" style={{ marginTop: 8 }}>
                  Email
                </label>
                <input
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  style={{
                    width: "100%",
                    padding: 8,
                    marginTop: 6,
                    borderRadius: 6,
                  }}
                />
                <label className="small-muted" style={{ marginTop: 8 }}>
                  Password
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  style={{
                    width: "100%",
                    padding: 8,
                    marginTop: 6,
                    borderRadius: 6,
                  }}
                />
                {setupError && (
                  <div style={{ color: "#ffb4b4", marginTop: 8 }}>
                    {setupError}
                  </div>
                )}
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginTop: 12,
                  }}
                >
                  <button className="button" type="submit" disabled={creating}>
                    {creating ? "Creating…" : "Create admin & sign in"}
                  </button>
                  <button
                    className="small-muted"
                    type="button"
                    onClick={() => setSetupMode(false)}
                    style={{
                      background: "transparent",
                      border: "none",
                      cursor: "pointer",
                    }}
                  >
                    Cancel
                  </button>
                </div>
              </form>
            )}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <label className="small-muted">Email</label>
          <input
            autoFocus
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={{
              width: "100%",
              padding: 10,
              marginTop: 6,
              borderRadius: 6,
              border: "1px solid rgba(255,255,255,0.03)",
              background: "transparent",
              color: "inherit",
            }}
          />
          <label className="small-muted" style={{ marginTop: 10 }}>
            Password
          </label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{
              width: "100%",
              padding: 10,
              marginTop: 6,
              borderRadius: 6,
              border: "1px solid rgba(255,255,255,0.03)",
              background: "transparent",
              color: "inherit",
            }}
          />
          {error && (
            <div style={{ color: "#ffb4b4", marginTop: 8 }}>{error}</div>
          )}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginTop: 12,
            }}
          >
            <div className="small-muted">
              Use an existing police user account
            </div>
            <button className="button" type="submit" disabled={loading}>
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
