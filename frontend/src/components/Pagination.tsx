import { ChevronLeft, ChevronRight } from "lucide-react";

interface PaginationProps {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
}

export default function Pagination({ page, pageSize, total, onPageChange }: PaginationProps) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  if (totalPages <= 1) return null;

  const start = page * pageSize + 1;
  const end = Math.min((page + 1) * pageSize, total);

  return (
    <div className="flex items-center justify-between px-1 py-3 text-sm">
      <span className="text-shield-dim tabular-nums">
        {start}–{end} of {total}
      </span>
      <div className="flex items-center gap-1">
        <button
          disabled={page === 0}
          onClick={() => onPageChange(page - 1)}
          className="p-1.5 rounded hover:bg-white/[0.04] text-shield-muted disabled:opacity-30 disabled:pointer-events-none transition-colors"
          aria-label="Previous page"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
        {Array.from({ length: totalPages }).map((_, i) => {
          // Show first, last, and pages near current
          if (i !== 0 && i !== totalPages - 1 && Math.abs(i - page) > 1) {
            if (i === page - 2 || i === page + 2) {
              return <span key={i} className="text-shield-dim px-1">&hellip;</span>;
            }
            return null;
          }
          return (
            <button
              key={i}
              onClick={() => onPageChange(i)}
              className={`w-7 h-7 rounded text-xs font-medium transition-colors ${
                i === page
                  ? "bg-shield-accent/15 text-shield-accent border border-shield-accent/30"
                  : "text-shield-muted hover:text-shield-text hover:bg-white/[0.04]"
              }`}
            >
              {i + 1}
            </button>
          );
        })}
        <button
          disabled={page >= totalPages - 1}
          onClick={() => onPageChange(page + 1)}
          className="p-1.5 rounded hover:bg-white/[0.04] text-shield-muted disabled:opacity-30 disabled:pointer-events-none transition-colors"
          aria-label="Next page"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
