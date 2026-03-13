import { formatApiLocation, API_BASE_URL } from "../config/api.js";

// Test backend connection
export async function testBackendConnection() {
  const healthUrl = `${API_BASE_URL}/health`;

  try {
    const response = await fetch(healthUrl);
    const data = await response.json();
    return { success: true, data, baseUrl: formatApiLocation() };
  } catch (err) {
    return { success: false, error: err.message, baseUrl: formatApiLocation() };
  }
}
