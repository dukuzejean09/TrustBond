const DEFAULT_API_BASE_URL = "https://trustbond-backend.onrender.com";
const LEGACY_BACKEND_HOSTS = new Set(["trustbond.onrender.com"]);

function normalizeApiBaseUrl(rawUrl) {
  const candidate = (rawUrl || "").trim() || DEFAULT_API_BASE_URL;
  const withScheme = /^https?:\/\//i.test(candidate)
    ? candidate
    : `https://${candidate}`;

  try {
    const parsed = new URL(withScheme);
    if (LEGACY_BACKEND_HOSTS.has(parsed.hostname)) {
      parsed.hostname = "trustbond-backend.onrender.com";
    }
    return parsed.origin;
  } catch {
    return DEFAULT_API_BASE_URL;
  }
}

export const API_BASE_URL = normalizeApiBaseUrl(
  typeof import.meta !== "undefined" ? import.meta.env?.VITE_API_BASE_URL : "",
);
