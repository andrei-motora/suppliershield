/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        shield: {
          bg: "#0a0e1a",
          surface: "#0d1220",
          border: "rgba(249,115,22,0.2)",
          accent: "#f97316",
          text: "#e2e8f0",
          muted: "#94a3b8",
          dim: "#64748b",
        },
        risk: {
          low: "#22c55e",
          medium: "#eab308",
          high: "#f97316",
          critical: "#ef4444",
          watch: "#3b82f6",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [],
};
