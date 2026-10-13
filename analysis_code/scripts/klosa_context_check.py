from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.paths import PATHS
from scripts.statistical_helpers import (
    positive_cost_burden,
    positive_weight_complete_case,
    weighted_linear_model,
    write_results,
)


def main() -> None:
    frame = pd.read_csv(PATHS.klosa_analytic, low_memory=False)
    frame["high_oopden_r7"], oop_threshold = positive_cost_burden(frame["oopden_r7"])
    rows = []
    covariates = ["age_r7", "female", "education_level", "married_partnered", "bmi", "current_smoker", "drink_level"]
    for exposure in ["no_dental_visit_r7", "high_oopden_r7"]:
        for outcome, baseline in [("cesd10_r8", "cesd10_r7"), ("flonel_r8", "flonel_r7")]:
            columns = [exposure, outcome, baseline, "weight_r7", *covariates]
            model_frame = positive_weight_complete_case(frame, columns, "weight_r7")
            rows.append(
                weighted_linear_model(
                    model_frame,
                    formula=f"{outcome} ~ {exposure} + {baseline} + age_r7 + female + education_level + married_partnered + bmi + current_smoker + drink_level",
                    weight_col="weight_r7",
                    outcome=outcome,
                    exposure=exposure,
                    sample="KLoSA contextual affordability analysis",
                )
            )
    result = pd.concat(rows, ignore_index=True)
    result["positive_cost_q75_10000_krw"] = oop_threshold
    write_results(result, PATHS.tables_root / "klosa_context_check_models.csv")


if __name__ == "__main__":
    main()
