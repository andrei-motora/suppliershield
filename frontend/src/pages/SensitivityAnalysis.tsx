import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import Plot from "react-plotly.js";
import { fetchCriticality, fetchPareto } from "../api/client";
import RiskBadge from "../components/RiskBadge";
import KPICard from "../components/KPICard";
import ErrorState from "../components/ErrorState";
import EmptyState from "../components/EmptyState";
import SupplierModal from "../components/SupplierModal";
import PageHeader from "../components/PageHeader";
import FilterBar from "../components/FilterBar";
import InfoTooltip from "../components/InfoTooltip";
import TableSkeleton from "../components/TableSkeleton";
import Pagination from "../components/Pagination";
import { exportCsv } from "../utils/exportCsv";

const PAGE_SIZE = 25;

export default function SensitivityAnalysis() {
  const [search, setSearch] = useState("");
  const [selectedSupplier, setSelectedSupplier] = useState<string | null>(null);
  const [page, setPage] = useState(0);

  const { data: critData, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["criticality"],
    queryFn: () => fetchCriticality(120),
  });
  const { data: pareto } = useQuery({
    queryKey: ["pareto"],
    queryFn: fetchPareto,
  });

  const items = critData?.items ?? [];

  const filtered = useMemo(() => {
    if (!search) return items;
    const q = search.toLowerCase();
    return items.filter(
      (i) =>
        i.supplier_id.toLowerCase().includes(q) ||
        i.name.toLowerCase().includes(q) ||
        i.country.toLowerCase().includes(q)
    );
  }, [items, search]);

  const paged = useMemo(
    () => filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE),
    [filtered, page]
  );

  if (isError)
    return <ErrorState message={error.message} onRetry={() => refetch()} />;

  const handleSearchChange = (v: string) => { setSearch(v); setPage(0); };

  const handleExport = () => {
    exportCsv(
      filtered.map((i) => ({
        Rank: i.rank,
        ID: i.supplier_id,
        Name: i.name,
        Tier: i.tier,
        Country: i.country,
        Risk: i.propagated_risk.toFixed(1),
        Category: i.risk_category,
        "Exposure (M)": i.total_revenue_exposure.toFixed(2),
        Criticality: i.criticality_score.toFixed(2),
        Products: i.affected_products,
      })),
      "sensitivity-analysis.csv"
    );
  };

  return (
    <div className="space-y-4 w-full">
      <PageHeader
        title="Sensitivity Analysis"
        description="Criticality = (Risk / 100) × Revenue Exposure — which single failure causes the most damage?"
      />

      {/* Pareto KPIs */}
      {pareto && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <KPICard
            label="Total Criticality"
            value={pareto.total_criticality.toFixed(0)}
          />
          <KPICard
            label="80% of Risk"
            value={`${pareto.pareto_80_suppliers} suppliers`}
            subtitle={`${pareto.pareto_80_percent.toFixed(1)}% of network`}
          />
          <KPICard
            label="50% of Risk"
            value={`${pareto.pareto_50_suppliers} suppliers`}
            subtitle={`${pareto.pareto_50_percent.toFixed(1)}% of network`}
          />
          <KPICard
            label="Top 10 Concentration"
            value={`${pareto.top_10_percent.toFixed(1)}%`}
            subtitle="of total criticality"
          />
        </div>
      )}

      {/* Scatter plot: Risk vs Exposure */}
      {isLoading ? (
        <div className="bg-shield-surface border border-shield-border rounded-lg h-[440px] animate-pulse" />
      ) : (
        <div className="bg-shield-surface border border-shield-border rounded-lg p-4">
          <Plot
            data={[
              {
                type: "scatter",
                mode: "markers",
                x: items.map((i) => i.propagated_risk),
                y: items.map((i) => i.total_revenue_exposure),
                text: items.map((i) => `${i.name} (${i.supplier_id})`),
                marker: {
                  size: items.map((i) => Math.max(6, Math.sqrt(i.criticality_score) * 3)),
                  color: items.map((i) => i.criticality_score),
                  colorscale: [
                    [0, "#22c55e"],
                    [0.33, "#eab308"],
                    [0.66, "#f97316"],
                    [1, "#ef4444"],
                  ],
                  colorbar: { title: { text: "Criticality" }, tickfont: { color: "#94a3b8" } },
                  line: { color: "rgba(255,255,255,0.2)", width: 1 },
                },
                hovertemplate: items.map(
                  (i) =>
                    `<b>${i.name}</b> (${i.supplier_id})<br>Risk: ${i.propagated_risk}<br>Exposure: €${i.total_revenue_exposure.toFixed(2)}M<br>Criticality: ${i.criticality_score.toFixed(2)}<extra></extra>`
                ),
              },
            ]}
            layout={{
              height: 400,
              margin: { t: 30, b: 50, l: 70, r: 20 },
              paper_bgcolor: "transparent",
              plot_bgcolor: "transparent",
              font: { color: "#e2e8f0" },
              xaxis: { title: { text: "Propagated Risk Score" }, gridcolor: "rgba(255,255,255,0.05)" },
              yaxis: { title: { text: "Revenue Exposure (€M)" }, gridcolor: "rgba(255,255,255,0.05)" },
              title: { text: "Risk vs Revenue Exposure", font: { size: 14, color: "#94a3b8" } },
            }}
            config={{ displayModeBar: false }}
            style={{ width: "100%" }}
          />
        </div>
      )}

      <FilterBar
        search={search}
        onSearchChange={handleSearchChange}
        searchPlaceholder="Search by ID, name, country..."
        resultCount={filtered.length}
        onExport={handleExport}
        exportDisabled={filtered.length === 0}
      />

      {/* Ranking table */}
      {isLoading ? (
        <TableSkeleton rows={10} cols={8} />
      ) : filtered.length === 0 ? (
        <EmptyState message="No suppliers match your search." />
      ) : (
        <>
          <div className="bg-shield-surface border border-shield-border rounded-lg overflow-auto max-h-[60vh]">
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>ID</th>
                  <th>Name</th>
                  <th>Tier</th>
                  <th>Country</th>
                  <th>
                    <span className="inline-flex items-center gap-1">
                      Risk <InfoTooltip text="Propagated risk score after upstream cascade from deep-tier suppliers." />
                    </span>
                  </th>
                  <th>Category</th>
                  <th>
                    <span className="inline-flex items-center gap-1">
                      Exposure <InfoTooltip text="Total revenue at risk (€M) if this supplier fails, including downstream impact." />
                    </span>
                  </th>
                  <th>
                    <span className="inline-flex items-center gap-1">
                      Criticality <InfoTooltip text="Criticality = (Risk / 100) × Revenue Exposure. Higher = more damaging failure." />
                    </span>
                  </th>
                  <th className="hidden lg:table-cell">Products</th>
                </tr>
              </thead>
              <tbody>
                {paged.map((item) => (
                  <tr key={item.supplier_id} data-critical={item.risk_category === "CRITICAL" ? "true" : undefined}>
                    <td className="num text-shield-muted">{item.rank}</td>
                    <td>
                      <button
                        onClick={() => setSelectedSupplier(item.supplier_id)}
                        className="font-mono text-xs text-shield-accent hover:underline cursor-pointer"
                      >
                        {item.supplier_id}
                      </button>
                    </td>
                    <td>{item.name}</td>
                    <td className="text-center">{item.tier}</td>
                    <td>{item.country}</td>
                    <td className="num">{item.propagated_risk.toFixed(1)}</td>
                    <td>
                      <RiskBadge level={item.risk_category} />
                    </td>
                    <td className="num">€{item.total_revenue_exposure.toFixed(2)}M</td>
                    <td className="num font-semibold">{item.criticality_score.toFixed(2)}</td>
                    <td className="hidden lg:table-cell text-center num">{item.affected_products}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination page={page} pageSize={PAGE_SIZE} total={filtered.length} onPageChange={setPage} />
        </>
      )}

      {selectedSupplier && (
        <SupplierModal
          supplierId={selectedSupplier}
          onClose={() => setSelectedSupplier(null)}
        />
      )}
    </div>
  );
}
