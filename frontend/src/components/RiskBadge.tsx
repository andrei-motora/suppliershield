import type { RiskCategory, Severity } from "../types";

const BADGE_STYLES: Record<string, string> = {
  LOW: "bg-risk-low/20 text-risk-low border-risk-low/30",
  MEDIUM: "bg-risk-medium/20 text-risk-medium border-risk-medium/30",
  HIGH: "bg-risk-high/20 text-risk-high border-risk-high/30",
  CRITICAL: "bg-risk-critical/20 text-risk-critical border-risk-critical/30",
  WATCH: "bg-blue-500/20 text-blue-400 border-blue-500/30",
};

export default function RiskBadge({
  level,
}: {
  level: RiskCategory | Severity;
}) {
  const cls = BADGE_STYLES[level] ?? BADGE_STYLES.MEDIUM;
  return (
    <span
      className={`inline-block px-2 py-0.5 rounded text-xs font-semibold border ${cls}`}
    >
      {level}
    </span>
  );
}
