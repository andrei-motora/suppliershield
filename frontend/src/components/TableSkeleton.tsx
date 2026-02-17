/** Skeleton for a data table, showing shimmering rows. */
export default function TableSkeleton({ rows = 8, cols = 6 }: { rows?: number; cols?: number }) {
  return (
    <div className="bg-shield-surface border border-shield-border rounded-lg overflow-hidden animate-pulse">
      {/* Header */}
      <div className="flex gap-4 px-4 py-3 border-b border-shield-border">
        {Array.from({ length: cols }).map((_, i) => (
          <div key={i} className="h-3 bg-white/5 rounded flex-1" />
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} className="flex gap-4 px-4 py-3 border-b border-white/5">
          {Array.from({ length: cols }).map((_, c) => (
            <div
              key={c}
              className="h-3 bg-white/5 rounded flex-1"
              style={{ maxWidth: c === 0 ? 60 : undefined }}
            />
          ))}
        </div>
      ))}
    </div>
  );
}
