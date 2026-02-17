import { RotateCcw } from "lucide-react";

interface CountryOption {
  code: string;
  name: string;
}

interface GlobeFilterBarProps {
  activeTiers: Set<number>;
  onToggleTier: (tier: number) => void;
  spofOnly: boolean;
  onToggleSpof: () => void;
  selectedCountry: string;
  onSelectCountry: (code: string) => void;
  countryOptions: CountryOption[];
  riskRange: [number, number];
  onRiskRangeChange: (range: [number, number]) => void;
  contractRange: [number, number];
  onContractRangeChange: (range: [number, number]) => void;
  contractBounds: { min: number; max: number };
  showArcs: boolean;
  onToggleArcs: () => void;
  visibleCount: number;
  totalCount: number;
  onReset: () => void;
}

const TIER_COLORS = ["#3b82f6", "#8b5cf6", "#ec4899"];

export default function GlobeFilterBar({
  activeTiers,
  onToggleTier,
  spofOnly,
  onToggleSpof,
  selectedCountry,
  onSelectCountry,
  countryOptions,
  riskRange,
  onRiskRangeChange,
  contractRange,
  onContractRangeChange,
  contractBounds,
  showArcs,
  onToggleArcs,
  visibleCount,
  totalCount,
  onReset,
}: GlobeFilterBarProps) {
  const isDefault =
    activeTiers.size === 3 &&
    !spofOnly &&
    selectedCountry === "" &&
    riskRange[0] === 0 &&
    riskRange[1] === 100 &&
    contractRange[0] === contractBounds.min &&
    contractRange[1] === contractBounds.max &&
    showArcs;

  return (
    <div className="flex flex-wrap items-center gap-3 px-4 py-2 text-xs">
      {/* Tier checkboxes */}
      <div className="flex items-center gap-1.5">
        <span className="text-shield-dim mr-0.5">Tier</span>
        {[1, 2, 3].map((t) => (
          <label
            key={t}
            className="flex items-center gap-1 cursor-pointer select-none"
          >
            <input
              type="checkbox"
              checked={activeTiers.has(t)}
              onChange={() => onToggleTier(t)}
              className="sr-only"
            />
            <span
              className={`px-1.5 py-0.5 rounded text-[10px] font-semibold transition-colors ${
                activeTiers.has(t)
                  ? "text-white"
                  : "text-shield-dim opacity-40"
              }`}
              style={{
                backgroundColor: activeTiers.has(t)
                  ? TIER_COLORS[t - 1] + "88"
                  : "transparent",
                border: `1px solid ${TIER_COLORS[t - 1]}${activeTiers.has(t) ? "88" : "33"}`,
              }}
            >
              T{t}
            </span>
          </label>
        ))}
      </div>

      {/* Divider */}
      <div className="w-px h-4 bg-shield-border" />

      {/* SPOF Only toggle */}
      <button
        onClick={onToggleSpof}
        className={`px-2 py-0.5 rounded text-[10px] font-semibold transition-colors ${
          spofOnly
            ? "bg-red-500/20 text-red-400 border border-red-500/40"
            : "text-shield-dim border border-shield-border hover:text-shield-muted hover:border-shield-border"
        }`}
      >
        SPOF Only
      </button>

      {/* Divider */}
      <div className="w-px h-4 bg-shield-border" />

      {/* Country dropdown */}
      <select
        value={selectedCountry}
        onChange={(e) => onSelectCountry(e.target.value)}
        className="bg-shield-bg border border-shield-border rounded px-1.5 py-0.5 text-[11px] text-shield-muted focus:outline-none focus:border-shield-accent/40 max-w-[130px]"
      >
        <option value="">All Countries</option>
        {countryOptions.map((c) => (
          <option key={c.code} value={c.code}>
            {c.name}
          </option>
        ))}
      </select>

      {/* Divider */}
      <div className="w-px h-4 bg-shield-border" />

      {/* Risk range */}
      <div className="flex items-center gap-1.5">
        <span className="text-shield-dim">Risk</span>
        <input
          type="range"
          min={0}
          max={100}
          value={riskRange[0]}
          onChange={(e) =>
            onRiskRangeChange([
              Math.min(Number(e.target.value), riskRange[1]),
              riskRange[1],
            ])
          }
          className="globe-slider w-14"
        />
        <input
          type="range"
          min={0}
          max={100}
          value={riskRange[1]}
          onChange={(e) =>
            onRiskRangeChange([
              riskRange[0],
              Math.max(Number(e.target.value), riskRange[0]),
            ])
          }
          className="globe-slider w-14"
        />
        <span className="text-shield-dim font-mono text-[10px] w-[52px] text-center">
          {riskRange[0]}-{riskRange[1]}
        </span>
      </div>

      {/* Divider */}
      <div className="w-px h-4 bg-shield-border" />

      {/* Contract value range */}
      <div className="flex items-center gap-1.5">
        <span className="text-shield-dim">Contract</span>
        <input
          type="range"
          min={contractBounds.min}
          max={contractBounds.max}
          step={0.1}
          value={contractRange[0]}
          onChange={(e) =>
            onContractRangeChange([
              Math.min(Number(e.target.value), contractRange[1]),
              contractRange[1],
            ])
          }
          className="globe-slider w-14"
        />
        <input
          type="range"
          min={contractBounds.min}
          max={contractBounds.max}
          step={0.1}
          value={contractRange[1]}
          onChange={(e) =>
            onContractRangeChange([
              contractRange[0],
              Math.max(Number(e.target.value), contractRange[0]),
            ])
          }
          className="globe-slider w-14"
        />
        <span className="text-shield-dim font-mono text-[10px] w-[72px] text-center">
          {contractRange[0].toFixed(1)}-{contractRange[1].toFixed(1)}M
        </span>
      </div>

      {/* Divider */}
      <div className="w-px h-4 bg-shield-border" />

      {/* Show Arcs toggle */}
      <button
        onClick={onToggleArcs}
        className={`px-2 py-0.5 rounded text-[10px] font-semibold transition-colors ${
          showArcs
            ? "bg-slate-400/15 text-slate-300 border border-slate-400/30"
            : "text-shield-dim border border-shield-border hover:text-shield-muted"
        }`}
      >
        Arcs
      </button>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Result count */}
      <span className="text-shield-dim font-mono text-[10px]">
        {visibleCount} / {totalCount} suppliers
      </span>

      {/* Reset button */}
      {!isDefault && (
        <button
          onClick={onReset}
          className="flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] text-shield-muted border border-shield-border hover:text-shield-accent hover:border-shield-accent/40 transition-colors"
        >
          <RotateCcw className="w-2.5 h-2.5" />
          Reset
        </button>
      )}
    </div>
  );
}
