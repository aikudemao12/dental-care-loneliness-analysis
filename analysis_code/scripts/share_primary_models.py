from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.paths import PATHS
from scripts.statistical_helpers import positive_weight_complete_case, weighted_linear_model, write_results


GROUP_TERM = "C(disadvantage_group, Treatment(reference='low_0_1'))"


def prepare_share_frame() -> pd.DataFrame:
    frame = pd.read_csv(PATHS.share_analytic, low_memory=False)
    frame["disadvantage_group"] = pd.Categorical(
        frame["disadvantage_group"],
        categories=["low_0_1", "mid_2", "high_3_4"],
        ordered=True,
    )
    frame["country"] = frame["country"].astype("category")
    return frame


def main() -> None:
    frame = prepare_share_frame()
    common_covariates = ["r7agey", "female", "education_level", "bmi", "chronic_burden", "country"]
    rows = []

    loneliness_columns = [
        "analysis_eligible_loneliness",
        "disadvantage_group",
        "disadvantage_score",
        "r8lnlys3",
        "r8wtresp",
        *common_covariates,
    ]
    loneliness = frame.loc[frame["analysis_eligible_loneliness"].eq(1)].copy()
    loneliness = positive_weight_complete_case(loneliness, loneliness_columns, "r8wtresp")

    rows.append(
        weighted_linear_model(
            loneliness,
            formula=f"r8lnlys3 ~ {GROUP_TERM} + r7agey + female + education_level + bmi + chronic_burden + C(country)",
            weight_col="r8wtresp",
            outcome="r8lnlys3",
            exposure="disadvantage_group",
            sample="SHARE loneliness primary model",
        )
    )
    rows.append(
        weighted_linear_model(
            loneliness,
            formula="r8lnlys3 ~ disadvantage_score + r7agey + female + education_level + bmi + chronic_burden + C(country)",
            weight_col="r8wtresp",
            outcome="r8lnlys3",
            exposure="disadvantage_score",
            sample="SHARE loneliness score model",
        )
    )

    if {"r7casp12", "r8casp12", "analysis_eligible_casp"}.issubset(frame.columns):
        casp_columns = [
            "analysis_eligible_casp",
            "disadvantage_group",
            "r7casp12",
            "r8casp12",
            "r8wtresp",
            *common_covariates,
        ]
        casp = frame.loc[frame["analysis_eligible_casp"].eq(1)].copy()
        casp = positive_weight_complete_case(casp, casp_columns, "r8wtresp")
        rows.append(
            weighted_linear_model(
                casp,
                formula=f"r8casp12 ~ {GROUP_TERM} + r7casp12 + r7agey + female + education_level + bmi + chronic_burden + C(country)",
                weight_col="r8wtresp",
                outcome="r8casp12",
                exposure="disadvantage_group",
                sample="SHARE CASP-12 secondary model",
            )
        )

    write_results(pd.concat(rows, ignore_index=True), PATHS.tables_root / "share_primary_models.csv")


if __name__ == "__main__":
    main()
