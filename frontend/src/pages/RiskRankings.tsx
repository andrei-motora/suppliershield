import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { ChevronUp, ChevronDown } from "lucide-react";
import { fetchSuppliers } from "../api/client";
import RiskBadge from "../components/RiskBadge";
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

export default function RiskRankings() {
  const [tierFilter, setTierFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [search, setSearch] = useState("");
  const [selectedSupplier, setSelectedSupplier] = useState<string | null>(null);
  const [page, setPage] = useState(0);

  const params: Record<string, string> = {};
  if (tierFilter) params.tier = tierFilter;
  if (categoryFilter) params.risk_category = categoryFilter;

  const { data: suppliers, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["suppliers", params],
    queryFn: () => fetchSuppliers(params),
  });

  const [sortKey, setSortKey] = useState<"composite" | "propagated" | "contract">("propagated");
  const [sortAsc, setSortAsc] = useState(false);

  const sorted = useMemo(() => {
    if (!suppliers) return [];
    let list = [...suppliers];

    if (search) {
      const q = search.toLowerCase();
      list = list.filter(
        (s) =>
          s.supplier_id.toLowerCase().includes(q) ||
          s.name.toLowerCase().includes(q) ||
          s.country.toLowerCase().includes(q) ||
          s.component.toLowerCase().includes(q)
      );
    }

    list.sort((a, b) => {
      let av: number, bv: number;
      switch (sortKey) {
        case "composite":
          av = a.risk.composite; bv = b.risk.composite; break;
        case "propagated":
          av = a.risk.propagated; bv = b.risk.propagated; break;
        case "contract":
          av = a.contract_value_eur_m; bv = b.contract_value_eur_m; break;
        default:
          av = a.risk.propagated; bv = b.risk.propagated;
      }
      return sortAsc ? av - bv : bv - av;
    });

    return list;
  }, [suppliers, search, sortKey, sortAsc]);

  // Reset page when filters change
  const paged = useMemo(() => {
    const start = page * PAGE_SIZE;
    return sorted.slice(start, start + PAGE_SIZE);
  }, [sorted, page]);

  // Reset page on filter/search change
  const handleSearchChange = (v: string) => { setSearch(v); setPage(0); };

  const toggleSort = (key: "composite" | "propagated" | "contract") => {
    if (sortKey === key) setSortAsc(!sortAsc);
    else { setSortKey(key); setSortAsc(false); }
    setPage(0);
  };

  const SortIcon = ({ col }: { col: string }) => {
    if (sortKey !== col) return <span className="w-4" />;
    return sortAsc ? <ChevronUp className="w-3.5 h-3.5 text-shield-accent" /> : <ChevronDown className="w-3.5 h-3.5 text-shield-accent" />;
  };

  const handleExport = () => {
    exportCsv(
      sorted.map((s) => ({
        ID: s.supplier_id,
        Name: s.name,
        Tier: s.tier,
        Component: s.component,
        Country: s.country,
        Composite: s.risk.composite.toFixed(1),
        Propagated: s.risk.propagated.toFixed(1),
        Category: s.risk.category,
        "Contract (M)": s.contract_value_eur_m.toFixed(2),
        SPOF: s.is_spof ? "YES" : "NO",
      })),
      "risk-rankings.csv"
    );
  };

  if (isError)
    return <ErrorState message={error.message} onRetry={() => refetch()} />;

  return (
    <div className="space-y-4 w-full">
      <PageHeader
        title="Risk Rankings"
        description="All suppliers ranked by propagated risk score. Click any supplier ID for details."
      />

      <FilterBar
        search={search}
        onSearchChange={handleSearchChange}
        searchPlaceholder="Search by ID, name, country..."
        resultCount={sorted.length}
        onExport={handleExport}
        exportDisabled={sorted.length === 0}
        filters={
          <>
            <select
              value={tierFilter}
              onChange={(e) => { setTierFilter(e.target.value); setPage(0); }}
              className="bg-shield-surface border border-shield-border rounded-md px-3 py-2 text-sm text-shield-text focus:outline-none focus:border-shield-accent/40 transition-colors"
            >
              <option value="">All Tiers</option>
              <option value="1">Tier 1</option>
              <option value="2">Tier 2</option>
              <option value="3">Tier 3</option>
            </select>
            <select
              value={categoryFilter}
              onChange={(e) => { setCategoryFilter(e.target.value); setPage(0); }}
              className="bg-shield-surface border border-shield-border rounded-md px-3 py-2 text-sm text-shield-text focus:outline-none focus:border-shield-accent/40 transition-colors"
            >
              <option value="">All Categories</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </>
        }
      />

      {/* Table */}
      {isLoading ? (
        <TableSkeleton rows={10} cols={8} />
      ) : sorted.length === 0 ? (
        <EmptyState message="No suppliers match your filters." />
      ) : (
        <>
          <div className="bg-shield-surface border border-shield-border rounded-lg overflow-auto max-h-[70vh]">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                  <th>Tier</th>
                  <th className="hidden lg:table-cell">Component</th>
                  <th>Country</th>
                  <th data-sortable onClick={() => toggleSort("composite")}>
                    <span className="inline-flex items-center gap-1">
                      Composite <InfoTooltip text="Weighted risk score across 5 dimensions: geopolitical, natural disaster, financial, logistics, and concentration." />
                      <SortIcon col="composite" />
                    </span>
                  </th>
                  <th data-sortable onClick={() => toggleSort("propagated")}>
                    <span className="inline-flex items-center gap-1">
                      Propagated <InfoTooltip text="Risk score after upstream cascade. Reveals hidden vulnerabilities from deep-tier suppliers." />
                      <SortIcon col="propagated" />
                    </span>
                  </th>
                  <th>Category</th>
                  <th data-sortable onClick={() => toggleSort("contract")}>
                    <span className="inline-flex items-center gap-1">
                      Contract <SortIcon col="contract" />
                    </span>
                  </th>
                  <th>
                    <span className="inline-flex items-center gap-1">
                      SPOF <InfoTooltip text="Single Point of Failure -- no backup supplier, high risk, or sole source for a critical path." />
                    </span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {paged.map((s) => (
                  <tr key={s.supplier_id} data-critical={s.risk.category === "CRITICAL" ? "true" : undefined}>
                    <td>
                      <button
                        onClick={() => setSelectedSupplier(s.supplier_id)}
                        className="font-mono text-xs text-shield-accent hover:underline cursor-pointer"
                      >
                        {s.supplier_id}
                      </button>
                    </td>
                    <td>{s.name}</td>
                    <td className="text-center">{s.tier}</td>
                    <td className="hidden lg:table-cell">{s.component}</td>
                    <td>{s.country}</td>
                    <td className="num">{s.risk.composite.toFixed(1)}</td>
                    <td className="num">{s.risk.propagated.toFixed(1)}</td>
                    <td>
                      <RiskBadge level={s.risk.category} />
                    </td>
                    <td className="num">€{s.contract_value_eur_m.toFixed(2)}M</td>
                    <td className="text-center">
                      {s.is_spof ? (
                        <span className="text-risk-critical font-bold text-xs">YES</span>
                      ) : (
                        <span className="text-shield-dim">-</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination page={page} pageSize={PAGE_SIZE} total={sorted.length} onPageChange={setPage} />
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
