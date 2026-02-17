"""
Dependency injection for SupplierShield API.

Provides per-session engine instances via SessionManager.
"""

import logging
from pathlib import Path

from fastapi import HTTPException, Request

from src.data.loader import DataValidator
from src.network.builder import SupplierNetworkBuilder
from src.risk.scorer import RiskScorer
from src.risk.propagation import RiskPropagator
from src.risk.spof_detector import SPOFDetector
from src.simulation.monte_carlo import MonteCarloSimulator
from src.simulation.sensitivity import SensitivityAnalyzer
from src.impact.bom_tracer import BOMImpactTracer
from src.recommendations.engine import RecommendationEngine

logger = logging.getLogger(__name__)


class SupplierShieldEngine:
    """Holds the entire analytics pipeline in memory for a single session."""

    def __init__(self):
        self.graph = None
        self.builder = None
        self.scorer = None
        self.propagator = None
        self.spof_detector = None
        self.simulator = None
        self.sensitivity = None
        self.bom_tracer = None
        self.recommender = None
        self.risk_scores = None
        self.propagated_risks = None
        self.spofs: set[str] = set()
        self.suppliers_df = None
        self.product_bom_df = None
        self._initialized = False

        # Cached computed results (populated on first access)
        self._cached_recommendations = None
        self._cached_rec_summary = None
        self._cached_criticality = None
        self._cached_pareto = None
        self._cached_risk_overview = None
        self._cached_graph_layout = None

    def initialize(self, data_dir: str):
        """Run the full analytics pipeline from data in the given directory."""
        if self._initialized:
            return

        try:
            logger.info("Initializing SupplierShield engine from %s...", data_dir)

            # 1. Load data
            validator = DataValidator(data_dir)
            suppliers, dependencies, country_risk, product_bom = validator.load_all()
            self.suppliers_df = suppliers
            self.product_bom_df = product_bom

            # 2. Build network graph
            self.builder = SupplierNetworkBuilder()
            self.builder.load_data(suppliers, dependencies, country_risk)
            self.graph = self.builder.build_graph()

            # 3. Score risks
            self.scorer = RiskScorer(self.graph)
            self.risk_scores = self.scorer.calculate_all_risks()
            self.scorer.add_scores_to_graph()

            # 4. Propagate risks
            self.propagator = RiskPropagator(self.graph)
            self.propagated_risks = self.propagator.propagate_all_risks()

            # 5. Detect SPOFs
            self.spof_detector = SPOFDetector(self.graph)
            self.spofs = set(self.spof_detector.detect_all_spofs())

            # 6. Initialise simulators & recommenders
            self.simulator = MonteCarloSimulator(self.graph, product_bom)
            self.sensitivity = SensitivityAnalyzer(self.graph, product_bom)
            self.bom_tracer = BOMImpactTracer(self.graph, product_bom)
            self.recommender = RecommendationEngine(self.graph, product_bom)

            # 7. Pre-compute expensive results
            self._warm_caches()

            self._initialized = True
            logger.info("SupplierShield engine ready.")

        except Exception:
            logger.exception("Failed to initialize SupplierShield engine")
            raise

    def _warm_caches(self):
        """Pre-compute results that don't change between requests."""
        logger.info("Pre-computing cached results...")
        self._cached_recommendations = self.recommender.generate_all_recommendations()
        self._cached_rec_summary = self.recommender.generate_executive_summary(
            self._cached_recommendations
        )
        self._cached_criticality = self.sensitivity.get_top_critical(120)
        self._cached_pareto = self.sensitivity.get_pareto_analysis()
        self._cached_graph_layout = self._compute_tier_layout()

        # Risk overview
        categories = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        total_risk = 0.0
        for node in self.graph.nodes():
            nd = self.graph.nodes[node]
            cat = nd.get("risk_category", "UNKNOWN")
            if cat in categories:
                categories[cat] += 1
            total_risk += nd.get("risk_propagated", nd.get("risk_composite", 0))
        n = self.graph.number_of_nodes()
        self._cached_risk_overview = {
            "avg_risk": round(total_risk / n, 2) if n else 0,
            "categories": categories,
            "total_suppliers": n,
        }
        logger.info("All caches warmed")

    def _compute_tier_layout(self):
        """Compute a tier-based horizontal layout: Tier 1 right, Tier 2 center, Tier 3 left.
        Within each tier, nodes are spread vertically with slight random jitter."""
        import random
        rng = random.Random(42)

        # Group nodes by tier
        tiers: dict[int, list[str]] = {}
        for node_id in self.graph.nodes():
            tier = self.graph.nodes[node_id].get("tier", 1)
            tiers.setdefault(tier, []).append(node_id)

        # Sort tiers (1, 2, 3)
        tier_keys = sorted(tiers.keys())

        # X positions: Tier 3 (raw materials) on the left, Tier 1 (direct) on the right
        tier_x = {}
        n_tiers = len(tier_keys)
        for i, t in enumerate(reversed(tier_keys)):
            tier_x[t] = (i / max(n_tiers - 1, 1)) * 2 - 1  # maps to -1..1

        pos = {}
        for tier, nodes in tiers.items():
            n = len(nodes)
            x_base = tier_x.get(tier, 0)
            for j, node_id in enumerate(nodes):
                y = (j / max(n - 1, 1)) * 2 - 1 if n > 1 else 0
                # Add jitter to avoid perfect grid
                x = x_base + rng.uniform(-0.08, 0.08)
                y = y + rng.uniform(-0.02, 0.02)
                pos[node_id] = (round(x, 4), round(y, 4))

        return pos

    def get_recommendations(self):
        """Return cached recommendations list."""
        return self._cached_recommendations

    def get_rec_summary(self):
        """Return cached recommendation summary."""
        return self._cached_rec_summary

    def get_criticality(self, top_n: int):
        """Return top N criticality items from cached full list."""
        return self._cached_criticality.head(top_n)

    def get_pareto(self):
        """Return cached pareto analysis."""
        return self._cached_pareto

    def get_risk_overview(self):
        """Return cached risk overview."""
        return self._cached_risk_overview

    def get_graph_layout(self):
        """Return cached spring layout positions."""
        return self._cached_graph_layout


def create_engine_from_dir(data_dir: str) -> SupplierShieldEngine:
    """Factory: create and initialize a SupplierShieldEngine from a data directory."""
    engine = SupplierShieldEngine()
    engine.initialize(data_dir)
    return engine


def get_session_id(request: Request) -> str:
    """FastAPI dependency — extract session ID from request state."""
    session_id = getattr(request.state, "session_id", None)
    if not session_id:
        raise HTTPException(status_code=401, detail="No active session")
    return session_id


def get_session_engine(request: Request) -> SupplierShieldEngine:
    """FastAPI dependency — get the engine for the current session."""
    session_id = get_session_id(request)
    session_manager = request.app.state.session_manager
    engine = session_manager.get_engine(session_id)
    if engine is None:
        raise HTTPException(
            status_code=404,
            detail="No data uploaded. Please upload your CSV files or load the sample dataset.",
        )
    return engine
