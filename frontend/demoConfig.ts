/// <reference types="vite/client" />

export const USE_DEMO_DATA: boolean =
  (import.meta.env.VITE_USE_DEMO_DATA ?? "false").toString().toLowerCase() === "true";

// DEMO_LOGIN enables automatic fallback to demo credentials (admin@aipeco.com)
// Set VITE_DEMO_LOGIN=true in .env.production to enable
export const DEMO_LOGIN: boolean =
  (import.meta.env.VITE_DEMO_LOGIN ?? "false").toString().toLowerCase() === "true";
