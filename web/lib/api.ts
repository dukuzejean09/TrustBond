const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

async function handleResp(res: Response) {
  const txt = await res.text();
  try {
    return JSON.parse(txt || "{}");
  } catch (e) {
    return txt;
  }
}

function authHeader() {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("tb_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function login(email: string, password: string) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error((await res.json()).detail || "Login failed");
  return handleResp(res);
}

export async function getReports(
  page = 1,
  per_page = 10,
  filters: Record<string, any> = {},
) {
  const params = new URLSearchParams({
    page: String(page),
    per_page: String(per_page),
  });
  Object.entries(filters).forEach(([k, v]) => {
    if (v !== undefined && v !== null) params.set(k, String(v));
  });
  const res = await fetch(`${API_BASE}/reports?${params.toString()}`, {
    headers: { "Content-Type": "application/json", ...authHeader() },
  });
  if (!res.ok) throw new Error("Failed to load reports");
  return handleResp(res);
}

export async function getReport(reportId: string) {
  const res = await fetch(`${API_BASE}/reports/${reportId}`, {
    headers: { "Content-Type": "application/json", ...authHeader() },
  });
  if (!res.ok) throw new Error("Report not found");
  return handleResp(res);
}

export async function getReportCount(filters: Record<string, any> = {}) {
  // Use reports endpoint with per_page=1 to read `total`
  const resp = await getReports(1, 1, filters);
  return resp.total ?? 0;
}

export async function getAssignments(status?: string, policeUserId?: number) {
  const params = new URLSearchParams();
  if (status) params.set("status_filter", status); // backend expects `status_filter`
  if (typeof policeUserId !== "undefined")
    params.set("police_user_id", String(policeUserId));
  const qs = params.toString() ? `?${params.toString()}` : "";
  const res = await fetch(`${API_BASE}/report-assignments${qs}`, {
    headers: { "Content-Type": "application/json", ...authHeader() },
  });
  if (!res.ok) return [];
  return handleResp(res);
}

export async function getHotspots() {
  const res = await fetch(`${API_BASE}/hotspots`, {
    headers: { "Content-Type": "application/json", ...authHeader() },
  });
  if (!res.ok) return [];
  return handleResp(res);
}

// Check whether any police users exist (public). Used by first-time bootstrap UI.
export async function adminExists() {
  const res = await fetch(`${API_BASE}/police-users/exists`, {
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) return { exists: true };
  return handleResp(res);
}

// Create the first admin account (bootstrap). Public but only allowed when no users exist.
export async function bootstrapAdmin(data: {
  first_name: string;
  last_name: string;
  middle_name?: string | null;
  email: string;
  password: string;
  phone_number?: string | null;
  badge_number?: string | null;
  role?: string;
}) {
  const res = await fetch(`${API_BASE}/police-users/bootstrap`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error((await res.json()).detail || "Bootstrap failed");
  return handleResp(res);
}
