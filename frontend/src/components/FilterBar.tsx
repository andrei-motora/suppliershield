import { Search } from "lucide-react";
import type { ReactNode } from "react";
import Button from "./Button";

interface FilterBarProps {
  search: string;
  onSearchChange: (value: string) => void;
  searchPlaceholder?: string;
  resultCount?: number;
  /** Slot for filter controls (dropdowns, chips, etc.) */
  filters?: ReactNode;
  /** Show export button */
  onExport?: () => void;
  exportDisabled?: boolean;
}

export default function FilterBar({
  search,
  onSearchChange,
  searchPlaceholder = "Search...",
  resultCount,
  filters,
  onExport,
  exportDisabled,
}: FilterBarProps) {
  return (
    <div className="flex gap-3 flex-wrap items-center">
      {/* Search input */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-shield-dim pointer-events-none" />
        <input
          type="text"
          placeholder={searchPlaceholder}
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          className="bg-shield-surface border border-shield-border rounded-md pl-9 pr-3 py-2 text-sm text-shield-text placeholder:text-shield-dim w-64 focus:outline-none focus:border-shield-accent/40 transition-colors"
        />
      </div>

      {/* Optional filter controls */}
      {filters}

      {/* Result count */}
      {resultCount != null && (
        <span className="text-shield-muted text-sm tabular-nums">
          {resultCount} {resultCount === 1 ? "result" : "results"}
        </span>
      )}

      {/* Export button (pushed right) */}
      {onExport && (
        <div className="ml-auto">
          <Button variant="secondary" onClick={onExport} disabled={exportDisabled}>
            Export CSV
          </Button>
        </div>
      )}
    </div>
  );
}
