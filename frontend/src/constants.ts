/** Shared color constants used across charts and components. */

export const RISK_COLORS: Record<string, string> = {
  LOW: "#22c55e",
  MEDIUM: "#eab308",
  HIGH: "#f97316",
  CRITICAL: "#ef4444",
};

export const SEVERITY_COLORS: Record<string, string> = {
  CRITICAL: "#ef4444",
  HIGH: "#f97316",
  MEDIUM: "#eab308",
  WATCH: "#3b82f6",
};

export const TIER_COLORS = ["#f97316", "#3b82f6", "#8b5cf6"];

/** Lat/Lng coordinates for supplier countries (approximate centroids). */
export const COUNTRY_COORDINATES: Record<string, { lat: number; lng: number }> = {
  CN: { lat: 30.6, lng: 104.1 },
  DE: { lat: 51.2, lng: 10.4 },
  MY: { lat: 4.2, lng: 101.9 },
  TW: { lat: 23.7, lng: 120.9 },
  NL: { lat: 52.1, lng: 5.3 },
  VN: { lat: 14.1, lng: 108.3 },
  PL: { lat: 51.9, lng: 19.1 },
  TH: { lat: 15.9, lng: 100.9 },
  US: { lat: 37.1, lng: -95.7 },
  JP: { lat: 36.2, lng: 138.3 },
  KR: { lat: 35.9, lng: 127.8 },
  CH: { lat: 46.8, lng: 8.2 },
  IN: { lat: 20.6, lng: 78.9 },
  CD: { lat: -4.0, lng: 21.8 },
};

/** Shared Plotly chart theme for consistent dark styling. */
export const CHART_THEME = {
  paper_bgcolor: "transparent",
  plot_bgcolor: "transparent",
  font: { color: "#e2e8f0" },
  gridColor: "rgba(255,255,255,0.05)",
  mutedColor: "#94a3b8",
  bgColor: "#0a0e1a",
  accentColor: "#f97316",
} as const;
