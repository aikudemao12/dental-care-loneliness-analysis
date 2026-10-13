"""Reproduce reported age thresholds and aggregate descriptive revision checks."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from config.paths import PATHS
from scripts.statistical_helpers import positive_weight_complete_case, weighted_linear_model, write_results

GROUP_TERM = "C(disadvantage_group, Treatment(reference='low_0_1'))"
COVARIATES = ["r7agey", "female", "education_level", "bmi", "chronic_burden", "country"]


def main() -> None:
    frame = pd.read_csv(PATHS.share_analytic, low_memory=False)
    frame["disadvantage_group"] = pd.Categorical(frame["disadvantage_group"], categories=["low_0_1", "mid_2", "high_3_4"], ordered=True)
    columns = ["disadvantage_group", "r8lnlys3", "r8wtresp", *COVARIATES]
    analysis = positive_weight_complete_case(frame.loc[frame["analysis_eligible_loneliness"].eq(1)], columns, "r8wtresp")
    rows = []
    for threshold in [65, 75]:
        sub = analysis.loc[analysis["r7agey"].ge(threshold)].copy()
        result = weighted_linear_model(sub, formula=f"r8lnlys3 ~ {GROUP_TERM} + r7agey + female + education_level + bmi + chronic_burden + C(country)", weight_col="r8wtresp", outcome="r8lnlys3", exposure="disadvantage_group", sample=f"SHARE age >={threshold} years")
        rows.append(result.loc[result["term"].str.contains("disadvantage_group", regex=False)])
    write_results(pd.concat(rows, ignore_index=True), PATHS.tables_root / "share_age_threshold_sensitivity.csv")
    education_rows = []
    for education, stratum in analysis.groupby("education_level"):
        for group, sub in stratum.groupby("disadvantage_group", observed=True):
            education_rows.append({"education_code": int(education), "disadvantage_group": str(group), "unweighted_n": len(sub), "weighted_share_within_education_pct": 100 * sub["r8wtresp"].sum() / stratum["r8wtresp"].sum(), "weighted_loneliness_mean": np.average(sub["r8lnlys3"], weights=sub["r8wtresp"])})
    write_results(pd.DataFrame(education_rows), PATHS.tables_root / "share_education_by_disadvantage.csv")
    if "rh789_" not in analysis.columns:
        raise ValueError("RH789 descriptive audit requires rh789_; prepare inputs with build_analysis_inputs.py.")
    low = analysis.loc[analysis["disadvantage_group"].eq("low_0_1") & analysis["disadv_postponed"].eq(1)]
    count = pd.to_numeric(low["rh789_"], errors="coerce").where(lambda values: values.ge(0)).dropna()
    audit = pd.DataFrame([{"sample": "Primary low-disadvantage participants reporting postponement", "n_postponers": len(low), "n_count_observed": len(count), "count_median": count.median(), "count_q25": count.quantile(0.25), "count_q75": count.quantile(0.75), "raw_zero_n": int(count.eq(0).sum()), "raw_999_n": int(count.eq(999).sum()), "use": "Descriptive audit only; raw 0 and 999 retained; RH789 not part of score"}])
    write_results(audit, PATHS.tables_root / "share_postponement_count_audit.csv")
    support = analysis.groupby(["disadvantage_component_nonmissing", "disadvantage_group"], observed=True).agg(n=("disadvantage_score", "size"), never_regular_n=("rh015_", lambda values: int(values.eq(5).sum()))).reset_index()
    write_results(support, PATHS.tables_root / "share_component_observation_support.csv")


if __name__ == "__main__":
    main()
