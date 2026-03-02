export const USE_DEMO_DATA: boolean =
  (import.meta.env.VITE_USE_DEMO_DATA ?? "true").toString().toLowerCase() === "true";

