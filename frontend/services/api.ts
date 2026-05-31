/**
 * API Service — handles all HTTP communication with the AI-PECO backend.
 *
 * Features:
 * - Automatic retry on transient failures (network errors, 503, 429, 502)
 * - Exponential backoff: 1s, 2s, 4s
 * - Per-call timeout (default 15s; cold-start aware)
 * - Graceful Render/Railway cold-start handling
 * - User-friendly error classification
 * - Smart analysis uses POST (not GET) for privacy
 */

const rawApiUrl = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL;
const API_BASE_URL = (rawApiUrl?.toString().trim().replace(/\/+$/, "")) || "http://localhost:8000";

const DEFAULT_TIMEOUT_MS = 15_000;
const COLD_START_TIMEOUT_MS = 30_000; // Render free tier can take ~25s to wake
const MAX_RETRIES = 3;
const RETRY_STATUSES = new Set([429, 502, 503, 504]);

// ─── Auth token ──────────────────────────────────────────────────────────────
const getToken = (): string | null => localStorage.getItem("access_token");

// ─── Sleep helper ─────────────────────────────────────────────────────────────
const sleep = (ms: number): Promise<void> =>
  new Promise((resolve) => setTimeout(resolve, ms));

// ─── Fetch with timeout ───────────────────────────────────────────────────────
async function fetchWithTimeout(
  url: string,
  options: RequestInit,
  timeoutMs: number
): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, { ...options, signal: controller.signal });
    return response;
  } finally {
    clearTimeout(timer);
  }
}

// ─── Error classification ─────────────────────────────────────────────────────
function classifyError(err: unknown, status?: number): string {
  if (err instanceof DOMException && err.name === "AbortError") {
    return "Request timed out. The server may be starting up — please try again in a moment.";
  }
  if (!navigator.onLine) {
    return "No internet connection. Please check your network.";
  }
  if (status === 401) return "Session expired. Please log in again.";
  if (status === 403) return "You do not have permission to perform this action.";
  if (status === 404) return "The requested resource was not found.";
  if (status === 422) return "Invalid request data. Please check your input.";
  if (status === 429) return "Too many requests. Please wait a moment and try again.";
  if (status === 503) return "Server is starting up. Retrying automatically…";
  if (status != null && status >= 500) {
    return "Server error. Our team has been notified. Please try again later.";
  }
  if (err instanceof TypeError && err.message.includes("Failed to fetch")) {
    return "Cannot reach the server. It may be starting up (Render cold start) — retrying…";
  }
  return (err as Error)?.message || "An unexpected error occurred.";
}

// ─── Core API call with retry ─────────────────────────────────────────────────
async function apiCall<T = unknown>(
  endpoint: string,
  method: string = "GET",
  data?: unknown,
  extraHeaders?: Record<string, string>,
  options: { timeoutMs?: number; retries?: number } = {}
): Promise<T> {
  const { timeoutMs = DEFAULT_TIMEOUT_MS, retries = MAX_RETRIES } = options;
  const token = getToken();
  const url = `${API_BASE_URL}${endpoint}`;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...extraHeaders,
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  const fetchOptions: RequestInit = {
    method,
    headers,
    ...(data !== undefined ? { body: JSON.stringify(data) } : {}),
  };

  let lastError: unknown;

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const response = await fetchWithTimeout(url, fetchOptions, timeoutMs);

      // Handle 401 globally (token expiry)
      if (response.status === 401) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("user");
        window.location.href = "/login";
        throw new Error("Session expired.");
      }

      // Retry on transient server errors
      if (RETRY_STATUSES.has(response.status) && attempt < retries) {
        const delay = Math.pow(2, attempt) * 1000; // 1s, 2s, 4s
        console.warn(
          `[API] ${method} ${endpoint} → ${response.status}. Retrying in ${delay}ms (attempt ${attempt + 1}/${retries})…`
        );
        await sleep(delay);
        lastError = new Error(classifyError(null, response.status));
        continue;
      }

      if (!response.ok) {
        let errorMessage = classifyError(null, response.status);
        try {
          const errorData = await response.json();
          if (errorData?.detail) {
            errorMessage =
              typeof errorData.detail === "string"
                ? errorData.detail
                : JSON.stringify(errorData.detail);
          }
        } catch {
          // Response body is not JSON — use classified message
        }
        throw new Error(errorMessage);
      }

      // Success — parse JSON
      const contentType = response.headers.get("Content-Type") || "";
      if (contentType.includes("application/json")) {
        return await response.json();
      }
      return {} as unknown as T;
    } catch (err) {
      // Network/timeout error — retry if attempts remain
      const isRetryable =
        err instanceof TypeError ||
        (err instanceof DOMException && err.name === "AbortError");

      if (isRetryable && attempt < retries) {
        const delay = Math.pow(2, attempt) * 1000;
        console.warn(
          `[API] ${method} ${endpoint} network error. Retrying in ${delay}ms (attempt ${attempt + 1}/${retries})…`,
          err
        );
        await sleep(delay);
        lastError = err;
        continue;
      }

      lastError = err;
      break;
    }
  }

  // All retries exhausted
  const msg = classifyError(lastError);
  console.error(`[API] ${method} ${endpoint} failed after ${retries + 1} attempts:`, lastError);
  throw new Error(msg);
}

// ─── Authentication ───────────────────────────────────────────────────────────
export const authAPI = {
  register: (name: string, email: string, password: string) =>
    apiCall<any>("/api/auth/register", "POST", { name, email, password }),

  login: (email: string, password: string) =>
    apiCall<any>("/api/auth/login", "POST", { email, password }),

  forgotPassword: (email: string) =>
    apiCall<any>("/api/auth/forgot-password", "POST", { email }),

  resetPassword: (token: string, newPassword: string) =>
    apiCall<any>("/api/auth/reset-password", "POST", { token, new_password: newPassword }),

  getProfile: () => apiCall<any>("/api/auth/me", "GET"),
};

// ─── Devices ──────────────────────────────────────────────────────────────────
export const deviceAPI = {
  getAll: () => apiCall<any[]>("/api/devices", "GET"),

  create: (name: string, location: string, relay_pin?: number) =>
    apiCall<any>("/api/devices", "POST", { name, location, relay_pin }),

  getOne: (deviceId: string) => apiCall<any>(`/api/devices/${deviceId}`, "GET"),

  update: (deviceId: string, data: unknown) =>
    apiCall<any>(`/api/devices/${deviceId}`, "PUT", data),

  delete: (deviceId: string) => apiCall<any>(`/api/devices/${deviceId}`, "DELETE"),
};

// ─── Energy Data ──────────────────────────────────────────────────────────────
export const energyAPI = {
  getDeviceHistory: (deviceId: string, hours: number = 24) =>
    apiCall<any[]>(`/api/energy/device/${deviceId}?hours=${hours}`, "GET"),

  getAlerts: (resolved: boolean = false) =>
    apiCall<any[]>(`/api/energy/alerts?resolved=${resolved}`, "GET"),

  createAlert: (message: string, alertType: string = "warning") =>
    apiCall<any>("/api/energy/alerts", "POST", { message, alert_type: alertType }),

  resolveAlert: (alertId: string) =>
    apiCall<any>(`/api/energy/alerts/${alertId}`, "PUT"),
};

// ─── Dashboard ────────────────────────────────────────────────────────────────
export const dashboardAPI = {
  getStats: () =>
    apiCall<any>("/api/dashboard/stats", "GET", undefined, undefined, {
      timeoutMs: COLD_START_TIMEOUT_MS, // first load can be slow on Render
    }),

  controlRelay: (deviceId: string, command: "ON" | "OFF") =>
    apiCall<any>(`/api/dashboard/relay/${deviceId}`, "POST", { device_id: deviceId, command }),

  getRecommendation: (deviceId: string) =>
    apiCall<any>(`/api/dashboard/recommendation/${deviceId}`, "GET"),

  getDeviceCommand: (deviceId: string) =>
    apiCall<any>(`/api/dashboard/device-command/${deviceId}`, "GET"),
};

// ─── Billing ──────────────────────────────────────────────────────────────────
export const billingAPI = {
  getCategories: () => apiCall<any[]>("/api/billing/categories"),
  estimate: (data: unknown) => apiCall<any>("/api/billing/estimate", "POST", data),
};

// ─── Predictions / AI ─────────────────────────────────────────────────────────
export const predictionsAPI = {
  getForecast: (deviceId: string) =>
    apiCall<any>(`/api/predictions/forecast/${deviceId}`, "GET"),

  getDisaggregation: (deviceId: string) =>
    apiCall<any>(`/api/predictions/disaggregate/${deviceId}`, "GET"),

  getRLSuggestion: () => apiCall<any>("/api/predictions/rl-suggestion", "GET"),

  /**
   * Smart analysis — uses POST to keep query out of URL/access logs.
   * Backend: POST /api/predictions/smart-analysis  { query: string }
   */
  getSmartAnalysis: (query: string) =>
    apiCall<any>("/api/predictions/smart-analysis", "POST", { query }),
};

// ─── Health Check ─────────────────────────────────────────────────────────────
export const healthAPI = {
  check: () =>
    fetchWithTimeout(`${API_BASE_URL}/health`, {}, 8_000)
      .then((res) => res.json())
      .catch(() => ({ status: "unavailable" })),
};

// ─── Default export (named group) ─────────────────────────────────────────────
const apiClient = {
  auth: authAPI,
  devices: deviceAPI,
  energy: energyAPI,
  dashboard: dashboardAPI,
  billing: billingAPI,
  predictions: predictionsAPI,
  health: healthAPI,
};

export default apiClient;