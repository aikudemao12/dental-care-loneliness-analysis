from __future__ import annotations

from pathlib import Path

import pandas as pd
import statsmodels.formula.api as smf


def require_columns(frame: pd.DataFrame, columns: list[str]) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"Input file is missing required columns: {', '.join(missing)}")


def positive_weight_complete_case(frame: pd.DataFrame, columns: list[str], weight_col: str) -> pd.DataFrame:
    require_columns(frame, [*columns, weight_col])
    model_frame = frame.dropna(subset=[*columns, weight_col]).copy()
    return model_frame.loc[model_frame[weight_col] > 0].copy()


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
    ci = fit.conf_int()
    rows = []
    for term in fit.params.index:
        rows.append(
            {
                "sample": sample,
                "outcome": outcome,
                "exposure": exposure,
                "term": term,
                "estimate": float(fit.params[term]),
                "std_error": float(fit.bse[term]),
                "ci_low": float(ci.loc[term, 0]),
                "ci_high": float(ci.loc[term, 1]),
                "p_value": float(fit.pvalues[term]),
                "n": int(fit.nobs),
                "model": "weighted linear model with HC3 robust SE",
            }
        )
    return pd.DataFrame(rows)


def write_results(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
