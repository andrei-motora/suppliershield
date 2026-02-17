/** Skeleton loading screen that mirrors the Dashboard layout. */
export default function DashboardSkeleton() {
  return (
    <div className="space-y-6 w-full animate-pulse">
      {/* KPI row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-shield-surface border border-shield-border rounded-lg p-4">
            <div className="h-3 w-24 bg-white/5 rounded mb-3" />
            <div className="h-7 w-16 bg-white/10 rounded mb-2" />
            <div className="h-2.5 w-20 bg-white/5 rounded" />
          </div>
        ))}
      </div>

      {/* Attention banner skeleton */}
      <div className="bg-white/[0.02] border border-shield-border rounded-lg p-4">
        <div className="h-4 w-56 bg-white/5 rounded mb-3" />
        <div className="space-y-2">
          <div className="h-3 w-full bg-white/5 rounded" />
          <div className="h-3 w-4/5 bg-white/5 rounded" />
          <div className="h-3 w-3/5 bg-white/5 rounded" />
        </div>
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-shield-surface border border-shield-border rounded-lg p-4">
          <div className="h-3 w-32 bg-white/5 rounded mb-4" />
          <div className="h-10 w-24 bg-white/10 rounded mb-3" />
          <div className="h-3 w-full bg-white/5 rounded mb-6" />
          <div className="flex gap-3 pt-4 border-t border-shield-border">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex-1 text-center">
                <div className="h-2.5 w-10 bg-white/5 rounded mx-auto mb-1" />
                <div className="h-6 w-8 bg-white/10 rounded mx-auto" />
              </div>
            ))}
          </div>
        </div>
        <div className="bg-shield-surface border border-shield-border rounded-lg h-[340px]" />
      </div>

      {/* Graph skeleton */}
      <div className="bg-shield-surface border border-shield-border rounded-lg h-[520px] flex items-center justify-center">
        <div className="text-shield-dim text-sm">Loading network graph...</div>
      </div>
    </div>
  );
}
