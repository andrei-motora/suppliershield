import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { X, FlaskConical, ClipboardCheck } from "lucide-react";
import { fetchSupplier } from "../api/client";
import RiskBadge from "./RiskBadge";
import Button from "./Button";

interface SupplierModalProps {
  supplierId: string;
  onClose: () => void;
}

export default function SupplierModal({ supplierId, onClose }: SupplierModalProps) {
  const navigate = useNavigate();
  const { data, isLoading, isError } = useQuery({
    queryKey: ["supplier", supplierId],
    queryFn: () => fetchSupplier(supplierId),
  });

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  const goToSimulation = () => {
    onClose();
    navigate(`/what-if?supplier=${supplierId}`);
  };

  const goToRecommendations = () => {
    onClose();
    navigate("/recommendations");
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4" role="dialog" aria-modal="true" aria-label={`Supplier detail: ${supplierId}`}>
      <div className="fixed inset-0 bg-black/60" onClick={onClose} />
      <div className="relative bg-shield-surface border border-shield-border rounded-lg max-w-2xl w-full max-h-[85vh] overflow-y-auto shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-shield-border sticky top-0 bg-shield-surface z-10">
          <h2 className="text-lg font-bold text-shield-text">Supplier Detail: {supplierId}</h2>
          <button
            onClick={onClose}
            className="text-shield-muted hover:text-shield-text p-1 transition-colors"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-5">
          {isLoading && (
            <div className="animate-pulse space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                {Array.from({ length: 8 }).map((_, i) => (
                  <div key={i}>
                    <div className="h-2.5 w-16 bg-white/5 rounded mb-2" />
                    <div className="h-4 w-24 bg-white/10 rounded" />
                  </div>
                ))}
              </div>
            </div>
          )}

          {isError && (
            <div className="text-risk-critical text-center py-8">
              Failed to load supplier details.
            </div>
          )}

          {data && (
            <>
              {/* Quick actions */}
              <div className="flex gap-2">
                <Button variant="secondary" onClick={goToSimulation} className="text-xs">
                  <span className="inline-flex items-center gap-1.5">
                    <FlaskConical className="w-3.5 h-3.5" />
                    Run Simulation
                  </span>
                </Button>
                <Button variant="secondary" onClick={goToRecommendations} className="text-xs">
                  <span className="inline-flex items-center gap-1.5">
                    <ClipboardCheck className="w-3.5 h-3.5" />
                    View Recommendations
                  </span>
                </Button>
              </div>

              {/* Basic info */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-xs text-shield-muted uppercase tracking-wider">Name</span>
                  <p className="font-semibold mt-0.5">{data.name}</p>
                </div>
                <div>
                  <span className="text-xs text-shield-muted uppercase tracking-wider">Tier</span>
                  <p className="font-semibold mt-0.5">{data.tier}</p>
                </div>
                <div>
                  <span className="text-xs text-shield-muted uppercase tracking-wider">Component</span>
                  <p className="font-semibold mt-0.5">{data.component}</p>
                </div>
                <div>
                  <span className="text-xs text-shield-muted uppercase tracking-wider">Country</span>
                  <p className="font-semibold mt-0.5">{data.country} ({data.country_code})</p>
                </div>
                <div>
                  <span className="text-xs text-shield-muted uppercase tracking-wider">Contract Value</span>
                  <p className="font-mono font-semibold mt-0.5">€{data.contract_value_eur_m.toFixed(2)}M</p>
                </div>
                <div>
                  <span className="text-xs text-shield-muted uppercase tracking-wider">Lead Time</span>
                  <p className="font-semibold mt-0.5">{data.lead_time_days} days</p>
                </div>
                <div>
                  <span className="text-xs text-shield-muted uppercase tracking-wider">Financial Health</span>
                  <p className="font-semibold mt-0.5">{data.financial_health}/100</p>
                </div>
                <div>
                  <span className="text-xs text-shield-muted uppercase tracking-wider">Past Disruptions</span>
                  <p className="font-semibold mt-0.5">{data.past_disruptions}</p>
                </div>
              </div>

              {/* Risk breakdown */}
              <div className="border-t border-shield-border pt-4">
                <h3 className="font-semibold mb-3 text-sm text-shield-text">Risk Breakdown</h3>
                <div className="flex items-center gap-3 mb-3">
                  <RiskBadge level={data.risk.category} />
                  {data.is_spof && (
                    <span className="text-risk-critical text-xs font-bold border border-risk-critical/30 px-2 py-0.5 rounded">
                      SPOF
                    </span>
                  )}
                </div>
                <div className="grid grid-cols-2 gap-x-4 gap-y-0.5 text-sm">
                  {([
                    ["Geopolitical", data.risk.geopolitical],
                    ["Natural Disaster", data.risk.natural_disaster],
                    ["Financial", data.risk.financial],
                    ["Logistics", data.risk.logistics],
                    ["Concentration", data.risk.concentration],
                    ["Composite", data.risk.composite],
                    ["Propagated", data.risk.propagated],
                  ] as [string, number][]).map(([label, val]) => (
                    <div key={label} className="flex justify-between py-1.5 border-b border-shield-border/50">
                      <span className="text-shield-muted">{label}</span>
                      <span className="font-mono tabular-nums">{val.toFixed(1)}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Dependencies */}
              <div className="border-t border-shield-border pt-4">
                <h3 className="font-semibold mb-3 text-sm text-shield-text">Supply Chain Dependencies</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-shield-muted mb-2 text-xs uppercase tracking-wider">Upstream ({data.upstream.length})</p>
                    {data.upstream.length === 0 ? (
                      <p className="text-shield-dim text-xs">No upstream suppliers</p>
                    ) : (
                      <div className="flex flex-wrap gap-1">
                        {data.upstream.map((id) => (
                          <span key={id} className="inline-block font-mono text-xs bg-shield-bg px-2 py-1 rounded">
                            {id}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  <div>
                    <p className="text-shield-muted mb-2 text-xs uppercase tracking-wider">Downstream ({data.downstream.length})</p>
                    {data.downstream.length === 0 ? (
                      <p className="text-shield-dim text-xs">No downstream suppliers</p>
                    ) : (
                      <div className="flex flex-wrap gap-1">
                        {data.downstream.map((id) => (
                          <span key={id} className="inline-block font-mono text-xs bg-shield-bg px-2 py-1 rounded">
                            {id}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
