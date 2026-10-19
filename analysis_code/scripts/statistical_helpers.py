from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scripts.model_diagnostics import diagnose_fit


def require_columns(frame: pd.DataFrame, columns: list[str]) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"Input file is missing required columns: {', '.join(missing)}")


def positive_weight_complete_case(frame: pd.DataFrame, columns: list[str], weight_col: str) -> pd.DataFrame:
    require_columns(frame, [*columns, weight_col])
    model_frame = frame.dropna(subset=[*columns, weight_col]).copy()
    return model_frame.loc[model_frame[weight_col] > 0].copy()


def positive_cost_quantile(cost: pd.Series, quantile: float = 0.75) -> float:
    """Return a quantile among strictly positive, non-missing costs.

    Zero-cost observations are retained in the resulting exposure as the
    reference category; they are excluded only when the threshold is formed.
    Negative values are treated as invalid and therefore excluded.
    """
    values = pd.to_numeric(cost, errors="coerce")
    positive = values.gt(0)
    if not positive.any():
        raise ValueError("Cannot define a positive-cost quantile: no strictly positive costs were observed.")
    return float(values.loc[positive].quantile(quantile))


def positive_cost_burden(cost: pd.Series, quantile: float = 0.75) -> tuple[pd.Series, float]:
    """Code high dental out-of-pocket expenditure at a positive-cost quantile while preserving zeros."""
    values = pd.to_numeric(cost, errors="coerce")
    threshold = positive_cost_quantile(values, quantile)
    burden = pd.Series(np.nan, index=values.index, dtype=float)
    valid = values.ge(0)
    burden.loc[valid] = values.loc[valid].ge(threshold).astype(float)
    return burden, threshold


def weighted_linear_model(
    frame: pd.DataFrame,
    *,
    formula: str,
    weight_col: str,
    outcome: str,
    exposure: str,
    sample: str,
) -> pd.DataFrame:
    fit = smf.wls(formula=formula, data=frame, weights=frame[weight_col]).fit(cov_type="HC3")
    diagnose_fit(fit, frame, weight_col)
    ci = fit.conf_int()
    rows = []
    for term in fit.params.index:
        rows.append(
            {
                "sample": sample,
                "outcome": outcome,
                "exposure": exposure,
                "term": term,
                "estimate": float(fit.params[term]) if term not in fit.nonestimable_terms else np.nan,
                "std_error": float(fit.bse[term]) if term not in fit.nonestimable_terms else np.nan,
                "ci_low": float(ci.loc[term, 0]) if term not in fit.nonestimable_terms else np.nan,
                "ci_high": float(ci.loc[term, 1]) if term not in fit.nonestimable_terms else np.nan,
                "p_value": float(fit.pvalues[term]) if term not in fit.nonestimable_terms else np.nan,
                "n": int(fit.nobs),
                "model": "weighted linear model with HC3 robust SE",
            }
        )
    return pd.DataFrame(rows)


def write_results(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
