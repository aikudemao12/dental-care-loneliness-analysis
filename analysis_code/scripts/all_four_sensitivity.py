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


def main() -> None:
    frame = pd.read_csv(PATHS.share_analytic, low_memory=False)
    frame["disadvantage_group"] = pd.Categorical(
        frame["disadvantage_group"],
        categories=["low_0_1", "mid_2", "high_3_4"],
        ordered=True,
    )
    frame["country"] = frame["country"].astype("category")
    columns = [
        "analysis_eligible_loneliness",
        "disadvantage_component_nonmissing",
        "disadvantage_group",
        "r8lnlys3",
        "r8wtresp",
        "r7agey",
        "female",
        "education_level",
        "bmi",
        "chronic_burden",
        "country",
    ]
    analysis = frame.loc[
        frame["analysis_eligible_loneliness"].eq(1)
        & frame["disadvantage_component_nonmissing"].eq(4)
    ].copy()
    analysis = positive_weight_complete_case(analysis, columns, "r8wtresp")
    result = weighted_linear_model(
        analysis,
        formula=f"r8lnlys3 ~ {GROUP_TERM} + r7agey + female + education_level + bmi + chronic_burden + C(country)",
        weight_col="r8wtresp",
        outcome="r8lnlys3",
        exposure="disadvantage_group",
        sample="SHARE all-four-component sensitivity analysis",
    )
    keep = result["term"].str.contains("disadvantage_group", regex=False)
    write_results(result.loc[keep].copy(), PATHS.tables_root / "share_all_four_exposure_components_sensitivity.csv")


if __name__ == "__main__":
    main()
