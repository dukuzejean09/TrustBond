// Test backend connection
export async function testBackendConnection() {
  const baseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
  const healthUrl = `${baseUrl}/health`;

  try {
    const response = await fetch(healthUrl);
    const data = await response.json();
    return { success: true, data };
  } catch (err) {
    return { success: false, error: err.message };
  }
}
