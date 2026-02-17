import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

interface KPICardProps {
  label: string;
  value: string | number;
  subtitle?: string;
  /** Accent color for the left border and value text (Tailwind color class without the prefix) */
  accent?: string;
  /** Lucide icon to display next to the label */
  icon?: LucideIcon;
  /** Make the card clickable */
  onClick?: () => void;
  /** Optional content rendered below the value */
  children?: ReactNode;
}

export default function KPICard({ label, value, subtitle, accent, icon: Icon, onClick, children }: KPICardProps) {
  const Wrapper = onClick ? "button" : "div";
  return (
    <Wrapper
      onClick={onClick}
      className={`bg-shield-surface border border-shield-border rounded-lg p-4 text-left transition-colors ${
        accent ? "border-l-4" : ""
      } ${
        onClick ? "cursor-pointer hover:bg-white/[0.03] hover:border-shield-accent/40" : ""
      }`}
      style={accent ? { borderLeftColor: accent } : undefined}
    >
      <div className="flex items-center gap-1.5 mb-1">
        {Icon && <Icon className="w-3.5 h-3.5 text-shield-dim" />}
        <p className="text-xs uppercase tracking-wider text-shield-muted">
          {label}
        </p>
      </div>
      <p
        className="text-2xl font-mono font-semibold"
        style={accent ? { color: accent } : undefined}
      >
        <span className={accent ? "" : "text-shield-text"}>{value}</span>
      </p>
      {subtitle && (
        <p className="text-xs text-shield-dim mt-1">{subtitle}</p>
      )}
      {children}
    </Wrapper>
  );
}
