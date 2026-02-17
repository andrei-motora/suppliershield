import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import Plot from "react-plotly.js";
import { fetchRecommendations, fetchRecommendationSummary } from "../api/client";
import RiskBadge from "../components/RiskBadge";
import KPICard from "../components/KPICard";
import ErrorState from "../components/ErrorState";
import EmptyState from "../components/EmptyState";
import PageHeader from "../components/PageHeader";
import FilterBar from "../components/FilterBar";
import TableSkeleton from "../components/TableSkeleton";
import Pagination from "../components/Pagination";
import { SEVERITY_COLORS } from "../constants";
import { exportCsv } from "../utils/exportCsv";

const PAGE_SIZE = 25;

export default function Recommendations() {
  const [severityFilter, setSeverityFilter] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(0);

  const { data: recs, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["recommendations", severityFilter],
    queryFn: () => fetchRecommendations(severityFilter || undefined),
  });
  const { data: summary } = useQuery({
    queryKey: ["recSummary"],
    queryFn: fetchRecommendationSummary,
  });

  const filtered = useMemo(() => {
    if (!recs) return [];
    if (!search) return recs;
    const q = search.toLowerCase();
    return recs.filter(
      (r) =>
        r.supplier_id.toLowerCase().includes(q) ||
        r.supplier_name.toLowerCase().includes(q) ||
        r.action.toLowerCase().includes(q) ||
        r.country.toLowerCase().includes(q)
    );
  }, [recs, search]);

  const paged = useMemo(
    () => filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE),
    [filtered, page]
  );

  if (isError)
    return <ErrorState message={error.message} onRetry={() => refetch()} />;

  const handleSearchChange = (v: string) => { setSearch(v); setPage(0); };

  const severityCountsRaw = summary
    ? {
        CRITICAL: summary.critical_count,
        HIGH: summary.high_count,
        MEDIUM: summary.medium_count,
        WATCH: summary.watch_count,
      }
    : {};

  const severityCounts = Object.fromEntries(
    Object.entries(severityCountsRaw).filter(([, v]) => v > 0)
  );

  const handleExport = () => {
    exportCsv(
      filtered.map((r) => ({
        Severity: r.severity,
        Supplier_ID: r.supplier_id,
        Supplier_Name: r.supplier_name,
        Tier: r.tier,
        Action: r.action,
        Reason: r.reason,
        Timeline: r.timeline,
        Risk: r.propagated_risk.toFixed(1),
        "Contract (M)": r.contract_value.toFixed(2),
      })),
      "recommendations.csv"
    );
  };

  return (
    <div className="space-y-4 w-full">
      <PageHeader
        title="Recommendations"
        description="Prioritised risk mitigation actions with severity levels and timelines."
      />

      {/* Summary KPIs */}
      {summary && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
          <KPICard label="Total Actions" value={summary.total_recommendations} />
          <KPICard
            label="Critical Actions"
            value={summary.critical_count}
            subtitle={`€${summary.critical_contract_value.toFixed(1)}M at risk`}
            accent="#ef4444"
          />
          <KPICard
            label="High"
            value={summary.high_count}
            subtitle={`€${summary.high_contract_value.toFixed(1)}M at risk`}
            accent="#f97316"
          />
          <KPICard label="Medium" value={summary.medium_count} accent="#eab308" />
          <KPICard label="Watch" value={summary.watch_count} accent="#3b82f6" />
        </div>
      )}

      {/* Donut + Executive Summary */}
      {summary && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="bg-shield-surface border border-shield-border rounded-lg p-4">
            <Plot
              data={[
                {
                  type: "pie",
                  labels: Object.keys(severityCounts),
                  values: Object.values(severityCounts),
                  hole: 0.55,
                  marker: {
                    colors: Object.keys(severityCounts).map((k) => SEVERITY_COLORS[k]),
                    line: { color: "#0a0e1a", width: 2 },
                  },
                  textinfo: "label+value",
                  textfont: { color: "#e2e8f0", size: 12 },
                  sort: false,
                },
              ]}
              layout={{
                height: 280,
                margin: { t: 40, b: 10, l: 10, r: 10 },
                paper_bgcolor: "transparent",
                plot_bgcolor: "transparent",
                font: { color: "#e2e8f0" },
                showlegend: false,
                title: { text: "By Severity", font: { size: 14, color: "#94a3b8" } },
              }}
              config={{ displayModeBar: false }}
              style={{ width: "100%" }}
            />
          </div>
          <div className="bg-shield-surface border border-shield-border rounded-lg p-5 flex flex-col justify-center space-y-3">
            <h3 className="font-semibold text-shield-text">Executive Summary</h3>
            <p className="text-sm text-shield-muted">
              {summary.unique_suppliers} unique suppliers across{" "}
              {summary.unique_countries} countries require attention.
            </p>
            <ul className="text-sm space-y-1.5">
              <li className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-risk-critical" />
                <span className="text-shield-text">{summary.critical_count} critical actions</span>
                <span className="text-shield-dim">(0–30 days)</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-risk-high" />
                <span className="text-shield-text">{summary.high_count} high-priority actions</span>
                <span className="text-shield-dim">(30–60 days)</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-risk-medium" />
                <span className="text-shield-text">{summary.medium_count} medium-priority actions</span>
                <span className="text-shield-dim">(60–90 days)</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-risk-watch" />
                <span className="text-shield-text">{summary.watch_count} ongoing monitoring</span>
                <span className="text-shield-dim">(continuous)</span>
              </li>
            </ul>
          </div>
        </div>
      )}

      {/* Filter */}
      <FilterBar
        search={search}
        onSearchChange={handleSearchChange}
        searchPlaceholder="Search recommendations..."
        resultCount={filtered.length}
        onExport={handleExport}
        exportDisabled={filtered.length === 0}
        filters={
          <div className="flex items-center gap-1.5">
            {["", "CRITICAL", "HIGH", "MEDIUM", "WATCH"].map((sev) => (
              <button
                key={sev}
                onClick={() => { setSeverityFilter(sev); setPage(0); }}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                  severityFilter === sev
                    ? "bg-shield-accent text-white"
                    : "bg-shield-surface border border-shield-border text-shield-muted hover:text-shield-text hover:border-shield-accent/40"
                }`}
              >
                {sev || "All"}
              </button>
            ))}
          </div>
        }
      />

      {/* Table */}
      {isLoading ? (
        <TableSkeleton rows={10} cols={7} />
      ) : filtered.length === 0 ? (
        <EmptyState message="No recommendations match your filters." />
      ) : (
        <>
          <div className="bg-shield-surface border border-shield-border rounded-lg overflow-auto max-h-[60vh]">
            <table>
              <thead>
                <tr>
                  <th>Severity</th>
                  <th>Supplier</th>
                  <th>Tier</th>
                  <th>Action</th>
                  <th className="hidden lg:table-cell">Reason</th>
                  <th>Timeline</th>
                  <th>Risk</th>
                  <th>Contract</th>
                </tr>
              </thead>
              <tbody>
                {paged.map((r, i) => (
                  <tr
                    key={`${r.supplier_id}-${r.rule_name}-${i}`}
                    data-critical={r.severity === "CRITICAL" ? "true" : undefined}
                  >
                    <td>
                      <RiskBadge level={r.severity} />
                    </td>
                    <td>
                      <span className="font-mono text-xs">{r.supplier_id}</span>
                      <br />
                      <span className="text-xs text-shield-muted">{r.supplier_name}</span>
                    </td>
                    <td className="text-center">{r.tier}</td>
                    <td className="max-w-xs text-sm">{r.action}</td>
                    <td className="hidden lg:table-cell max-w-xs text-xs text-shield-muted">{r.reason}</td>
                    <td className="text-xs whitespace-nowrap">{r.timeline}</td>
                    <td className="num">{r.propagated_risk.toFixed(1)}</td>
                    <td className="num">€{r.contract_value.toFixed(2)}M</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination page={page} pageSize={PAGE_SIZE} total={filtered.length} onPageChange={setPage} />
        </>
      )}
    </div>
  );
}
