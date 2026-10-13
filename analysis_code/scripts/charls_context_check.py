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
    frame = pd.read_csv(PATHS.charls_analytic, low_memory=False)
    # CHARLS is designed for respondents aged 45 years or older. The
    # harmonised respondent file contains a small number of younger records;
    # exclude them before defining the contextual analytic frame.
    frame = frame.loc[frame["age_r2"].ge(45)].copy()
    frame["high_oopden_r2"], oop_threshold = positive_cost_burden(frame["oopden_r2"])
    rows = []
    covariates = ["age_r2", "female", "education_level", "married_partnered", "bmi", "current_smoker", "drink_level"]
    for exposure in ["no_dental_visit_r2", "high_oopden_r2"]:
        for outcome, baseline in [("cesd10_r3", "cesd10_r2"), ("flonel_r3", "flonel_r2")]:
            columns = [exposure, outcome, baseline, "weight_r2", *covariates]
            model_frame = positive_weight_complete_case(frame, columns, "weight_r2")
            rows.append(
                weighted_linear_model(
                    model_frame,
                    formula=f"{outcome} ~ {exposure} + {baseline} + age_r2 + female + education_level + married_partnered + bmi + current_smoker + drink_level",
                    weight_col="weight_r2",
                    outcome=outcome,
                    exposure=exposure,
                    sample="CHARLS contextual affordability analysis",
                )
            )
    result = pd.concat(rows, ignore_index=True)
    result["positive_cost_q75_rmb"] = oop_threshold
    write_results(result, PATHS.tables_root / "charls_context_check_models.csv")


if __name__ == "__main__":
    main()
