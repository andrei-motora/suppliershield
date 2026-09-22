import { useEffect, useRef, useState, useMemo, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchCountryAggregation } from "../api/client";
import { usePrefersReducedMotion } from "../hooks/useMediaQuery";
import { RISK_COLORS, COUNTRY_COORDINATES } from "../constants";
import type { CountryAggregation, RiskCategory, GraphNode, GraphEdge } from "../types";

import Globe from "react-globe.gl";

interface GeoFeature {
  type: string;
  properties: Record<string, unknown>;
  geometry: unknown;
}

interface GeoJSON {
  type: string;
  features: GeoFeature[];
}

/** Common ISO 3166-1 alpha-3 → alpha-2 mapping.
 *  Used as a frontend fallback in case the backend hasn't normalized yet
 *  (e.g. cached API responses from before the normalization was deployed). */
const ISO3_TO_ISO2: Record<string, string> = {
  AFG:"AF",ALB:"AL",DZA:"DZ",AND:"AD",AGO:"AO",ATG:"AG",ARG:"AR",ARM:"AM",
  AUS:"AU",AUT:"AT",AZE:"AZ",BHS:"BS",BHR:"BH",BGD:"BD",BRB:"BB",BLR:"BY",
  BEL:"BE",BLZ:"BZ",BEN:"BJ",BTN:"BT",BOL:"BO",BIH:"BA",BWA:"BW",BRA:"BR",
  BRN:"BN",BGR:"BG",BFA:"BF",BDI:"BI",CPV:"CV",KHM:"KH",CMR:"CM",CAN:"CA",
  CAF:"CF",TCD:"TD",CHL:"CL",CHN:"CN",COL:"CO",COM:"KM",COG:"CG",COD:"CD",
  CRI:"CR",CIV:"CI",HRV:"HR",CUB:"CU",CYP:"CY",CZE:"CZ",DNK:"DK",DJI:"DJ",
  DMA:"DM",DOM:"DO",ECU:"EC",EGY:"EG",SLV:"SV",GNQ:"GQ",ERI:"ER",EST:"EE",
  SWZ:"SZ",ETH:"ET",FJI:"FJ",FIN:"FI",FRA:"FR",GAB:"GA",GMB:"GM",GEO:"GE",
  DEU:"DE",GHA:"GH",GRC:"GR",GRD:"GD",GTM:"GT",GIN:"GN",GNB:"GW",GUY:"GY",
  HTI:"HT",HND:"HN",HUN:"HU",ISL:"IS",IND:"IN",IDN:"ID",IRN:"IR",IRQ:"IQ",
  IRL:"IE",ISR:"IL",ITA:"IT",JAM:"JM",JPN:"JP",JOR:"JO",KAZ:"KZ",KEN:"KE",
  KIR:"KI",PRK:"KP",KOR:"KR",KWT:"KW",KGZ:"KG",LAO:"LA",LVA:"LV",LBN:"LB",
  LSO:"LS",LBR:"LR",LBY:"LY",LIE:"LI",LTU:"LT",LUX:"LU",MDG:"MG",MWI:"MW",
  MYS:"MY",MDV:"MV",MLI:"ML",MLT:"MT",MHL:"MH",MRT:"MR",MUS:"MU",MEX:"MX",
  FSM:"FM",MDA:"MD",MCO:"MC",MNG:"MN",MNE:"ME",MAR:"MA",MOZ:"MZ",MMR:"MM",
  NAM:"NA",NRU:"NR",NPL:"NP",NLD:"NL",NZL:"NZ",NIC:"NI",NER:"NE",NGA:"NG",
  MKD:"MK",NOR:"NO",OMN:"OM",PAK:"PK",PLW:"PW",PAN:"PA",PNG:"PG",PRY:"PY",
  PER:"PE",PHL:"PH",POL:"PL",PRT:"PT",QAT:"QA",ROU:"RO",RUS:"RU",RWA:"RW",
  KNA:"KN",LCA:"LC",VCT:"VC",WSM:"WS",SMR:"SM",STP:"ST",SAU:"SA",SEN:"SN",
  SRB:"RS",SYC:"SC",SLE:"SL",SGP:"SG",SVK:"SK",SVN:"SI",SLB:"SB",SOM:"SO",
  ZAF:"ZA",SSD:"SS",ESP:"ES",LKA:"LK",SDN:"SD",SUR:"SR",SWE:"SE",CHE:"CH",
  SYR:"SY",TWN:"TW",TJK:"TJ",TZA:"TZ",THA:"TH",TLS:"TL",TGO:"TG",TON:"TO",
  TTO:"TT",TUN:"TN",TUR:"TR",TKM:"TM",TUV:"TV",UGA:"UG",UKR:"UA",ARE:"AE",
  GBR:"GB",USA:"US",URY:"UY",UZB:"UZ",VUT:"VU",VEN:"VE",VNM:"VN",YEM:"YE",
  ZMB:"ZM",ZWE:"ZW",HKG:"HK",MAC:"MO",PSE:"PS",XKX:"XK",
};

/** Normalize a country code to ISO alpha-2 (handles 3-letter codes). */
function toAlpha2(code: string): string {
  if (!code) return code;
  const upper = code.trim().toUpperCase();
  if (upper.length === 2) return upper;
  if (upper.length === 3) return ISO3_TO_ISO2[upper] ?? upper;
  return upper;
}

/** Extract a reliable 2-letter ISO code from a GeoJSON feature.
 *  Prefers ISO_A2_EH which is correct for all countries (including Taiwan, France, Norway)
 *  over ISO_A2 which has "-99" or "CN-TW" for some features. */
function getFeatureCode(f: GeoFeature): string {
  const eh = (f.properties.ISO_A2_EH as string) ?? "";
  if (eh && eh !== "-99") return eh;
  const a2 = (f.properties.ISO_A2 as string) ?? "";
  if (a2 && a2 !== "-99" && a2.length === 2) return a2;
  return "";
}

/** Compute country centroids from GeoJSON features.
 *  For MultiPolygon, coordinates are weighted by ring length to bias toward
 *  the largest landmass (e.g. continental US rather than Alaska). */
function computeCentroids(geo: GeoJSON): Record<string, { lat: number; lng: number }> {
  const result: Record<string, { lat: number; lng: number }> = {};
  for (const feature of geo.features) {
    const code = getFeatureCode(feature);
    if (!code) continue;
    const geom = feature.geometry as { type: string; coordinates: number[][][][] | number[][][] };
    let rings: number[][][] = [];
    if (geom.type === "Polygon") {
      rings = [geom.coordinates[0] as unknown as number[][]];
    } else if (geom.type === "MultiPolygon") {
      rings = (geom.coordinates as number[][][][]).map((poly) => poly[0]);
    }
    if (!rings.length) continue;

    let totalWeight = 0;
    let weightedLat = 0;
    let weightedLng = 0;
    for (const ring of rings) {
      const weight = ring.length; // bias toward larger landmasses
      let sumLat = 0;
      let sumLng = 0;
      for (const [lng, lat] of ring) {
        sumLat += lat;
        sumLng += lng;
      }
      weightedLat += (sumLat / ring.length) * weight;
      weightedLng += (sumLng / ring.length) * weight;
      totalWeight += weight;
    }
    if (totalWeight > 0) {
      result[code] = { lat: weightedLat / totalWeight, lng: weightedLng / totalWeight };
    }
  }
  return result;
}

function hasWebGL(): boolean {
  try {
    const canvas = document.createElement("canvas");
    return !!(
      canvas.getContext("webgl") || canvas.getContext("experimental-webgl")
    );
  } catch {
    return false;
  }
}

function getRiskColor(category: RiskCategory | string): string {
  return RISK_COLORS[category] ?? "rgba(255,255,255,0.05)";
}

/** Spread multiple suppliers in the same country so nodes don't stack */
function jitter(base: number, index: number, total: number, spread = 3): number {
  if (total <= 1) return base;
  const angle = (2 * Math.PI * index) / total;
  const radius = spread * Math.sqrt(index + 1) / Math.sqrt(total);
  return base + radius * Math.cos(angle);
}

function jitterLng(base: number, index: number, total: number, spread = 3): number {
  if (total <= 1) return base;
  const angle = (2 * Math.PI * index) / total;
  const radius = spread * Math.sqrt(index + 1) / Math.sqrt(total);
  return base + radius * Math.sin(angle);
}

interface SupplierPoint {
  id: string;
  name: string;
  lat: number;
  lng: number;
  tier: number;
  risk: number;
  category: string;
  contract_value: number;
  is_spof: boolean;
}

interface DependencyArc {
  startLat: number;
  startLng: number;
  endLat: number;
  endLng: number;
  sourceId: string;
  targetId: string;
}

/* ── Tier badge colors ─────────────────────────────────── */
const TIER_COLORS: Record<number, string> = {
  1: "#f97316", // orange
  2: "#3b82f6", // blue
  3: "#a855f7", // purple
};

/* ── Country Detail Panel ─────────────────────────────── */
interface CountryDetailPanelProps {
  countryCode: string;
  countryName: string;
  nodes: GraphNode[];
  onClose: () => void;
}

function CountryDetailPanel({ countryCode, countryName, nodes, onClose }: CountryDetailPanelProps) {
  const suppliers = nodes.filter((n) => n.country_code === countryCode);
  const avgRisk = suppliers.length
    ? suppliers.reduce((s, n) => s + n.risk, 0) / suppliers.length
    : 0;
  const totalContract = suppliers.reduce((s, n) => s + n.contract_value, 0);
  const riskCat = categorizeRisk(avgRisk);

  return (
    <div
      className="absolute left-0 top-0 bottom-0 z-20 flex flex-col overflow-hidden rounded-l-lg"
      style={{
        width: 320,
        background: "rgba(15,20,35,0.95)",
        backdropFilter: "blur(12px)",
        borderRight: "1px solid rgba(249,115,22,0.15)",
        animation: "slideInLeft 0.25s ease-out",
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-shield-border/30">
        <div>
          <h3 className="text-sm font-semibold text-shield-text">{countryName}</h3>
          <span className="text-[10px] text-shield-dim font-mono">{countryCode}</span>
        </div>
        <button
          onClick={onClose}
          className="w-6 h-6 flex items-center justify-center rounded hover:bg-white/10 text-shield-muted hover:text-shield-text transition-colors"
        >
          ✕
        </button>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-3 gap-2 px-4 py-3 border-b border-shield-border/30">
        <div className="text-center">
          <div className="text-lg font-bold text-shield-text">{suppliers.length}</div>
          <div className="text-[10px] text-shield-dim">Suppliers</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-bold" style={{ color: getRiskColor(riskCat) }}>
            {avgRisk.toFixed(1)}
          </div>
          <div className="text-[10px] text-shield-dim">
            <span
              className="px-1 py-px rounded text-[9px] font-semibold"
              style={{ backgroundColor: getRiskColor(riskCat) + "22", color: getRiskColor(riskCat) }}
            >
              {riskCat}
            </span>
          </div>
        </div>
        <div className="text-center">
          <div className="text-lg font-bold text-shield-text">€{totalContract.toFixed(1)}M</div>
          <div className="text-[10px] text-shield-dim">Contract</div>
        </div>
      </div>

      {/* Supplier list */}
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1.5" style={{ scrollbarWidth: "thin" }}>
        {suppliers.length === 0 ? (
          <div className="text-center text-shield-dim text-sm py-8">
            No suppliers in this country
          </div>
        ) : (
          suppliers
            .sort((a, b) => b.risk - a.risk)
            .map((s) => (
              <div
                key={s.id}
                className="rounded-md px-3 py-2"
                style={{
                  background: "rgba(255,255,255,0.03)",
                  borderLeft: `3px solid ${getRiskColor(s.category)}`,
                }}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-semibold text-shield-text truncate" style={{ maxWidth: 180 }}>
                    {s.name}
                  </span>
                  <span
                    className="text-[10px] font-bold px-1.5 py-0.5 rounded"
                    style={{
                      backgroundColor: (TIER_COLORS[s.tier] ?? "#64748b") + "22",
                      color: TIER_COLORS[s.tier] ?? "#64748b",
                    }}
                  >
                    T{s.tier}
                  </span>
                </div>
                <div className="text-[10px] text-shield-dim font-mono mb-1">{s.id}</div>
                <div className="flex items-center justify-between text-[11px]">
                  <span>
                    Risk:{" "}
                    <span className="font-semibold" style={{ color: getRiskColor(s.category) }}>
                      {s.risk.toFixed(1)}
                    </span>
                  </span>
                  <span className="text-shield-muted">€{s.contract_value.toFixed(2)}M</span>
                </div>
                {s.is_spof && (
                  <div className="mt-1 text-[10px] font-bold text-red-500">⚠ SPOF</div>
                )}
              </div>
            ))
        )}
      </div>
    </div>
  );
}

/** Fallback table when WebGL is not available */
function CountryTable({ countries }: { countries: CountryAggregation[] }) {
  return (
    <div className="overflow-auto max-h-80">
      <table className="w-full text-xs">
        <thead className="text-shield-muted sticky top-0 bg-shield-surface">
          <tr>
            <th className="text-left p-2">Country</th>
            <th className="text-right p-2">Suppliers</th>
            <th className="text-right p-2">Avg Risk</th>
            <th className="text-right p-2">Category</th>
            <th className="text-right p-2">Contract Value</th>
          </tr>
        </thead>
        <tbody>
          {countries.map((c) => (
            <tr key={c.country_code} className="border-t border-shield-border/30">
              <td className="p-2 text-shield-text">{c.country_name}</td>
              <td className="p-2 text-right text-shield-muted">{c.supplier_count}</td>
              <td className="p-2 text-right font-mono" style={{ color: getRiskColor(c.risk_category) }}>
                {c.avg_risk.toFixed(1)}
              </td>
              <td className="p-2 text-right">
                <span
                  className="px-1.5 py-0.5 rounded text-[10px] font-semibold"
                  style={{ backgroundColor: getRiskColor(c.risk_category) + "22", color: getRiskColor(c.risk_category) }}
                >
                  {c.risk_category}
                </span>
              </td>
              <td className="p-2 text-right text-shield-muted">{c.total_contract_value.toFixed(1)}M</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

interface GlobeVisualizationProps {
  nodes?: GraphNode[];
  edges?: GraphEdge[];
  showArcs?: boolean;
  filterBar?: React.ReactNode;
}

function categorizeRisk(avg: number): RiskCategory {
  if (avg >= 75) return "CRITICAL";
  if (avg >= 55) return "HIGH";
  if (avg >= 35) return "MEDIUM";
  return "LOW";
}

export default function GlobeVisualization({
  nodes = [],
  edges = [],
  showArcs = true,
  filterBar,
}: GlobeVisualizationProps) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const globeRef = useRef<any>(null);
  const reducedMotion = usePrefersReducedMotion();
  const [geoData, setGeoData] = useState<GeoJSON | null>(null);
  const [webGLAvailable] = useState(hasWebGL);
  const [selectedCountry, setSelectedCountry] = useState<string | null>(null);

  const { data: countryData } = useQuery({
    queryKey: ["countryAggregation"],
    queryFn: fetchCountryAggregation,
  });

  // Build lookup from the *filtered* nodes so country highlighting reflects active filters
  const countryMap = useMemo(() => {
    const map = new Map<string, CountryAggregation>();
    if (!nodes.length) return map;

    // Aggregate filtered nodes by country (normalize 3-letter codes as fallback)
    const byCountry = new Map<string, GraphNode[]>();
    for (const n of nodes) {
      const code = toAlpha2(n.country_code);
      if (!code) continue;
      if (!byCountry.has(code)) byCountry.set(code, []);
      byCountry.get(code)!.push(n);
    }

    // Look up country names from API data if available
    const nameMap = new Map<string, string>();
    if (countryData) {
      for (const c of countryData.countries) {
        nameMap.set(c.country_code, c.country_name);
      }
    }

    for (const [code, countryNodes] of byCountry) {
      const avgRisk = countryNodes.reduce((s, n) => s + n.risk, 0) / countryNodes.length;
      const totalContract = countryNodes.reduce((s, n) => s + n.contract_value, 0);
      map.set(code, {
        country_code: code,
        country_name: nameMap.get(code) ?? code,
        supplier_count: countryNodes.length,
        avg_risk: avgRisk,
        risk_category: categorizeRisk(avgRisk),
        total_contract_value: totalContract,
      });
    }
    return map;
  }, [nodes, countryData]);

  // Load GeoJSON
  useEffect(() => {
    fetch("/ne_110m_countries.geojson")
      .then((r) => r.json())
      .then((data: GeoJSON) => setGeoData(data))
      .catch(() => {
        // GeoJSON failed to load -- globe won't render but app won't crash
      });
  }, []);

  // Derive centroids from GeoJSON, with COUNTRY_COORDINATES as manual overrides
  const coordMap = useMemo(() => {
    const centroids = geoData ? computeCentroids(geoData) : {};
    // COUNTRY_COORDINATES overrides take priority for manual tweaks
    return { ...centroids, ...COUNTRY_COORDINATES };
  }, [geoData]);

  // Auto-rotate control
  useEffect(() => {
    const globe = globeRef.current as { controls: () => { autoRotate: boolean; autoRotateSpeed: number } } | null;
    if (globe?.controls) {
      const controls = globe.controls();
      controls.autoRotate = !reducedMotion;
      controls.autoRotateSpeed = 0.4;
    }
  }, [reducedMotion, geoData]);

  // Build supplier points with jittered coordinates
  const supplierPoints: SupplierPoint[] = useMemo(() => {
    if (!nodes.length) return [];

    // Group nodes by country to compute jitter (normalize 3-letter codes as fallback)
    const byCountry = new Map<string, GraphNode[]>();
    for (const n of nodes) {
      const code = toAlpha2(n.country_code);
      if (!code || !coordMap[code]) continue;
      if (!byCountry.has(code)) byCountry.set(code, []);
      byCountry.get(code)!.push(n);
    }

    const points: SupplierPoint[] = [];
    for (const [code, countryNodes] of byCountry) {
      const base = coordMap[code];
      countryNodes.forEach((n, i) => {
        points.push({
          id: n.id,
          name: n.name,
          lat: jitter(base.lat, i, countryNodes.length),
          lng: jitterLng(base.lng, i, countryNodes.length),
          tier: n.tier,
          risk: n.risk,
          category: n.category,
          contract_value: n.contract_value,
          is_spof: n.is_spof,
        });
      });
    }
    return points;
  }, [nodes, coordMap]);

  // Build lookup for point positions
  const pointPositions = useMemo(() => {
    const map = new Map<string, { lat: number; lng: number }>();
    for (const p of supplierPoints) {
      map.set(p.id, { lat: p.lat, lng: p.lng });
    }
    return map;
  }, [supplierPoints]);

  // Build arcs from edges (only when showArcs is enabled)
  const arcsData: DependencyArc[] = useMemo(() => {
    if (!showArcs || !edges.length || !pointPositions.size) return [];
    const arcs: DependencyArc[] = [];
    for (const e of edges) {
      const s = pointPositions.get(e.source);
      const t = pointPositions.get(e.target);
      if (s && t) {
        arcs.push({
          startLat: s.lat,
          startLng: s.lng,
          endLat: t.lat,
          endLng: t.lng,
          sourceId: e.source,
          targetId: e.target,
        });
      }
    }
    return arcs;
  }, [showArcs, edges, pointPositions]);

  // Polygon callbacks
  const getPolygonColor = useCallback(
    (feat: object) => {
      const f = feat as GeoFeature;
      const code = getFeatureCode(f);
      const agg = countryMap.get(code);
      if (!agg) return "rgba(255,255,255,0.08)";
      return getRiskColor(agg.risk_category) + "bb";
    },
    [countryMap]
  );

  const getPolygonSideColor = useCallback(
    (feat: object) => {
      const f = feat as GeoFeature;
      const code = getFeatureCode(f);
      const agg = countryMap.get(code);
      if (!agg) return "rgba(255,255,255,0.03)";
      return getRiskColor(agg.risk_category) + "44";
    },
    [countryMap]
  );

  const getPolygonAltitude = useCallback(
    (feat: object) => {
      const f = feat as GeoFeature;
      const code = getFeatureCode(f);
      return countryMap.has(code) ? 0.02 : 0.001;
    },
    [countryMap]
  );

  const getPolygonLabel = useCallback(
    (feat: object) => {
      const f = feat as GeoFeature;
      const code = getFeatureCode(f);
      const name = (f.properties.NAME as string) ?? code;
      const agg = countryMap.get(code);
      if (!agg)
        return `<div style="padding:4px 8px;background:rgba(10,14,26,0.9);border:1px solid rgba(249,115,22,0.2);border-radius:6px;color:#94a3b8;font-size:12px">${name}</div>`;
      return `<div style="padding:8px 12px;background:rgba(10,14,26,0.95);border:1px solid ${getRiskColor(agg.risk_category)}44;border-radius:8px;font-size:12px;min-width:140px">
        <div style="color:#e2e8f0;font-weight:600;margin-bottom:4px">${agg.country_name}</div>
        <div style="color:#94a3b8">Suppliers: <span style="color:#e2e8f0">${agg.supplier_count}</span></div>
        <div style="color:#94a3b8">Avg Risk: <span style="color:${getRiskColor(agg.risk_category)};font-weight:600">${agg.avg_risk.toFixed(1)}</span> <span style="color:${getRiskColor(agg.risk_category)};font-size:10px">${agg.risk_category}</span></div>
        <div style="color:#94a3b8">Contract Value: <span style="color:#e2e8f0">\u20ac${agg.total_contract_value.toFixed(1)}M</span></div>
      </div>`;
    },
    [countryMap]
  );

  // Country click handler
  const handlePolygonClick = useCallback(
    (feat: object) => {
      const f = feat as GeoFeature;
      const code = getFeatureCode(f);
      setSelectedCountry((prev) => (prev === code ? null : code));
    },
    []
  );

  // Derive selected country name for the panel
  const selectedCountryName = useMemo(() => {
    if (!selectedCountry) return "";
    const agg = countryMap.get(selectedCountry);
    if (agg) return agg.country_name;
    // Fallback: look in geoData features
    if (geoData) {
      const feat = geoData.features.find(
        (f) => getFeatureCode(f) === selectedCountry
      );
      if (feat) return (feat.properties.NAME as string) ?? selectedCountry;
    }
    return selectedCountry;
  }, [selectedCountry, countryMap, geoData]);

  // Point callbacks
  const getPointColor = useCallback((point: object) => {
    const p = point as SupplierPoint;
    return getRiskColor(p.category);
  }, []);

  const getPointAltitude = useCallback(() => 0.03, []);

  const getPointRadius = useCallback((point: object) => {
    const p = point as SupplierPoint;
    const base = Math.max(0.15, Math.min(0.6, p.contract_value * 0.08));
    return p.is_spof ? base * 1.3 : base;
  }, []);

  const getPointLabel = useCallback((point: object) => {
    const p = point as SupplierPoint;
    const spofBadge = p.is_spof
      ? `<div style="color:#ef4444;font-weight:700;font-size:11px;margin-top:4px">&#9888; SPOF</div>`
      : "";
    return `<div style="padding:8px 12px;background:rgba(10,14,26,0.95);border:1px solid ${getRiskColor(p.category)}44;border-radius:8px;font-size:12px;min-width:160px">
      <div style="color:#e2e8f0;font-weight:600;margin-bottom:4px">${p.name}</div>
      <div style="color:#94a3b8">ID: <span style="color:#e2e8f0">${p.id}</span></div>
      <div style="color:#94a3b8">Tier: <span style="color:#e2e8f0">${p.tier}</span></div>
      <div style="color:#94a3b8">Risk: <span style="color:${getRiskColor(p.category)};font-weight:600">${p.risk.toFixed(1)}</span> <span style="color:${getRiskColor(p.category)};font-size:10px">${p.category}</span></div>
      <div style="color:#94a3b8">Contract: <span style="color:#e2e8f0">\u20ac${p.contract_value.toFixed(2)}M</span></div>
      ${spofBadge}
    </div>`;
  }, []);

  // Arc callbacks
  const getArcColor = useCallback(() => "rgba(148,163,184,0.25)", []);
  const getArcDashLength = useCallback(() => 0.4, []);
  const getArcDashGap = useCallback(() => 0.2, []);
  const getArcStroke = useCallback(() => 0.3, []);

  const countries = countryData?.countries ?? [];

  // No WebGL -> show fallback table
  if (!webGLAvailable) {
    return (
      <div className="bg-shield-surface border border-shield-border rounded-lg p-4">
        <p className="text-xs text-shield-muted mb-3 uppercase tracking-wider">
          Supply Chain Globe (WebGL not available)
        </p>
        {countries.length > 0 ? (
          <CountryTable countries={countries} />
        ) : (
          <div className="text-shield-dim text-sm text-center py-8">Loading country data...</div>
        )}
      </div>
    );
  }

  return (
    <div className="bg-shield-surface border border-shield-border rounded-lg p-2 overflow-visible">
      <div className="flex items-center justify-between px-4 pt-2 pb-1">
        <h2 className="text-sm font-semibold text-shield-muted">
          Supply Chain Globe
        </h2>
        <span className="text-[10px] text-shield-dim">
          {countries.length} countries &middot; {supplierPoints.length} suppliers &middot; {arcsData.length} dependencies &middot; Drag to rotate &middot; Scroll to zoom
        </span>
      </div>
      {filterBar}
      <div className="relative flex justify-center" style={{ height: 600 }}>
        {/* Country detail panel */}
        {selectedCountry && (
          <CountryDetailPanel
            countryCode={selectedCountry}
            countryName={selectedCountryName}
            nodes={nodes}
            onClose={() => setSelectedCountry(null)}
          />
        )}
        {geoData ? (
          <Globe
            ref={globeRef}
            width={860}
            height={580}
            backgroundColor="rgba(0,0,0,0)"
            globeImageUrl="//unpkg.com/three-globe/example/img/earth-night.jpg"
            showGlobe={true}
            showAtmosphere={true}
            atmosphereColor="#f97316"
            atmosphereAltitude={0.15}
            // Country polygons
            polygonsData={geoData.features}
            polygonCapColor={getPolygonColor}
            polygonSideColor={getPolygonSideColor}
            polygonAltitude={getPolygonAltitude}
            polygonStrokeColor={() => "rgba(255,255,255,0.08)"}
            polygonLabel={getPolygonLabel}
            onPolygonClick={handlePolygonClick}
            // Supplier nodes
            pointsData={supplierPoints}
            pointLat="lat"
            pointLng="lng"
            pointColor={getPointColor}
            pointAltitude={getPointAltitude}
            pointRadius={getPointRadius}
            pointLabel={getPointLabel}
            // Dependency arcs
            arcsData={arcsData}
            arcStartLat="startLat"
            arcStartLng="startLng"
            arcEndLat="endLat"
            arcEndLng="endLng"
            arcColor={getArcColor}
            arcDashLength={getArcDashLength}
            arcDashGap={getArcDashGap}
            arcStroke={getArcStroke}
            arcDashAnimateTime={2000}
          />
        ) : (
          <div className="flex items-center justify-center text-shield-dim text-sm">
            Loading globe...
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-4 pb-2">
        {(["LOW", "MEDIUM", "HIGH", "CRITICAL"] as const).map((cat) => (
          <div key={cat} className="flex items-center gap-1.5">
            <div
              className="w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: RISK_COLORS[cat] }}
            />
            <span className="text-[10px] text-shield-dim">{cat}</span>
          </div>
        ))}
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-white/5 border border-white/10" />
          <span className="text-[10px] text-shield-dim">No suppliers</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full border-2 border-red-500 bg-transparent" />
          <span className="text-[10px] text-shield-dim">SPOF</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-4 h-px bg-slate-400/40" />
          <span className="text-[10px] text-shield-dim">Dependency</span>
        </div>
      </div>
    </div>
  );
}
