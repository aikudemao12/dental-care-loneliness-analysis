"""Descriptive routines retained from the existing analysis, without I/O side effects."""

from typing import Callable

import numpy as np

import pandas as pd

def weighted_mean(series: pd.Series, weights: pd.Series) -> float:
    mask = series.notna() & weights.notna() & (weights > 0)
    if mask.sum() == 0:
        return np.nan
    return float(np.average(series.loc[mask], weights=weights.loc[mask]))

def weighted_sd(series: pd.Series, weights: pd.Series) -> float:
    mask = series.notna() & weights.notna() & (weights > 0)
    if mask.sum() == 0:
        return np.nan
    x = series.loc[mask].to_numpy(dtype=float)
    w = weights.loc[mask].to_numpy(dtype=float)
    mean = np.average(x, weights=w)
    var = np.average((x - mean) ** 2, weights=w)
    return float(np.sqrt(var))

def weighted_proportion(series: pd.Series, weights: pd.Series, value=1) -> float:
    mask = series.notna() & weights.notna() & (weights > 0)
    if mask.sum() == 0:
        return np.nan
    indicator = (series.loc[mask] == value).astype(float)
    return float(np.average(indicator, weights=weights.loc[mask]))

def summarize_table1(analytic_lon: pd.DataFrame) -> pd.DataFrame:
    groups = ["overall", "low_0_1", "mid_2", "high_3_4"]
    rows: list[dict[str, str]] = []

    def subset_for(group: str) -> pd.DataFrame:
        if group == "overall":
            return analytic_lon
        return analytic_lon.loc[analytic_lon["disadvantage_group"] == group]

    def fmt_mean_sd(series: pd.Series, weights: pd.Series) -> str:
        return f"{weighted_mean(series, weights):.3f} ({weighted_sd(series, weights):.3f})"

    def fmt_prop(series: pd.Series, weights: pd.Series) -> str:
        return f"{weighted_proportion(series, weights) * 100:.1f}"

    def fmt_available(column: str) -> Callable[[pd.DataFrame, pd.Series], str]:
        def formatter(sub: pd.DataFrame, weights: pd.Series) -> str:
            return f"{sub[column].notna().mean() * 100:.1f}"

        return formatter

    def weighted_var(series: pd.Series, weights: pd.Series) -> float:
        values = pd.to_numeric(series, errors="coerce").to_numpy(dtype=float)
        w = pd.to_numeric(weights, errors="coerce").to_numpy(dtype=float)
        mask = np.isfinite(values) & np.isfinite(w) & (w > 0)
        values = values[mask]
        w = w[mask]
        if values.size <= 1:
            return 0.0
        mean = np.average(values, weights=w)
        return float(np.average((values - mean) ** 2, weights=w))

    def weighted_binary_asd(series_a: pd.Series, w_a: pd.Series, series_b: pd.Series, w_b: pd.Series) -> float:
        p1 = weighted_proportion(series_a, w_a)
        p0 = weighted_proportion(series_b, w_b)
        pooled = (p1 * (1 - p1) + p0 * (1 - p0)) / 2
        return abs(p1 - p0) / np.sqrt(pooled) if pooled > 0 else np.nan

    def weighted_cont_asd(series_a: pd.Series, w_a: pd.Series, series_b: pd.Series, w_b: pd.Series) -> float:
        m1 = weighted_mean(series_a, w_a)
        m0 = weighted_mean(series_b, w_b)
        v1 = weighted_var(series_a, w_a)
        v0 = weighted_var(series_b, w_b)
        pooled_sd = np.sqrt((v1 + v0) / 2)
        return abs(m1 - m0) / pooled_sd if pooled_sd > 0 else np.nan

    def fmt_asd(value: float) -> str:
        if not np.isfinite(value):
            return "—"
        return f"{value:.3f}"

    def binary_available(column: str) -> bool:
        return column in analytic_lon.columns and analytic_lon[column].notna().any()

    def fmt_category_prop(column: str, predicate: Callable[[pd.Series], pd.Series]) -> Callable[[pd.DataFrame, pd.Series], str]:
        def formatter(sub: pd.DataFrame, weights: pd.Series) -> str:
            series = pd.to_numeric(sub[column], errors="coerce")
            derived = np.where(predicate(series), 1.0, 0.0)
            derived = pd.Series(derived, index=sub.index, dtype=float)
            derived.loc[series.isna()] = np.nan
            return fmt_prop(derived, weights)

        return formatter

    def fmt_r6_complete(sub: pd.DataFrame, weights: pd.Series) -> str:
        required = [
            "r7agey",
            "female",
            "education_level",
            "married_partnered",
            "bmi",
            "chronic_burden",
            "country",
            "r8lnlys3",
            "r6_smoke_ever",
            "r6_drink_freq",
            "r6eurod",
            "r6lnlys3",
        ]
        if any(col not in sub.columns for col in required):
            return ""
        return f"{sub[required].notna().all(axis=1).mean() * 100:.1f}"

    def asd_category_prop(
        column: str,
        predicate: Callable[[pd.Series], pd.Series],
        sub_a: pd.DataFrame,
        sub_b: pd.DataFrame,
    ) -> str:
        series_a = pd.to_numeric(sub_a[column], errors="coerce")
        series_b = pd.to_numeric(sub_b[column], errors="coerce")
        val_a = pd.Series(np.where(predicate(series_a), 1.0, 0.0), index=sub_a.index, dtype=float)
        val_b = pd.Series(np.where(predicate(series_b), 1.0, 0.0), index=sub_b.index, dtype=float)
        val_a.loc[series_a.isna()] = np.nan
        val_b.loc[series_b.isna()] = np.nan
        return fmt_asd(weighted_binary_asd(val_a, sub_a["r8wtresp"], val_b, sub_b["r8wtresp"]))

    def add_binary_derivative(column: str, source: str, predicate: Callable[[pd.Series], pd.Series]) -> None:
        if source in analytic_lon.columns and column not in analytic_lon.columns:
            analytic_lon[column] = np.where(predicate(analytic_lon[source]), 1.0, 0.0)
            analytic_lon.loc[analytic_lon[source].isna(), column] = np.nan

    add_binary_derivative("age_65_plus", "r7agey", lambda s: s >= 65)
    add_binary_derivative("education_lower_secondary_or_less", "education_level", lambda s: s <= 2)
    add_binary_derivative("bmi_obese", "bmi", lambda s: s >= 30)
    add_binary_derivative("chronic_burden_2plus", "chronic_burden", lambda s: s >= 2)
    # Operational grouping for Table 1/S3 descriptions; country fixed effects enter models.
    # EJPH-R1-20261019: include Greece (19), exclude Luxembourg (31); other codes retained.
    add_binary_derivative("country_south_or_east_europe", "country_code", lambda s: s.isin([15, 16, 19, 28, 29, 32, 33, 34, 35, 47, 48, 51, 53, 57, 59, 61, 63]))

    metrics: list[tuple[str, str, callable, str]] = [
        ("Sample structure", "section", None, "section"),
        ("Unweighted N", "n", lambda sub, w: f"{len(sub):,}", "meta"),
        ("Weighted sample share, %", "weighted_share", lambda sub, w: f"{(w.sum() / analytic_lon['r8wtresp'].sum()) * 100:.1f}", "meta"),
        ("Countries represented", "country_count", lambda sub, w: f"{sub['country_code'].nunique():,}", "meta"),
        ("Exposure construction", "section", None, "section"),
        ("Mean disadvantage score", "disadvantage_score", fmt_mean_sd, "continuous"),
        ("No regular childhood dental care, %", "disadv_childhood", fmt_prop, "binary"),
        ("No stable adult regular care, %", "disadv_adult_pattern", fmt_prop, "binary"),
        ("Late/absent uptake of regular care, %", "disadv_late_uptake", fmt_prop, "binary"),
        ("Lifetime dental postponement, %", "disadv_postponed", fmt_prop, "binary"),
        ("Sociodemographic profile", "section", None, "section"),
        ("Age, years", "r7agey", fmt_mean_sd, "continuous"),
        ("Age >=65 years, %", "age_65_plus", fmt_prop, "binary"),
        ("Age 50-64 years, %", "r7agey", fmt_category_prop("r7agey", lambda s: (s >= 50) & (s <= 64)), "derived_binary"),
        ("Age 65-74 years, %", "r7agey", fmt_category_prop("r7agey", lambda s: (s >= 65) & (s <= 74)), "derived_binary"),
        ("Age >=75 years, %", "r7agey", fmt_category_prop("r7agey", lambda s: s >= 75), "derived_binary"),
        ("Female, %", "female", fmt_prop, "binary"),
        ("Education level, mean (SD)", "education_level", fmt_mean_sd, "continuous"),
        ("Lower education, %", "education_lower_secondary_or_less", fmt_prop, "binary"),
        ("Education category 1, %", "education_level", fmt_category_prop("education_level", lambda s: s == 1), "derived_binary"),
        ("Education category 2, %", "education_level", fmt_category_prop("education_level", lambda s: s == 2), "derived_binary"),
        ("Education category 3, %", "education_level", fmt_category_prop("education_level", lambda s: s == 3), "derived_binary"),
        ("Married or partnered, %", "married_partnered", fmt_prop, "binary"),
        ("South/east Europe, %", "country_south_or_east_europe", fmt_prop, "binary"),
        ("Health profile", "section", None, "section"),
        ("BMI, kg/m2", "bmi", fmt_mean_sd, "continuous"),
        ("BMI >=30 kg/m2, %", "bmi_obese", fmt_prop, "binary"),
        ("Chronic disease burden", "chronic_burden", fmt_mean_sd, "continuous"),
        ("No chronic conditions, %", "chronic_burden", fmt_category_prop("chronic_burden", lambda s: s == 0), "derived_binary"),
        ("One chronic condition, %", "chronic_burden", fmt_category_prop("chronic_burden", lambda s: s == 1), "derived_binary"),
        ("Chronic burden >=2, %", "chronic_burden_2plus", fmt_prop, "binary"),
        ("Data availability in analytic frame", "section", None, "section"),
        ("Wave 6 ever-smoked proxy available, %", "r6_smoke_ever", fmt_available("r6_smoke_ever"), "meta") if binary_available("r6_smoke_ever") else None,
        ("Wave 6 recent drinking indicator available, %", "r6_drink_freq", fmt_available("r6_drink_freq"), "meta") if "r6_drink_freq" in analytic_lon.columns else None,
        ("Wave 6 EURO-D available, %", "r6eurod", fmt_available("r6eurod"), "meta") if "r6eurod" in analytic_lon.columns else None,
        ("Wave 6 prior loneliness available, %", "r6lnlys3", fmt_available("r6lnlys3"), "meta") if "r6lnlys3" in analytic_lon.columns else None,
        ("Wave 6 complete proxy subset available, %", "r6_proxy_complete", fmt_r6_complete, "meta")
        if all(col in analytic_lon.columns for col in ["r7agey", "female", "education_level", "married_partnered", "bmi", "chronic_burden", "country", "r8lnlys3", "r6_smoke_ever", "r6_drink_freq", "r6eurod", "r6lnlys3"])
        else None,
        ("Wave 8 CASP-12 available, %", "r8casp12", fmt_available("r8casp12"), "meta") if "r8casp12" in analytic_lon.columns else None,
        ("Wave 8 ADL available, %", "r8adla", fmt_available("r8adla"), "meta") if "r8adla" in analytic_lon.columns else None,
        ("Wave 8 IADL available, %", "r8iadla", fmt_available("r8iadla"), "meta") if "r8iadla" in analytic_lon.columns else None,
        ("Descriptive outcome context", "section", None, "section"),
        ("Wave 8 loneliness", "r8lnlys3", fmt_mean_sd, "continuous"),
        ("Wave 8 CASP-12", "r8casp12", fmt_mean_sd, "continuous"),
        ("Wave 8 ADL count", "r8adla", fmt_mean_sd, "continuous"),
        ("Wave 8 IADL count", "r8iadla", fmt_mean_sd, "continuous"),
    ]
    metrics = [metric for metric in metrics if metric is not None]

    low_sub = subset_for("low_0_1")
    low_w = low_sub["r8wtresp"]
    for label, column, formatter, metric_type in metrics:
        row: dict[str, str] = {"Characteristic": label}
        if metric_type == "section":
            row.update(
                {
                    "overall": "",
                    "low_0_1": "",
                    "mid_2": "",
                    "high_3_4": "",
                    "mid_vs_low_asd": "",
                    "high_vs_low_asd": "",
                }
            )
            rows.append(row)
            continue
        for group in groups:
            sub = subset_for(group)
            weights = sub["r8wtresp"]
            if column in {"n", "weighted_share", "country_count"}:
                row[group] = formatter(sub, weights)
            elif metric_type in {"meta", "derived_binary"}:
                row[group] = formatter(sub, weights)
            else:
                row[group] = formatter(sub[column], weights)
        if metric_type == "binary":
            mid_sub = subset_for("mid_2")
            high_sub = subset_for("high_3_4")
            row["mid_vs_low_asd"] = fmt_asd(weighted_binary_asd(mid_sub[column], mid_sub["r8wtresp"], low_sub[column], low_w))
            row["high_vs_low_asd"] = fmt_asd(weighted_binary_asd(high_sub[column], high_sub["r8wtresp"], low_sub[column], low_w))
        elif metric_type == "derived_binary":
            mid_sub = subset_for("mid_2")
            high_sub = subset_for("high_3_4")
            if label == "Age 50-64 years, %":
                predicate = lambda s: (s >= 50) & (s <= 64)
            elif label == "Age 65-74 years, %":
                predicate = lambda s: (s >= 65) & (s <= 74)
            elif label == "Age >=75 years, %":
                predicate = lambda s: s >= 75
            elif label == "Education category 1, %":
                predicate = lambda s: s == 1
            elif label == "Education category 2, %":
                predicate = lambda s: s == 2
            elif label == "Education category 3, %":
                predicate = lambda s: s == 3
            elif label == "No chronic conditions, %":
                predicate = lambda s: s == 0
            else:
                predicate = lambda s: s == 1
            row["mid_vs_low_asd"] = asd_category_prop(column, predicate, mid_sub, low_sub)
            row["high_vs_low_asd"] = asd_category_prop(column, predicate, high_sub, low_sub)
        elif metric_type == "continuous":
            mid_sub = subset_for("mid_2")
            high_sub = subset_for("high_3_4")
            row["mid_vs_low_asd"] = fmt_asd(weighted_cont_asd(mid_sub[column], mid_sub["r8wtresp"], low_sub[column], low_w))
            row["high_vs_low_asd"] = fmt_asd(weighted_cont_asd(high_sub[column], high_sub["r8wtresp"], low_sub[column], low_w))
        else:
            row["mid_vs_low_asd"] = ""
            row["high_vs_low_asd"] = ""
        rows.append(row)

    table1 = pd.DataFrame(rows)
    table1 = table1.rename(
        columns={
            "overall": "Overall",
            "low_0_1": "Low (0-1)",
            "mid_2": "Mid (2)",
            "high_3_4": "High (3-4)",
            "mid_vs_low_asd": "Mid vs low ASD",
            "high_vs_low_asd": "High vs low ASD",
        }
    )
    return table1
