"""
File upload validation and storage for SupplierShield.

Handles CSV validation, sanitization, and cross-file consistency checks.
"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)

# Expected columns per file type
EXPECTED_COLUMNS: Dict[str, List[str]] = {
    "suppliers": [
        "id", "name", "tier", "component", "country", "country_code",
        "region", "contract_value_eur_m", "lead_time_days",
        "financial_health", "past_disruptions", "has_backup",
    ],
    "dependencies": ["source_id", "target_id", "dependency_weight"],
    "country_risk": [
        "country", "country_code", "political_stability",
        "natural_disaster_freq", "trade_restriction_risk",
        "logistics_performance",
    ],
    "product_bom": [
        "product_id", "product_name", "annual_revenue_eur_m",
        "component_supplier_ids",
    ],
}

VALID_FILE_TYPES = set(EXPECTED_COLUMNS.keys())

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


@dataclass
class ValidationError:
    file: str
    check: str
    message: str


@dataclass
class FileValidationResult:
    valid: bool
    file_type: str
    row_count: int = 0
    columns: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class FileHandler:
    """Handles upload validation and storage for CSV files."""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir

    def get_session_dir(self, session_id: str) -> Path:
        """Return the temp directory for a session."""
        session_dir = (self.base_dir / session_id).resolve()
        if not str(session_dir).startswith(str(self.base_dir.resolve())):
            raise ValueError("Invalid session path")
        return session_dir

    def validate_and_save(
        self, session_dir: Path, file_type: str, content: bytes
    ) -> FileValidationResult:
        """Validate a CSV file and save it to the session directory."""
        errors: List[str] = []

        # 1. Check file type
        if file_type not in VALID_FILE_TYPES:
            return FileValidationResult(
                valid=False, file_type=file_type,
                errors=[f"Invalid file type: {file_type}. Expected one of: {', '.join(VALID_FILE_TYPES)}"],
            )

        # 2. Check size
        if len(content) > MAX_FILE_SIZE:
            return FileValidationResult(
                valid=False, file_type=file_type,
                errors=[f"File too large ({len(content) / 1024 / 1024:.1f} MB). Maximum is 50 MB."],
            )

        # 3. Try to parse as CSV
        try:
            import io
            df = pd.read_csv(io.BytesIO(content))
        except Exception as e:
            return FileValidationResult(
                valid=False, file_type=file_type,
                errors=[f"Could not parse as CSV: {e}"],
            )

        if df.empty:
            return FileValidationResult(
                valid=False, file_type=file_type,
                errors=["CSV file is empty (no data rows)"],
            )

        # 4. Check required columns
        expected = set(EXPECTED_COLUMNS[file_type])
        actual = set(df.columns)
        missing = expected - actual
        if missing:
            errors.append(f"Missing required columns: {', '.join(sorted(missing))}")

        extra = actual - expected
        if extra:
            # Extra columns are a warning, not an error — we'll just ignore them
            logger.info("Extra columns in %s: %s (will be ignored)", file_type, extra)

        # 5. Sanitize cell content (CSV formula injection prevention)
        df = self._sanitize_dataframe(df)

        # 6. Basic data type validation
        type_errors = self._validate_data_types(df, file_type)
        errors.extend(type_errors)

        if errors:
            return FileValidationResult(
                valid=False, file_type=file_type,
                row_count=len(df), columns=list(df.columns),
                errors=errors,
            )

        # 7. Save the sanitized file
        session_dir.mkdir(parents=True, exist_ok=True)
        out_path = session_dir / f"{file_type}.csv"
        df.to_csv(out_path, index=False)
        logger.info("Saved %s.csv (%d rows) to %s", file_type, len(df), session_dir)

        return FileValidationResult(
            valid=True, file_type=file_type,
            row_count=len(df), columns=list(df.columns),
        )

    def get_upload_status(self, session_dir: Path) -> Dict:
        """Check which files have been uploaded. Only 3 are required — country_risk is optional."""
        status = {}
        for ft in VALID_FILE_TYPES:
            status[f"has_{ft}"] = (session_dir / f"{ft}.csv").exists()
        # Only suppliers, dependencies, and product_bom are required
        status["ready_to_finalize"] = (
            status["has_suppliers"]
            and status["has_dependencies"]
            and status["has_product_bom"]
        )
        # Include baseline country count for frontend display
        try:
            from src.data.baseline import load_baseline
            status["baseline_country_count"] = len(load_baseline())
        except Exception:
            status["baseline_country_count"] = 0
        return status

    def run_cross_validation(self, session_dir: Path) -> List[ValidationError]:
        """Load files and run cross-file consistency checks.

        Country risk is optional — if not uploaded, the built-in baseline is used.
        """
        errors: List[ValidationError] = []

        # Load required files + optional country_risk (merged with baseline)
        try:
            suppliers = pd.read_csv(session_dir / "suppliers.csv")
            dependencies = pd.read_csv(session_dir / "dependencies.csv")
            product_bom = pd.read_csv(session_dir / "product_bom.csv")

            # Country risk: merge user upload (if any) with baseline
            from src.data.baseline import load_baseline, merge_country_risk
            baseline = load_baseline()
            user_country_risk = None
            if (session_dir / "country_risk.csv").exists():
                user_country_risk = pd.read_csv(session_dir / "country_risk.csv")
            country_risk = merge_country_risk(baseline, user_country_risk)
        except Exception as e:
            errors.append(ValidationError(
                file="general", check="load", message=f"Failed to load files: {e}"
            ))
            return errors

        supplier_ids = set(str(sid) for sid in suppliers["id"])

        # Check 1: No missing values (only check user-uploaded files for nulls)
        files_to_check = [("suppliers", suppliers), ("dependencies", dependencies),
                          ("product_bom", product_bom)]
        if user_country_risk is not None:
            files_to_check.append(("country_risk", user_country_risk))
        for name, df in files_to_check:
            null_count = df.isnull().sum().sum()
            if null_count > 0:
                null_cols = df.columns[df.isnull().any()].tolist()
                errors.append(ValidationError(
                    file=name, check="nulls",
                    message=f"{null_count} missing values in columns: {', '.join(null_cols)}",
                ))

        # Check 2: Tier values
        if "tier" in suppliers.columns:
            invalid_tiers = set(suppliers["tier"].unique()) - {1, 2, 3}
            if invalid_tiers:
                errors.append(ValidationError(
                    file="suppliers", check="tier_values",
                    message=f"Invalid tier values: {invalid_tiers}. Must be 1, 2, or 3.",
                ))

        # Check 3: Dependency edges reference valid suppliers
        if "source_id" in dependencies.columns and "target_id" in dependencies.columns:
            invalid_sources = set(str(s) for s in dependencies["source_id"]) - supplier_ids
            invalid_targets = set(str(s) for s in dependencies["target_id"]) - supplier_ids
            if invalid_sources:
                errors.append(ValidationError(
                    file="dependencies", check="source_ids",
                    message=f"Source IDs not found in suppliers: {', '.join(sorted(str(s) for s in invalid_sources)[:5])}",
                ))
            if invalid_targets:
                errors.append(ValidationError(
                    file="dependencies", check="target_ids",
                    message=f"Target IDs not found in suppliers: {', '.join(sorted(str(s) for s in invalid_targets)[:5])}",
                ))

        # Check 4: Country consistency
        if "country_code" in suppliers.columns and "country_code" in country_risk.columns:
            risk_countries = set(country_risk["country_code"])
            supplier_countries = set(suppliers["country_code"])
            missing = supplier_countries - risk_countries
            if missing:
                errors.append(ValidationError(
                    file="country_risk", check="country_coverage",
                    message=f"Missing country risk data for: {', '.join(sorted(missing))}",
                ))

        # Check 5: Product BOM supplier IDs
        if "component_supplier_ids" in product_bom.columns:
            for _, row in product_bom.iterrows():
                bom_ids = str(row["component_supplier_ids"]).split(",")
                invalid = [sid for sid in bom_ids if sid.strip() not in supplier_ids]
                if invalid:
                    errors.append(ValidationError(
                        file="product_bom", check="supplier_refs",
                        message=f"Product {row.get('product_id', '?')} references invalid suppliers: {', '.join(invalid[:5])}",
                    ))
                    break  # Don't flood with errors

        return errors

    @staticmethod
    def _sanitize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Strip CSV formula injection prefixes from string cells."""
        formula_pattern = re.compile(r'^[=+\-@]')
        for col in df.select_dtypes(include=["object"]).columns:
            df[col] = df[col].apply(
                lambda x: re.sub(formula_pattern, "", str(x)) if pd.notna(x) and formula_pattern.match(str(x)) else x
            )
        return df

    @staticmethod
    def _validate_data_types(df: pd.DataFrame, file_type: str) -> List[str]:
        """Validate basic data types for known columns."""
        errors = []

        if file_type == "suppliers":
            if "tier" in df.columns:
                try:
                    tiers = pd.to_numeric(df["tier"], errors="coerce")
                    if tiers.isna().any():
                        errors.append("Column 'tier' contains non-numeric values")
                except Exception:
                    errors.append("Column 'tier' must be numeric")

            for col in ["contract_value_eur_m", "financial_health", "lead_time_days", "past_disruptions"]:
                if col in df.columns:
                    vals = pd.to_numeric(df[col], errors="coerce")
                    if vals.isna().any():
                        errors.append(f"Column '{col}' contains non-numeric values")

        elif file_type == "dependencies":
            if "dependency_weight" in df.columns:
                vals = pd.to_numeric(df["dependency_weight"], errors="coerce")
                if vals.isna().any():
                    errors.append("Column 'dependency_weight' contains non-numeric values")

        elif file_type == "country_risk":
            for col in ["political_stability", "natural_disaster_freq", "logistics_performance", "trade_restriction_risk"]:
                if col in df.columns:
                    vals = pd.to_numeric(df[col], errors="coerce")
                    if vals.isna().any():
                        errors.append(f"Column '{col}' contains non-numeric values")

        elif file_type == "product_bom":
            if "annual_revenue_eur_m" in df.columns:
                vals = pd.to_numeric(df["annual_revenue_eur_m"], errors="coerce")
                if vals.isna().any():
                    errors.append("Column 'annual_revenue_eur_m' contains non-numeric values")

        return errors
