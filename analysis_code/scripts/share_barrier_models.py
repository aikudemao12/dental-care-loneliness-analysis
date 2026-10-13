from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.paths import PATHS
from scripts.statistical_helpers import positive_weight_complete_case, weighted_linear_model, write_results


BARRIER_DEFINITIONS = {
    "financial_barrier": ["rh026d1", "rh026d2", "rh026d3"],
    "structural_info_barrier": ["rh026d4", "rh026d5", "rh026d7"],
    "attitudinal_barrier": ["rh026d6", "rh026d8"],
}


def as_binary_indicator(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        values = pd.to_numeric(series, errors="coerce")
        out = pd.Series(float("nan"), index=series.index, dtype=float)
        out.loc[values.eq(0)] = 0.0
        out.loc[values.eq(1)] = 1.0
        return out
    cleaned = series.astype(str).str.strip().str.lower()
    out = pd.Series(float("nan"), index=series.index, dtype=float)
    out.loc[cleaned.isin({"0", "no", "false", "n"})] = 0.0
    out.loc[cleaned.isin({"1", "yes", "true", "y"})] = 1.0
    return out


def ensure_barrier_indicators(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    for barrier, item_columns in BARRIER_DEFINITIONS.items():
        if barrier in frame.columns:
            frame[barrier] = as_binary_indicator(frame[barrier])
            continue
        missing = [column for column in item_columns if column not in frame.columns]
        if missing:
            raise ValueError(
                f"Cannot derive {barrier}; missing raw item columns: {', '.join(missing)}"
            )
        item_frame = pd.concat([as_binary_indicator(frame[column]) for column in item_columns], axis=1)
        frame[barrier] = item_frame.max(axis=1)
        frame.loc[item_frame.notna().sum(axis=1).eq(0), barrier] = float("nan")
    return frame


def dental_disadvantage_mask(frame: pd.DataFrame) -> pd.Series:
    if "disadvantage_score" not in frame.columns:
        raise ValueError("SHARE barrier models require the derived disadvantage_score column.")
    return pd.to_numeric(frame["disadvantage_score"], errors="coerce").ge(2)


def main() -> None:
    frame = pd.read_csv(PATHS.share_analytic, low_memory=False)
    frame = ensure_barrier_indicators(frame)
    frame["country"] = frame["country"].astype("category")

    rows = []
    covariates = ["r7agey", "female", "education_level", "bmi", "chronic_burden", "country"]
    base_columns = ["r8lnlys3", "r8wtresp", *covariates]
    restricted = frame.loc[
        frame["analysis_eligible_loneliness"].eq(1) & dental_disadvantage_mask(frame)
    ].copy()

    # Use one common complete-case set across the three barrier domains. This
    # prevents the reported N from changing by barrier and preserves missing
    # barrier responses rather than treating them as no barrier.
    complete_columns = [*base_columns, *BARRIER_DEFINITIONS]
    analysis = positive_weight_complete_case(restricted, complete_columns, "r8wtresp")
    for barrier in BARRIER_DEFINITIONS:
        rows.append(
            weighted_linear_model(
                analysis,
                formula=f"r8lnlys3 ~ {barrier} + r7agey + female + education_level + bmi + chronic_burden + C(country)",
                weight_col="r8wtresp",
                outcome="r8lnlys3",
                exposure=barrier,
                sample="SHARE dental-barrier model",
            )
        )

    result = pd.concat(rows, ignore_index=True)
    keep = result["term"].isin(BARRIER_DEFINITIONS)
    write_results(result.loc[keep].copy(), PATHS.tables_root / "share_barrier_models.csv")


if __name__ == "__main__":
    main()
