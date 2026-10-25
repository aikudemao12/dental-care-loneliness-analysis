"""Dental-care score construction and weighted regression models."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

COMPONENTS = [
    "disadv_childhood", "disadv_adult_pattern", "disadv_late_uptake", "disadv_postponed",
]
HISTORY_COLUMNS = ["rh015_", "rh016_", "rh017_", "rh018_", "rh788_", "rabyear"]
BLANK_FLAGS = ["rh016_raw_blank", "rh018_raw_blank"]
GROUPS = ["low_0_1", "mid_2", "high_3_4"]
COVARIATES = ["r7agey", "female", "education_level", "bmi", "chronic_burden", "country"]
MODEL_COLUMNS = ["disadvantage_group", "r8lnlys3", "r8wtresp", *COVARIATES]
GROUP_TERM = "C(disadvantage_group, Treatment(reference='low_0_1'))"
FORMULA = f"r8lnlys3 ~ {GROUP_TERM} + r7agey + female + education_level + bmi + chronic_burden + C(country)"
PREPARED_COLUMNS = ["mergeid", *HISTORY_COLUMNS, *BLANK_FLAGS, "r8lnlys3", "r8wtresp", *COVARIATES]


def require_columns(frame: pd.DataFrame, columns: list[str]) -> None:
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise ValueError(f"Missing input columns: {', '.join(missing)}")


def sum_score_components(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["disadvantage_component_nonmissing"] = result[COMPONENTS].notna().sum(axis=1)
    result["disadvantage_score"] = result[COMPONENTS].sum(axis=1, min_count=1).where(
        result["disadvantage_component_nonmissing"].ge(3)
    )
    result["disadvantage_group"] = pd.cut(
        result["disadvantage_score"], [-0.1, 1, 2, 4], labels=GROUPS,
    )
    return result


def derive_dental_score(frame: pd.DataFrame) -> pd.DataFrame:
    """Derive four components, retaining source-empty evidence for structural skips."""
    require_columns(frame, HISTORY_COLUMNS)
    result = frame.copy()
    empty = {}
    for source, flag in [("rh016_", "rh016_raw_blank"), ("rh018_", "rh018_raw_blank")]:
        if flag in result:
            values = result[flag].astype("string").str.strip().str.lower()
            invalid = values.notna() & ~values.isin(["true", "false", "1", "0", "1.0", "0.0"])
            if invalid.any():
                raise ValueError(f"{flag} must contain boolean values or missing values.")
            empty[source] = values.isin(["true", "1", "1.0"])
        else:
            empty[source] = result[source].astype("string").str.strip().eq("").fillna(False)
    result[HISTORY_COLUMNS] = result[HISTORY_COLUMNS].apply(pd.to_numeric, errors="coerce")
    result[HISTORY_COLUMNS] = result[HISTORY_COLUMNS].where(result[HISTORY_COLUMNS].ge(0))
    ever = result["rh015_"].map({1: 1.0, 5: 0.0})
    continuous = result["rh018_"].map({1: 1.0, 5: 0.0})
    result["disadv_childhood"] = 1 - result["rh016_"].map({1: 1.0, 5: 0.0})
    structural_skip = (
        result["rh015_"].eq(5) & result["rh016_"].isna() & result["rh018_"].isna()
        & empty["rh016_"] & empty["rh018_"]
    )
    result.loc[structural_skip, "disadv_childhood"] = 1.0
    adult = pd.Series(np.nan, index=result.index, dtype=float)
    adult.loc[ever.eq(1) & continuous.eq(1)] = 0.0
    adult.loc[ever.eq(0) | continuous.eq(0)] = 1.0
    result["disadv_adult_pattern"] = adult
    start_age = result["rh017_"] - result["rabyear"]
    result["regular_dental_start_age"] = start_age.where(start_age.between(0, 100))
    early = result["rh016_"].eq(1) | result["regular_dental_start_age"].le(25)
    late = pd.Series(np.nan, index=result.index, dtype=float)
    late.loc[early & continuous.eq(1)] = 0.0
    late.loc[result["regular_dental_start_age"].gt(25) | ever.eq(0) | continuous.eq(0)] = 1.0
    result["disadv_late_uptake"] = late
    result["disadv_postponed"] = result["rh788_"].map({1: 1.0, 5: 0.0})
    return sum_score_components(result)


def primary_sample(frame: pd.DataFrame, minimum_age: int = 50) -> pd.DataFrame:
    require_columns(frame, MODEL_COLUMNS)
    result = frame.loc[frame["r7agey"].ge(minimum_age)].dropna(subset=MODEL_COLUMNS).copy()
    result = result.loc[result["r8wtresp"].gt(0)].copy()
    result["disadvantage_group"] = pd.Categorical(
        result["disadvantage_group"], categories=GROUPS, ordered=True,
    )
    result["country"] = result["country"].astype("category").cat.remove_unused_categories()
    return result


def fit_weighted_model(
    frame: pd.DataFrame, *, formula: str, weight: str, required: list[str],
):
    """Fit a complete-case weighted linear model with HC3 inference."""
    require_columns(frame, [*required, weight])
    sample = frame.dropna(subset=[*required, weight]).copy()
    sample = sample.loc[sample[weight].gt(0)].copy()
    if sample.empty:
        raise ValueError("The model has no complete cases with positive weights.")
    for column in sample.select_dtypes(include="category"):
        sample[column] = sample[column].cat.remove_unused_categories()
    fit = smf.wls(formula=formula, data=sample, weights=sample[weight]).fit(cov_type="HC3")
    design = np.asarray(fit.model.wexog, dtype=float)
    if np.linalg.matrix_rank(design) < design.shape[1]:
        raise ValueError("The weighted model design matrix is rank deficient.")
    return fit


def positive_cost_indicator(cost: pd.Series, quantile: float = 0.75) -> tuple[pd.Series, float]:
    """Use positive-cost quantiles; zero and lower positive costs form the reference."""
    values = pd.to_numeric(cost, errors="coerce")
    positive = values.loc[values.gt(0)]
    if positive.empty:
        raise ValueError("A positive-cost threshold requires observed positive costs.")
    threshold = float(positive.quantile(quantile))
    indicator = pd.Series(np.nan, index=values.index, dtype=float)
    valid = values.ge(0)
    indicator.loc[valid] = values.loc[valid].ge(threshold).astype(float)
    return indicator, threshold


def discordance_sensitivity(frame: pd.DataFrame) -> pd.DataFrame:
    """Reset two discordant components to missing and refit the primary model."""
    require_columns(frame, [*COMPONENTS, "rh016_", "regular_dental_start_age"])
    primary = primary_sample(frame)
    discordant = (
        primary["rh016_"].eq(5)
        & primary["regular_dental_start_age"].between(0, 16, inclusive="left")
    )
    changed = primary.copy()
    changed.loc[discordant, ["disadv_childhood", "disadv_late_uptake"]] = np.nan
    changed = primary_sample(sum_score_components(changed))
    rows = []
    for name, sample in [
        ("SHARE primary model", primary),
        ("SHARE discordant childhood-care/start-age sensitivity", changed),
    ]:
        fit = fit_weighted_model(sample, formula=FORMULA, weight="r8wtresp", required=MODEL_COLUMNS)
        ci = fit.conf_int()
        for group, contrast in [
            ("mid_2", "Mid disadvantage vs low"),
            ("high_3_4", "High disadvantage vs low"),
        ]:
            term = f"{GROUP_TERM}[T.{group}]"
            rows.append({
                "sample": name, "outcome": "r8lnlys3", "exposure": "disadvantage_group",
                "term": term, "estimate": float(fit.params[term]),
                "std_error": float(fit.bse[term]), "ci_low": float(ci.loc[term, 0]),
                "ci_high": float(ci.loc[term, 1]), "p_value": float(fit.pvalues[term]),
                "n": int(fit.nobs), "model": "weighted linear model with HC3 robust SE",
                "contrast": contrast, "primary_n": len(primary),
                "discordant_n": int(discordant.sum()),
                "excluded_from_primary_n": len(primary) - len(sample),
            })
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog="Prepared input columns: " + ", ".join(PREPARED_COLUMNS)
        + ". The two raw-blank flags must preserve original empty source cells before missing-value conversion."
        + " Covariates must already use the study definitions.",
    )
    parser.add_argument("--input", type=Path, required=True, help="Prepared SHARE CSV with the fields listed below.")
    parser.add_argument("--output", type=Path, required=True, help="Output CSV containing aggregate primary and sensitivity estimates.")
    args = parser.parse_args()
    frame = pd.read_csv(args.input, dtype={"mergeid": str}, low_memory=False)
    require_columns(frame, PREPARED_COLUMNS)
    if frame["mergeid"].isna().any() or frame["mergeid"].duplicated().any():
        raise ValueError("Prepared participant identifiers must be observed and unique.")
    results = discordance_sensitivity(derive_dental_score(frame))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(args.output, index=False)


if __name__ == "__main__":
    main()
