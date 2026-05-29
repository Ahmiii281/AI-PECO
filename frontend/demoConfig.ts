/// <reference types="vite/client" />
export const USE_DEMO_DATA: boolean =
  (import.meta.env.VITE_USE_DEMO_DATA ?? "false").toString().toLowerCase() === "true";

export const DEMO_LOGIN: boolean = true;
