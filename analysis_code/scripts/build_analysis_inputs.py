"""Build restricted analysis-ready CSVs locally from approved cohort CSVs.

This implements evidence-based zero/one coding for the corrected score.
Verified never-regular-care skips imply childhood disadvantage; unknown
retrospective responses remain missing.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from config.paths import PATHS

CONDITIONS = ["hibpe", "diabe", "cancre", "lunge", "hearte", "stroke", "arthre", "psyche", "hchole", "parkine", "catracte", "ulcere", "kidneye"]
COMPONENTS = ["disadv_childhood", "disadv_adult_pattern", "disadv_late_uptake", "disadv_postponed"]
BARRIERS = {"financial_barrier": ["rh026d1", "rh026d2", "rh026d3"], "structural_info_barrier": ["rh026d4", "rh026d5", "rh026d7"], "attitudinal_barrier": ["rh026d6", "rh026d8"]}
SHARE_COLUMNS = ["mergeid", "country", "rabyear", "ragender", "raeducl", "r7agey", "r7bmi", "r7mstat", "r7lnlys3", "r8lnlys3", "r7casp12", "r8casp12", "r8wtresp", "r6smokev", "r6drinkxw", "r6eurod", "r6lnlys3", "r7smoken", "r7drinkxw", "r7adla", "r8adla", "r7iadla", "r8iadla", "r7eurod"] + ["r7" + name for name in CONDITIONS]
RH_COLUMNS = ["mergeid", "rh015_", "rh016_", "rh017_", "rh018_", "rh788_", "rh789_"] + [f"rh026d{i}" for i in range(1, 9)]


def read_source(path: Path, columns: list[str], identifier: str, prefix: str = "") -> pd.DataFrame:
    wanted = set(columns) | {prefix + column for column in columns}
    frame = pd.read_csv(path, usecols=lambda name: name in wanted, dtype={identifier: str, prefix + identifier: str}, low_memory=False, keep_default_na=False)
    if prefix:
        frame = frame.rename(columns={name: name.removeprefix(prefix) for name in frame.columns})
    absent = set(columns) - set(frame.columns)
    if absent:
        raise ValueError(f"Missing source variables: {', '.join(sorted(absent))}")
    if frame[identifier].isna().any() or frame[identifier].str.strip().eq('').any() or frame[identifier].duplicated().any():
        raise ValueError(f"The source identifier {identifier} must be nonmissing and unique.")
    # Capture actual empty source cells BEFORE negative response codes or text
    # unknowns are converted to NaN. A cleaned NaN alone is not skip evidence.
    for column in ['rh016_', 'rh018_']:
        if column in frame:
            frame[column.rstrip('_') + '_raw_blank'] = frame[column].astype(str).str.strip().eq('')
    numeric = [column for column in columns if column != identifier]
    frame[numeric] = frame[numeric].apply(pd.to_numeric, errors="coerce")
    frame[numeric] = frame[numeric].where(frame[numeric].ge(0))
    return frame


def partnered(values: pd.Series) -> pd.Series:
    return values.map({1: 1.0, 2: 1.0, 3: 1.0, 4: 0.0, 5: 0.0, 7: 0.0, 8: 0.0})


def binary_yes_no(values: pd.Series) -> pd.Series:
    return values.map({1: 1.0, 5: 0.0})


def derive_share(harmonized: pd.DataFrame, history: pd.DataFrame) -> pd.DataFrame:
    frame = harmonized.merge(history, on="mergeid", how="left", validate="one_to_one")
    ever = binary_yes_no(frame["rh015_"])
    continuity = binary_yes_no(frame["rh018_"])
    frame["disadv_childhood"] = 1 - binary_yes_no(frame["rh016_"])
    raw_blank = lambda name: frame[name].eq(True) if name in frame else pd.Series(False, index=frame.index)
    structural_childhood_skip = (frame['rh015_'].eq(5) & frame['rh016_'].isna()
                                 & frame['rh018_'].isna()
                                 & raw_blank('rh016_raw_blank') & raw_blank('rh018_raw_blank'))
    frame.loc[structural_childhood_skip, 'disadv_childhood'] = 1.0
    adult = pd.Series(np.nan, index=frame.index, dtype=float)
    adult.loc[ever.eq(1) & continuity.eq(1)] = 0.0
    adult.loc[ever.eq(0) | continuity.eq(0)] = 1.0
    frame["disadv_adult_pattern"] = adult
    start = frame["rh017_"] - frame["rabyear"]
    frame["regular_dental_start_age"] = start.where(start.between(0, 100))
    # RH017 is structurally skipped after childhood initiation. A zero requires
    # evidence of early initiation AND continuity; unknown responses stay missing.
    late = pd.Series(np.nan, index=frame.index, dtype=float)
    early = frame["rh016_"].eq(1) | frame["regular_dental_start_age"].le(25)
    late.loc[early & continuity.eq(1)] = 0.0
    late.loc[frame["regular_dental_start_age"].gt(25) | ever.eq(0) | continuity.eq(0)] = 1.0
    frame["disadv_late_uptake"] = late
    frame["disadv_postponed"] = binary_yes_no(frame["rh788_"])
    frame["disadvantage_component_nonmissing"] = frame[COMPONENTS].notna().sum(axis=1)
    frame["disadvantage_score"] = frame[COMPONENTS].sum(axis=1, min_count=1)
    frame.loc[frame["disadvantage_component_nonmissing"].lt(3), "disadvantage_score"] = np.nan
    frame["disadvantage_group"] = pd.cut(frame["disadvantage_score"], [-0.1, 1, 2, 4], labels=["low_0_1", "mid_2", "high_3_4"])
    for name, columns in BARRIERS.items():
        items = frame[columns]
        frame[name] = items.eq(1).any(axis=1).astype(float)
        frame.loc[items.isna().all(axis=1), name] = np.nan
    diagnoses = frame[["r7" + name for name in CONDITIONS]].where(lambda values: values.isin([0, 1]))
    frame["chronic_burden"] = diagnoses.sum(axis=1, min_count=1)
    frame["female"] = frame["ragender"].map({1: 0.0, 2: 1.0})
    frame["education_level"] = frame["raeducl"]
    frame["bmi"] = frame["r7bmi"]
    frame["married_partnered"] = partnered(frame["r7mstat"])
    frame["r6_smoke_ever"] = frame["r6smokev"].eq(1).astype(float).where(frame["r6smokev"].notna())
    # r6drinkxw is a binary indicator for alcohol use in the last 7 days.
    frame["r6_recent_drinking"] = frame["r6drinkxw"]
    frame["r6_drink_freq"] = frame["r6_recent_drinking"]  # legacy internal alias
    if "r7smoken" in frame:
        frame["current_smoker"] = frame["r7smoken"].eq(1).astype(float).where(frame["r7smoken"].notna())
    if "r7drinkxw" in frame:
        frame["drink_freq"] = frame["r7drinkxw"]
    common = frame["r7agey"].ge(50) & frame[["disadvantage_score", "r8wtresp", "female", "education_level", "bmi", "chronic_burden"]].notna().all(axis=1)
    frame["analysis_eligible_loneliness"] = (common & frame["r8lnlys3"].notna()).astype(int)
    frame["analysis_eligible_casp"] = (common & frame[["r7casp12", "r8casp12"]].notna().all(axis=1)).astype(int)
    return frame


def derive_external(frame: pd.DataFrame, cohort: str) -> pd.DataFrame:
    wave = 2 if cohort == "CHARLS" else 7
    suffix = "1y" if cohort == "CHARLS" else ""
    for derived, raw in {f"dentst_r{wave}": f"r{wave}dentst{suffix}", f"oopden_r{wave}": f"r{wave}oopden{suffix}", f"age_r{wave}": f"r{wave}agey", "bmi": "r2mbmi" if cohort == "CHARLS" else "r7bmi", "drink_level": "r2drinkl" if cohort == "CHARLS" else "r7drink", f"weight_r{wave}": "r2wtrespb" if cohort == "CHARLS" else "r7wtresp"}.items():
        frame[derived] = frame[raw]
    for current in [wave, wave + 1]:
        frame[f"flonel_r{current}"] = frame[f"r{current}flonel"]
        frame[f"cesd10_r{current}"] = frame[f"r{current}cesd10" + ("" if cohort == "CHARLS" else "b")]
    frame["female"] = frame["ragender"].map({1: 0.0, 2: 1.0})
    frame["education_level"] = frame["raeducl"]
    frame["married_partnered"] = partnered(frame[f"r{wave}mstat"])
    frame["current_smoker"] = frame[f"r{wave}smoken"].eq(1).astype(float).where(frame[f"r{wave}smoken"].notna())
    frame[f"no_dental_visit_r{wave}"] = frame[f"dentst_r{wave}"].eq(0).astype(float).where(frame[f"dentst_r{wave}"].notna())
    # Corrected positive-cost thresholds and CHARLS >=45 restriction are applied
    # by the cohort model scripts, after reading these analysis-ready inputs.
    return frame


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for flag, env in [("share-harmonized", "SHARE_HARMONIZED_CSV"), ("share-history", "SHARE_WAVE7_RH_CSV"), ("charls-harmonized", "CHARLS_HARMONIZED_CSV"), ("klosa-harmonized", "KLOSA_HARMONIZED_CSV")]:
        parser.add_argument("--" + flag, type=Path, default=os.environ.get(env))
    parser.add_argument("--output-dir", type=Path, default=PATHS.data_root)
    args = parser.parse_args()
    if any(getattr(args, name) is None for name in ["share_harmonized", "share_history", "charls_harmonized", "klosa_harmonized"]):
        parser.error("Provide all four approved local source CSV paths using flags or their documented environment variables.")
    share = derive_share(read_source(args.share_harmonized, SHARE_COLUMNS, "mergeid"), read_source(args.share_history, RH_COLUMNS, "mergeid"))
    charls_columns = ["ID", "r2dentst1y", "r2oopden1y", "r2cesd10", "r3cesd10", "r2flonel", "r3flonel", "r2agey", "ragender", "raeducl", "r2mstat", "r2mbmi", "r2smoken", "r2drinkl", "r2wtrespb"]
    klosa_columns = ["pid", "r7dentst", "r7oopden", "r7cesd10b", "r8cesd10b", "r7flonel", "r8flonel", "r7agey", "ragender", "raeducl", "r7mstat", "r7bmi", "r7smoken", "r7drink", "r7wtresp"]
    charls = derive_external(read_source(args.charls_harmonized, charls_columns, "ID", "h_charls_d_data__"), "CHARLS")
    klosa = derive_external(read_source(args.klosa_harmonized, klosa_columns, "pid"), "KLoSA")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in [("share_analysis_dataset.csv", share), ("charls_context_dataset.csv", charls), ("klosa_context_dataset.csv", klosa)]:
        frame.to_csv(args.output_dir / name, index=False)
    print("Restricted local inputs prepared; do not commit or redistribute individual-level CSVs.")


if __name__ == "__main__":
    main()
