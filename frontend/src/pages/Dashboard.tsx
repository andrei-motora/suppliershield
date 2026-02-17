import { useMemo, useState, useEffect, useCallback, lazy, Suspense } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import Plot from "react-plotly.js";
import { AlertTriangle, Users, ShieldAlert, Activity, ChevronRight, Loader2 } from "lucide-react";
import KPICard from "../components/KPICard";
import ErrorState from "../components/ErrorState";
import DashboardSkeleton from "../components/DashboardSkeleton";
import GlobeFilterBar from "../components/GlobeFilterBar";
import { fetchRiskOverview, fetchNetworkStats, fetchSPOFs, fetchNetworkGraph, fetchCountryAggregation, fetchRecommendations, ApiError } from "../api/client";
import { RISK_COLORS, TIER_COLORS } from "../constants";

const GlobeVisualization = lazy(() => import("../components/GlobeVisualization"));

export default function Dashboard() {
  const navigate = useNavigate();
  const overview = useQuery({ queryKey: ["riskOverview"], queryFn: fetchRiskOverview });
  const stats = useQuery({ queryKey: ["networkStats"], queryFn: fetchNetworkStats });
  const spofs = useQuery({ queryKey: ["spofs"], queryFn: fetchSPOFs });
  const graph = useQuery({ queryKey: ["networkGraph"], queryFn: fetchNetworkGraph });
  const urgentRecs = useQuery({
    queryKey: ["recommendations", "urgent"],
    queryFn: async () => {
      // Try CRITICAL first; fall back to HIGH if no critical actions exist
      const critical = await fetchRecommendations("CRITICAL");
      if (critical.length > 0) return { items: critical, level: "CRITICAL" as const };
      const high = await fetchRecommendations("HIGH");
      return { items: high, level: "HIGH" as const };
    },
  });

  // Globe filter states
  const [activeTiers, setActiveTiers] = useState<Set<number>>(new Set([1, 2, 3]));
  const [spofOnly, setSpofOnly] = useState(false);
  const [selectedCountry, setSelectedCountry] = useState("");
  const [riskRange, setRiskRange] = useState<[number, number]>([0, 100]);
  const [contractRange, setContractRange] = useState<[number, number]>([0, 100]);
  const [showArcs, setShowArcs] = useState(true);

  const countryAgg = useQuery({ queryKey: ["countryAggregation"], queryFn: fetchCountryAggregation });

  const countryOptions = useMemo(() => {
    if (!countryAgg.data) return [];
    return countryAgg.data.countries
      .map((c) => ({ code: c.country_code, name: c.country_name }))
      .sort((a, b) => a.name.localeCompare(b.name));
  }, [countryAgg.data]);

  const contractBounds = useMemo(() => {
    if (!graph.data) return { min: 0, max: 100 };
    const vals = graph.data.nodes.map((n) => n.contract_value);
    return {
      min: Math.floor(Math.min(...vals) * 10) / 10,
      max: Math.ceil(Math.max(...vals) * 10) / 10,
    };
  }, [graph.data]);

  // Initialize contract range when data loads
  useEffect(() => {
    if (graph.data) {
      setContractRange([contractBounds.min, contractBounds.max]);
    }
  }, [graph.data, contractBounds.min, contractBounds.max]);

  const handleToggleTier = useCallback((tier: number) => {
    setActiveTiers((prev) => {
      const next = new Set(prev);
      if (next.has(tier)) next.delete(tier);
      else next.add(tier);
      return next;
    });
  }, []);

  const handleResetFilters = useCallback(() => {
    setActiveTiers(new Set([1, 2, 3]));
    setSpofOnly(false);
    setSelectedCountry("");
    setRiskRange([0, 100]);
    setContractRange([contractBounds.min, contractBounds.max]);
    setShowArcs(true);
  }, [contractBounds.min, contractBounds.max]);

  // Pre-filter donut chart categories (must be before early returns to respect Rules of Hooks)
  const donutCategories = useMemo(
    () => overview.data ? Object.entries(overview.data.categories).filter(([, v]) => v > 0) : [],
    [overview.data]
  );

  // Filter graph nodes based on all 5 filters
  const visibleNodes = useMemo(() => {
    if (!graph.data) return [];
    return graph.data.nodes.filter((n) => {
      if (!activeTiers.has(n.tier)) return false;
      if (spofOnly && !n.is_spof) return false;
      if (selectedCountry && n.country_code !== selectedCountry) return false;
      if (n.risk < riskRange[0] || n.risk > riskRange[1]) return false;
      if (n.contract_value < contractRange[0] || n.contract_value > contractRange[1]) return false;
      return true;
    });
  }, [graph.data, activeTiers, spofOnly, selectedCountry, riskRange, contractRange]);

  const visibleNodeIds = useMemo(() => new Set(visibleNodes.map((n) => n.id)), [visibleNodes]);

  const visibleEdges = useMemo(() => {
    if (!graph.data) return [];
    return graph.data.edges.filter(
      (e) => visibleNodeIds.has(e.source) && visibleNodeIds.has(e.target)
    );
  }, [graph.data, visibleNodeIds]);

  // Redirect to upload page if no data has been loaded (404 from API)
  const noData =
    (overview.error instanceof ApiError && overview.error.status === 404) ||
    (stats.error instanceof ApiError && stats.error.status === 404);

  useEffect(() => {
    if (noData) navigate("/upload", { replace: true });
  }, [noData, navigate]);

  if (overview.isLoading || stats.isLoading || noData)
    return <DashboardSkeleton />;

  if (overview.isError)
    return <ErrorState message={overview.error.message} onRetry={() => overview.refetch()} />;
  if (stats.isError)
    return <ErrorState message={stats.error.message} onRetry={() => stats.refetch()} />;

  const ov = overview.data!;
  const st = stats.data!;
  const avgRiskColor = ov.avg_risk >= 75 ? "#ef4444" : ov.avg_risk >= 55 ? "#f97316" : ov.avg_risk >= 35 ? "#eab308" : "#22c55e";

  return (
    <div className="space-y-6 w-full">
      {/* KPI row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          label="Total Suppliers"
          value={st.total_nodes}
          subtitle="Across 3 tiers"
          icon={Users}
          onClick={() => navigate("/risk-rankings")}
        />
        <KPICard
          label="Critical Suppliers"
          value={ov.categories.CRITICAL ?? 0}
          subtitle={`${((ov.categories.CRITICAL ?? 0) / ov.total_suppliers * 100).toFixed(1)}% of network`}
          accent="#ef4444"
          icon={AlertTriangle}
          onClick={() => navigate("/risk-rankings?category=CRITICAL")}
        />
        <KPICard
          label="SPOFs Detected"
          value={spofs.data?.length ?? "..."}
          subtitle="Single Points of Failure"
          accent="#ef4444"
          icon={ShieldAlert}
        />
        <KPICard
          label="Avg Risk Score"
          value={ov.avg_risk.toFixed(1)}
          subtitle="/100"
          accent={avgRiskColor}
          icon={Activity}
          onClick={() => navigate("/sensitivity")}
        />
      </div>

      {/* Attention Required banner */}
      {urgentRecs.data && urgentRecs.data.items.length > 0 && (() => {
        const { items, level } = urgentRecs.data;
        const isCritical = level === "CRITICAL";
        const borderColor = isCritical ? "border-risk-critical/20" : "border-risk-high/20";
        const bgColor = isCritical ? "bg-risk-critical/5" : "bg-risk-high/5";
        const textColor = isCritical ? "text-risk-critical" : "text-risk-high";
        const pillBg = isCritical ? "bg-risk-critical/20" : "bg-risk-high/20";
        return (
          <div className={`${bgColor} border ${borderColor} rounded-lg p-4`}>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <AlertTriangle className={`w-4 h-4 ${textColor}`} />
                <h2 className={`text-sm font-semibold ${textColor}`}>
                  Attention Required -- {items.length} {level === "CRITICAL" ? "Critical" : "High Priority"} Actions
                </h2>
              </div>
              <button
                onClick={() => navigate("/recommendations")}
                className="text-xs text-shield-muted hover:text-shield-text flex items-center gap-1 transition-colors"
              >
                View all <ChevronRight className="w-3 h-3" />
              </button>
            </div>
            <div className="space-y-2">
              {items.slice(0, 3).map((rec, i) => (
                <div key={i} className="flex items-start gap-3 text-sm">
                  <span className={`shrink-0 w-5 h-5 rounded-full ${pillBg} ${textColor} flex items-center justify-center text-xs font-bold`}>
                    {i + 1}
                  </span>
                  <div className="min-w-0">
                    <span className="text-shield-text font-medium">{rec.supplier_name}</span>
                    <span className="text-shield-dim mx-1.5">--</span>
                    <span className="text-shield-muted">{rec.action}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })()}

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Risk bar (compact replacement for gauge) */}
        <div className="bg-shield-surface border border-shield-border rounded-lg p-4">
          <p className="text-xs uppercase tracking-wider text-shield-muted mb-3">Average Network Risk</p>
          <div className="flex items-end gap-3 mb-3">
            <span className="text-4xl font-mono font-bold" style={{ color: avgRiskColor }}>
              {ov.avg_risk.toFixed(1)}
            </span>
            <span className="text-shield-dim text-lg mb-1">/ 100</span>
          </div>
          <div className="w-full h-3 rounded-full bg-white/5 overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-700"
              style={{
                width: `${ov.avg_risk}%`,
                background: `linear-gradient(90deg, #22c55e 0%, #eab308 35%, #f97316 55%, #ef4444 75%)`,
              }}
            />
          </div>
          <div className="flex justify-between text-[10px] text-shield-dim mt-1.5">
            <span>Low</span>
            <span>Medium</span>
            <span>High</span>
            <span>Critical</span>
          </div>

          {/* Tier breakdown inline */}
          <div className="flex gap-3 mt-5 pt-4 border-t border-shield-border">
            {[1, 2, 3].map((tier) => (
              <div key={tier} className="flex-1 text-center">
                <div
                  className="text-xs font-semibold mb-0.5"
                  style={{ color: TIER_COLORS[tier - 1] }}
                >
                  Tier {tier}
                </div>
                <div className="text-lg font-mono text-shield-text">
                  {st.tier_counts[String(tier)] ?? 0}
                </div>
                <div className="text-[10px] text-shield-dim">suppliers</div>
              </div>
            ))}
          </div>
        </div>

        {/* Donut */}
        <div className="bg-shield-surface border border-shield-border rounded-lg p-2">
          <Plot
            data={[
              {
                type: "pie",
                labels: donutCategories.map(([k]) => k),
                values: donutCategories.map(([, v]) => v),
                hole: 0.6,
                marker: {
                  colors: donutCategories.map(([c]) => RISK_COLORS[c] ?? "#666"),
                  line: { color: "#0a0e1a", width: 2 },
                },
                textinfo: "label+percent",
                textfont: { size: 12, color: "#e2e8f0" },
                sort: false,
              },
            ]}
            layout={{
              height: 300,
              margin: { t: 40, b: 10, l: 10, r: 10 },
              paper_bgcolor: "transparent",
              plot_bgcolor: "transparent",
              font: { color: "#e2e8f0" },
              showlegend: true,
              legend: { orientation: "h", y: -0.1, x: 0.5, xanchor: "center", font: { color: "#94a3b8" } },
              title: { text: "Risk Category Distribution", font: { size: 14, color: "#94a3b8" } },
              annotations: [
                {
                  text: `<b>${ov.total_suppliers}</b><br>suppliers`,
                  showarrow: false,
                  font: { size: 20, color: "#e2e8f0", family: "JetBrains Mono" },
                },
              ],
            }}
            config={{ displayModeBar: false }}
            style={{ width: "100%" }}
          />
        </div>
      </div>

      {/* 3D Supply Chain Globe (countries + supplier nodes + dependency arcs) */}
      <Suspense
        fallback={
          <div className="bg-shield-surface border border-shield-border rounded-lg p-4 flex items-center justify-center" style={{ height: 640 }}>
            <Loader2 className="w-6 h-6 text-shield-accent animate-spin" />
          </div>
        }
      >
        <GlobeVisualization
          nodes={visibleNodes}
          edges={visibleEdges}
          showArcs={showArcs}
          filterBar={
            <GlobeFilterBar
              activeTiers={activeTiers}
              onToggleTier={handleToggleTier}
              spofOnly={spofOnly}
              onToggleSpof={() => setSpofOnly((v) => !v)}
              selectedCountry={selectedCountry}
              onSelectCountry={setSelectedCountry}
              countryOptions={countryOptions}
              riskRange={riskRange}
              onRiskRangeChange={setRiskRange}
              contractRange={contractRange}
              onContractRangeChange={setContractRange}
              contractBounds={contractBounds}
              showArcs={showArcs}
              onToggleArcs={() => setShowArcs((v) => !v)}
              visibleCount={visibleNodes.length}
              totalCount={graph.data?.nodes.length ?? 0}
              onReset={handleResetFilters}
            />
          }
        />
      </Suspense>
    </div>
  );
}
