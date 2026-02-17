import { useState, useMemo, useRef, useEffect } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import Plot from "react-plotly.js";
import { Search, X, ChevronDown } from "lucide-react";
import { fetchSuppliers, runSimulation } from "../api/client";
import KPICard from "../components/KPICard";
import ErrorState from "../components/ErrorState";
import PageHeader from "../components/PageHeader";
import Button from "../components/Button";
import InfoTooltip from "../components/InfoTooltip";
import type { SimulationResult } from "../types";

export default function WhatIfSimulator() {
  const { data: suppliers, isError, error, refetch } = useQuery({
    queryKey: ["suppliers"],
    queryFn: () => fetchSuppliers(),
  });

  const [target, setTarget] = useState("");
  const [duration, setDuration] = useState(30);
  const [iterations, setIterations] = useState(5000);
  const [scenarioType, setScenarioType] = useState<"single_node" | "regional" | "correlated">("single_node");

  // Comparison mode: store previous results
  const [results, setResults] = useState<(SimulationResult & { label: string })[]>([]);
  const [activeTab, setActiveTab] = useState(0);

  const mutation = useMutation({
    mutationFn: runSimulation,
    onSuccess: (data) => {
      const supplierName = suppliers?.find((s) => s.supplier_id === target)?.name ?? target;
      const label = `${supplierName} (${scenarioType}, ${duration}d)`;
      setResults((prev) => [...prev, { ...data, label }]);
      setActiveTab(results.length); // switch to new tab
    },
  });

  const handleRun = () => {
    if (!target) return;
    mutation.mutate({
      target_supplier: target,
      duration_days: duration,
      iterations,
      scenario_type: scenarioType,
    });
  };

  const removeResult = (idx: number) => {
    setResults((prev) => prev.filter((_, i) => i !== idx));
    setActiveTab((prev) => Math.min(prev, results.length - 2));
  };

  const currentResult = results[activeTab] ?? null;

  if (isError)
    return <ErrorState message={error.message} onRetry={() => refetch()} />;

  return (
    <div className="space-y-4 w-full">
      <PageHeader
        title="What-If Simulator"
        description="Run Monte Carlo disruption simulations to estimate revenue impact. Compare multiple scenarios side-by-side."
      />

      {/* Configuration */}
      <div className="bg-shield-surface border border-shield-border rounded-lg p-5 space-y-4">
        <h2 className="font-semibold text-sm text-shield-text">Scenario Configuration</h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-shield-muted mb-1.5 uppercase tracking-wider">
              <span className="inline-flex items-center gap-1">
                Target Supplier <InfoTooltip text="The supplier to simulate a disruption for. All downstream impact will be calculated." />
              </span>
            </label>
            <SupplierCombobox
              suppliers={suppliers ?? []}
              value={target}
              onChange={setTarget}
            />
          </div>
          <div>
            <label className="block text-xs text-shield-muted mb-1.5 uppercase tracking-wider">
              <span className="inline-flex items-center gap-1">
                Scenario Type <InfoTooltip text="Single: one supplier fails. Regional: all suppliers in the same region. Correlated: financially linked suppliers." />
              </span>
            </label>
            <select
              value={scenarioType}
              onChange={(e) => setScenarioType(e.target.value as typeof scenarioType)}
              className="w-full bg-shield-bg border border-shield-border rounded-md px-3 py-2 text-sm text-shield-text focus:outline-none focus:border-shield-accent/40 transition-colors"
            >
              <option value="single_node">Single Supplier</option>
              <option value="regional">Regional Disruption</option>
              <option value="correlated">Correlated Failure</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-shield-muted mb-1.5 uppercase tracking-wider">
              Duration: <span className="text-shield-text font-medium">{duration} days</span>
            </label>
            <input
              type="range"
              min={7}
              max={90}
              value={duration}
              onChange={(e) => setDuration(Number(e.target.value))}
              className="w-full accent-shield-accent"
            />
            <div className="flex justify-between text-[10px] text-shield-dim mt-1">
              <span>7 days</span>
              <span>90 days</span>
            </div>
          </div>
          <div>
            <label className="block text-xs text-shield-muted mb-1.5 uppercase tracking-wider">
              Iterations: <span className="text-shield-text font-medium">{iterations.toLocaleString()}</span>
            </label>
            <input
              type="range"
              min={1000}
              max={10000}
              step={1000}
              value={iterations}
              onChange={(e) => setIterations(Number(e.target.value))}
              className="w-full accent-shield-accent"
            />
            <div className="flex justify-between text-[10px] text-shield-dim mt-1">
              <span>1,000</span>
              <span>10,000</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="primary"
            onClick={handleRun}
            disabled={!target || mutation.isPending}
          >
            {mutation.isPending ? "Running simulation..." : "Run Simulation"}
          </Button>
          {results.length > 0 && (
            <span className="text-xs text-shield-dim">
              {results.length} simulation{results.length !== 1 ? "s" : ""} completed
            </span>
          )}
        </div>

        {mutation.isError && (
          <p className="text-risk-critical text-sm">
            Simulation failed: {mutation.error.message}
          </p>
        )}
      </div>

      {/* Results tabs */}
      {results.length > 0 && (
        <div className="space-y-4">
          {/* Tab bar */}
          {results.length > 1 && (
            <div className="flex gap-1 overflow-x-auto pb-1">
              {results.map((r, i) => (
                <button
                  key={i}
                  onClick={() => setActiveTab(i)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium whitespace-nowrap transition-colors ${
                    activeTab === i
                      ? "bg-shield-accent/15 text-shield-accent border border-shield-accent/30"
                      : "bg-shield-surface border border-shield-border text-shield-muted hover:text-shield-text"
                  }`}
                >
                  {r.label}
                  <span
                    onClick={(e) => { e.stopPropagation(); removeResult(i); }}
                    className="ml-1 hover:text-risk-critical transition-colors"
                  >
                    <X className="w-3 h-3" />
                  </span>
                </button>
              ))}
            </div>
          )}

          {currentResult && (
            <>
              <h2 className="text-sm font-semibold text-shield-text">
                Results: {currentResult.label}
              </h2>

              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
                <KPICard label="Mean Impact" value={`€${currentResult.mean.toFixed(2)}M`} />
                <KPICard label="Median (P50)" value={`€${currentResult.median.toFixed(2)}M`} />
                <KPICard label="P95" value={`€${currentResult.p95.toFixed(2)}M`} accent="#ef4444" />
                <KPICard label="Worst Case" value={`€${currentResult.max.toFixed(2)}M`} accent="#ef4444" />
                <KPICard
                  label="Affected"
                  value={currentResult.affected_suppliers_count}
                  subtitle={`${currentResult.affected_products.length} products`}
                />
              </div>

              {/* Histogram */}
              <div className="bg-shield-surface border border-shield-border rounded-lg p-4">
                <Plot
                  data={[
                    {
                      type: "bar",
                      x: currentResult.histogram.bin_centers,
                      y: currentResult.histogram.counts,
                      marker: { color: "#f97316", opacity: 0.8 },
                      hovertemplate:
                        "Revenue Impact: €%{x:.2f}M<br>Frequency: %{y}<extra></extra>",
                    },
                  ]}
                  layout={{
                    height: 320,
                    margin: { t: 30, b: 50, l: 60, r: 20 },
                    paper_bgcolor: "transparent",
                    plot_bgcolor: "transparent",
                    font: { color: "#e2e8f0" },
                    xaxis: { title: { text: "Revenue Impact (€M)" }, gridcolor: "rgba(255,255,255,0.05)" },
                    yaxis: { title: { text: "Frequency" }, gridcolor: "rgba(255,255,255,0.05)" },
                    title: { text: "Impact Distribution", font: { size: 14, color: "#94a3b8" } },
                    shapes: [
                      {
                        type: "line",
                        x0: currentResult.mean,
                        x1: currentResult.mean,
                        y0: 0, y1: 1, yref: "paper",
                        line: { color: "#f97316", width: 2, dash: "dot" },
                      },
                      {
                        type: "line",
                        x0: currentResult.p95,
                        x1: currentResult.p95,
                        y0: 0, y1: 1, yref: "paper",
                        line: { color: "#ef4444", width: 2, dash: "dash" },
                      },
                    ],
                    annotations: [
                      {
                        x: currentResult.mean,
                        y: 1, yref: "paper",
                        text: `Mean: €${currentResult.mean.toFixed(2)}M`,
                        showarrow: false,
                        font: { color: "#f97316", size: 11 },
                        yanchor: "bottom",
                      },
                      {
                        x: currentResult.p95,
                        y: 0.92, yref: "paper",
                        text: `P95: €${currentResult.p95.toFixed(2)}M`,
                        showarrow: false,
                        font: { color: "#ef4444", size: 11 },
                        yanchor: "bottom",
                      },
                    ],
                  }}
                  config={{ displayModeBar: false }}
                  style={{ width: "100%" }}
                />
              </div>

              {/* Stats table */}
              <div className="bg-shield-surface border border-shield-border rounded-lg overflow-hidden">
                <table>
                  <thead>
                    <tr>
                      <th>Metric</th>
                      <th>Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      ["Mean Impact", `€${currentResult.mean.toFixed(2)}M`],
                      ["Std Deviation", `€${currentResult.std.toFixed(2)}M`],
                      ["Min (Best Case)", `€${currentResult.min.toFixed(2)}M`],
                      ["P25", `€${currentResult.p25.toFixed(2)}M`],
                      ["Median (P50)", `€${currentResult.median.toFixed(2)}M`],
                      ["P75", `€${currentResult.p75.toFixed(2)}M`],
                      ["P90", `€${currentResult.p90.toFixed(2)}M`],
                      ["P95", `€${currentResult.p95.toFixed(2)}M`],
                      ["P99", `€${currentResult.p99.toFixed(2)}M`],
                      ["Max (Worst Case)", `€${currentResult.max.toFixed(2)}M`],
                      ["Runtime", `${currentResult.runtime.toFixed(2)}s`],
                    ].map(([label, val]) => (
                      <tr key={label}>
                        <td className="text-shield-muted">{label}</td>
                        <td className="num">{val}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

/* ── Searchable Supplier Combobox ── */

interface SupplierComboboxProps {
  suppliers: { supplier_id: string; name: string; risk: { propagated: number; category: string } }[];
  value: string;
  onChange: (id: string) => void;
}

function SupplierCombobox({ suppliers, value, onChange }: SupplierComboboxProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const selectedSupplier = suppliers.find((s) => s.supplier_id === value);

  const filtered = useMemo(() => {
    if (!query) return suppliers.slice(0, 30);
    const q = query.toLowerCase();
    return suppliers
      .filter((s) =>
        s.supplier_id.toLowerCase().includes(q) ||
        s.name.toLowerCase().includes(q)
      )
      .slice(0, 30);
  }, [suppliers, query]);

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
        setQuery("");
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  return (
    <div ref={containerRef} className="relative">
      <div
        className="w-full bg-shield-bg border border-shield-border rounded-md px-3 py-2 text-sm text-shield-text flex items-center gap-2 cursor-pointer hover:border-shield-accent/40 transition-colors"
        onClick={() => { setOpen(true); setTimeout(() => inputRef.current?.focus(), 0); }}
      >
        {open ? (
          <div className="flex items-center gap-2 flex-1">
            <Search className="w-3.5 h-3.5 text-shield-dim shrink-0" />
            <input
              ref={inputRef}
              type="text"
              placeholder="Type to search suppliers..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="bg-transparent outline-none flex-1 text-shield-text placeholder:text-shield-dim"
              onKeyDown={(e) => {
                if (e.key === "Escape") { setOpen(false); setQuery(""); }
                if (e.key === "Enter" && filtered.length > 0) {
                  onChange(filtered[0].supplier_id);
                  setOpen(false);
                  setQuery("");
                }
              }}
            />
          </div>
        ) : (
          <span className={selectedSupplier ? "text-shield-text" : "text-shield-dim"}>
            {selectedSupplier
              ? `${selectedSupplier.supplier_id} - ${selectedSupplier.name}`
              : "Select a supplier..."
            }
          </span>
        )}
        <ChevronDown className="w-3.5 h-3.5 text-shield-dim shrink-0" />
      </div>

      {open && (
        <div className="absolute z-50 mt-1 w-full bg-shield-surface border border-shield-border rounded-md shadow-xl max-h-64 overflow-y-auto">
          {filtered.length === 0 ? (
            <div className="px-3 py-4 text-sm text-shield-dim text-center">No suppliers found</div>
          ) : (
            filtered.map((s) => (
              <button
                key={s.supplier_id}
                onClick={() => {
                  onChange(s.supplier_id);
                  setOpen(false);
                  setQuery("");
                }}
                className={`w-full text-left px-3 py-2 text-sm hover:bg-white/[0.04] transition-colors flex items-center justify-between ${
                  s.supplier_id === value ? "bg-shield-accent/10 text-shield-accent" : "text-shield-text"
                }`}
              >
                <span>
                  <span className="font-mono text-xs mr-2">{s.supplier_id}</span>
                  {s.name}
                </span>
                <span className="text-xs text-shield-dim tabular-nums">
                  Risk: {s.risk.propagated.toFixed(1)}
                </span>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}
