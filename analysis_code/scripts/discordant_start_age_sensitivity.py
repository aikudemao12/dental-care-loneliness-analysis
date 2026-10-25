"""Reproduce the reported childhood-care/start-age discordance sensitivity.

Use the corrected SHARE analysis-ready input from build_analysis_inputs.py.
Only aggregate model results are written; participant records are not exported.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.paths import PATHS
from scripts.build_analysis_inputs import COMPONENTS
from scripts.statistical_helpers import (
    positive_weight_complete_case,
    require_columns,
    weighted_linear_model,
    write_results,
)

GROUPS = ["low_0_1", "mid_2", "high_3_4"]
GROUP_TERM = "C(disadvantage_group, Treatment(reference='low_0_1'))"
FORMULA = f"r8lnlys3 ~ {GROUP_TERM} + r7agey + female + education_level + bmi + chronic_burden + C(country)"
MODEL_COLUMNS = [
    "disadvantage_group", "r8lnlys3", "r8wtresp", "r7agey", "female",
    "education_level", "bmi", "chronic_burden", "country",
]


def sensitivity_results(frame: pd.DataFrame) -> pd.DataFrame:
    require_columns(
        frame,
        ["mergeid", "analysis_eligible_loneliness", "rh016_",
         "regular_dental_start_age", *COMPONENTS, *MODEL_COLUMNS],
    )
    primary = frame.loc[
        frame["analysis_eligible_loneliness"].eq(1) & frame["r7agey"].ge(50)
    ].copy()
    primary = positive_weight_complete_case(primary, MODEL_COLUMNS, "r8wtresp")
    primary["disadvantage_group"] = pd.Categorical(
        primary["disadvantage_group"], categories=GROUPS, ordered=True,
    )
    primary["country"] = primary["country"].astype("category").cat.remove_unused_categories()

    # RH016=5 indicates no regular care before age 16. The input builder has
    # already restricted derived start ages to 0-100; retain that valid range
    # explicitly when identifying the discordant records in the primary sample.
    discordant = (
        primary["rh016_"].eq(5)
        & primary["regular_dental_start_age"].between(0, 16, inclusive="left")
    )
    changed = primary.copy()
    changed.loc[discordant, ["disadv_childhood", "disadv_late_uptake"]] = np.nan
    changed["disadvantage_component_nonmissing"] = changed[COMPONENTS].notna().sum(axis=1)
    changed["disadvantage_score"] = changed[COMPONENTS].sum(axis=1, min_count=1).where(
        changed["disadvantage_component_nonmissing"].ge(3)
    )
    changed["disadvantage_group"] = pd.cut(
        changed["disadvantage_score"], [-0.1, 1, 2, 4], labels=GROUPS,
    )
    changed = positive_weight_complete_case(changed, MODEL_COLUMNS, "r8wtresp")
    changed["country"] = changed["country"].cat.remove_unused_categories()

    rows = []
    for name, analysis in [
        ("SHARE primary model", primary),
        ("SHARE discordant childhood-care/start-age sensitivity", changed),
    ]:
        result = weighted_linear_model(
            analysis,
            formula=FORMULA,
            weight_col="r8wtresp",
            outcome="r8lnlys3",
            exposure="disadvantage_group",
            sample=name,
        )
        result = result.loc[result["term"].str.contains("disadvantage_group", regex=False)].copy()
        result["contrast"] = result["term"].map({
            f"{GROUP_TERM}[T.mid_2]": "Mid disadvantage vs low",
            f"{GROUP_TERM}[T.high_3_4]": "High disadvantage vs low",
        })
        result["primary_n"] = len(primary)
        result["discordant_n"] = int(discordant.sum())
        result["excluded_from_primary_n"] = len(primary) - len(analysis)
        rows.append(result)
    return pd.concat(rows, ignore_index=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=PATHS.share_analytic)
    parser.add_argument(
        "--output", type=Path,
        default=PATHS.tables_root / "source_data" / "share_discordant_start_age_sensitivity.csv",
    )
    args = parser.parse_args()
    frame = pd.read_csv(args.input, dtype={"mergeid": str}, low_memory=False)
    result = sensitivity_results(frame)
    write_results(result, args.output)
    print(
        f"Discordance sensitivity reproduced: primary N={int(result['primary_n'].iloc[0])}, "
        f"discordant n={int(result['discordant_n'].iloc[0])}, "
        f"sensitivity N={int(result['n'].iloc[-1])}."
    )


if __name__ == "__main__":
    main()
