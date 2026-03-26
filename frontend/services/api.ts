/**
 * API Service - Handles all communication with backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Get token from localStorage
const getToken = () => localStorage.getItem("access_token");

// Generic API request handler
const apiCall = async (
  endpoint: string,
  method: string = "GET",
  data?: any,
  headers?: any
) => {
  const token = getToken();

  const options: RequestInit = {
    method,
    headers: {
      "Content-Type": "application/json",
      ...headers,
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  };

  if (data) {
    options.body = JSON.stringify(data);
  }

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, options);

    if (!response.ok) {
      if (response.status === 401) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("user");
        window.location.href = "/login";
      }
      throw new Error(`HTTP Error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API Error [${method} ${endpoint}]:`, error);
    throw error;
  }
};

// ==================== Authentication ====================
export const authAPI = {
  register: (name: string, email: string, password: string) =>
    apiCall("/api/auth/register", "POST", { name, email, password }),

  login: (email: string, password: string) =>
    apiCall("/api/auth/login", "POST", { email, password }),

  getProfile: () => apiCall("/api/auth/me", "GET"),
};

// ==================== Devices ====================
export const deviceAPI = {
  getAll: () => apiCall("/api/devices", "GET"),

  create: (name: string, location: string, relay_pin?: number) =>
    apiCall("/api/devices", "POST", { name, location, relay_pin }),

  getOne: (deviceId: string) =>
    apiCall(`/api/devices/${deviceId}`, "GET"),

  update: (deviceId: string, data: any) =>
    apiCall(`/api/devices/${deviceId}`, "PUT", data),

  delete: (deviceId: string) =>
    apiCall(`/api/devices/${deviceId}`, "DELETE"),
};

// ==================== Energy Data ====================
export const energyAPI = {
  getDeviceHistory: (deviceId: string, hours: number = 24) =>
    apiCall(`/api/energy/device/${deviceId}?hours=${hours}`, "GET"),

  getAlerts: (resolved: boolean = false) =>
    apiCall(`/api/energy/alerts?resolved=${resolved}`, "GET"),

  createAlert: (message: string, alertType: string = "warning") =>
    apiCall("/api/energy/alerts", "POST", { message, alert_type: alertType }),

  resolveAlert: (alertId: string) =>
    apiCall(`/api/energy/alerts/${alertId}`, "PUT"),
};

// ==================== Dashboard ====================
export const dashboardAPI = {
  getStats: () => apiCall("/api/dashboard/stats", "GET"),

  controlRelay: (deviceId: string, command: "ON" | "OFF") =>
    apiCall(`/api/dashboard/relay/${deviceId}`, "POST", { device_id: deviceId, command }),

  getRecommendation: (deviceId: string) =>
    apiCall(`/api/dashboard/recommendation/${deviceId}`, "GET"),

  getDeviceCommand: (deviceId: string) =>
    apiCall(`/api/dashboard/device-command/${deviceId}`, "GET"),
};

// ==================== Billing ====================
export const billingAPI = {
  getCategories: () => apiCall("/api/billing/categories"),
  estimate: (data: any) => apiCall("/api/billing/estimate", "POST", data),
};

// ==================== Health Check ====================
export const healthAPI = {
  check: () =>
    fetch(`${API_BASE_URL}/health`)
      .then((res) => res.json())
      .catch(() => ({ status: "unavailable" })),
};
