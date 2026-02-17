"""Network graph and statistics endpoints."""

from collections import defaultdict

from fastapi import APIRouter, Depends

from ..dependencies import get_session_engine, SupplierShieldEngine
from ..schemas import (
    NetworkStatsResponse, NetworkGraphResponse, GraphNode, GraphEdge,
    CountryAggregation, CountryAggregationResponse,
)
from src.risk.config import get_risk_category

router = APIRouter()


@router.get("/stats", response_model=NetworkStatsResponse)
def network_stats(engine: SupplierShieldEngine = Depends(get_session_engine)):
    """Get network graph statistics."""
    g = engine.graph
    n = g.number_of_nodes()
    e = g.number_of_edges()

    tier_counts = {"1": 0, "2": 0, "3": 0}
    for node in g.nodes():
        t = str(g.nodes[node]["tier"])
        tier_counts[t] = tier_counts.get(t, 0) + 1

    return NetworkStatsResponse(
        total_nodes=n,
        total_edges=e,
        density=round(e / (n * (n - 1)), 6) if n > 1 else 0,
        avg_degree=round(e / n, 2) if n else 0,
        tier_counts=tier_counts,
    )


@router.get("/graph", response_model=NetworkGraphResponse)
def network_graph(engine: SupplierShieldEngine = Depends(get_session_engine)):
    """Get full graph data (nodes + edges) for visualisation."""
    g = engine.graph
    pos = engine.get_graph_layout()

    nodes = []
    for node_id in g.nodes():
        nd = g.nodes[node_id]
        x, y = pos[node_id]
        nodes.append(GraphNode(
            id=node_id,
            name=nd["name"],
            tier=nd["tier"],
            risk=round(nd.get("risk_propagated", nd["risk_composite"]), 2),
            category=nd.get("risk_category", "UNKNOWN"),
            contract_value=nd["contract_value_eur_m"],
            is_spof=nd.get("is_spof", False),
            x=round(float(x), 4),
            y=round(float(y), 4),
            country_code=nd.get("country_code", ""),
        ))

    edges = [
        GraphEdge(source=u, target=v, weight=d.get("weight", 1))
        for u, v, d in g.edges(data=True)
    ]

    return NetworkGraphResponse(nodes=nodes, edges=edges)


@router.get("/countries", response_model=CountryAggregationResponse)
def network_countries(engine: SupplierShieldEngine = Depends(get_session_engine)):
    """Aggregate suppliers by country for globe visualisation."""
    g = engine.graph
    buckets: dict[str, dict] = defaultdict(lambda: {
        "risks": [], "contract_values": [], "country_name": "",
    })

    for node_id in g.nodes():
        nd = g.nodes[node_id]
        code = nd.get("country_code", "")
        if not code:
            continue
        b = buckets[code]
        b["country_name"] = nd.get("country", code)
        risk = nd.get("risk_propagated", nd.get("risk_composite", 50))
        b["risks"].append(risk)
        b["contract_values"].append(nd.get("contract_value_eur_m", 0))

    countries = []
    for code, b in sorted(buckets.items()):
        avg = sum(b["risks"]) / len(b["risks"]) if b["risks"] else 0
        countries.append(CountryAggregation(
            country_code=code,
            country_name=b["country_name"],
            supplier_count=len(b["risks"]),
            avg_risk=round(avg, 2),
            risk_category=get_risk_category(avg),
            total_contract_value=round(sum(b["contract_values"]), 2),
        ))

    return CountryAggregationResponse(countries=countries)
