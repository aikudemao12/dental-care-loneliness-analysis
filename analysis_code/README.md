# Analysis reproduction

The scripts write individual-level analysis-ready inputs only to a local data directory and report aggregate model/descriptive outputs. Approved access to each cohort's source data is required. Individual-level records must not be committed or redistributed.

Version: `EJPH-R1-20261019-v2`. The operational South/east Europe grouping used in Table 1 and Supplementary Table S3 comprises Spain (15), Italy (16), Greece (19), Czech Republic (28), Poland (29), Hungary (32), Portugal (33), Slovenia (34), Estonia (35), Croatia (47), Lithuania (48), Bulgaria (51), Cyprus (53), Latvia (57), Malta (59), Romania (61) and Slovakia (63). Portugal has no participants in the current primary sample. This release removes Luxembourg (31), includes Greece (19) and retains all other memberships. The grouping supplies descriptive percentages and standardised differences; regression adjustment uses country fixed effects.

## Prepare local inputs

Provide CSV exports of these official data sources:

- Harmonized SHARE Version F.2 respondent file: `mergeid`, demographic and Wave 6–8 fields listed in `build_analysis_inputs.py`.
- SHARE Wave 7 retrospective-health module: `mergeid`, `rh015_`, `rh016_`, `rh017_`, `rh018_`, `rh788_`, `rh789_` and `rh026d1`–`rh026d8`.
- Harmonized CHARLS respondent file, Version D (June 2021), with unprefixed variables or `h_charls_d_data__` prefixed merged variables.
- Harmonized KLoSA Version E.2 respondent file with unprefixed variables. The input preserves all 11,174 harmonised records without a study-specific row restriction; 6,940 have observed Wave 7 age (55–102 years). Model complete-case selection follows derivation; no additional age filter is applied.

Set `SHARE_HARMONIZED_CSV`, `SHARE_WAVE7_RH_CSV`, `CHARLS_HARMONIZED_CSV` and `KLOSA_HARMONIZED_CSV` to approved local source paths, then run:

```sh
export COHORT_DATA_ROOT=/path/to/restricted_inputs
export TABLES_ROOT=/path/to/aggregate_results
python scripts/build_analysis_inputs.py --output-dir "$COHORT_DATA_ROOT"
python scripts/run_all.py
```

The input builder also accepts the flags `--share-harmonized`, `--share-history`, `--charls-harmonized` and `--klosa-harmonized` instead of environment variables. No provider or personal filesystem paths are embedded in the scripts.

If inputs are stored elsewhere, set `COHORT_DATA_ROOT`, or set `SHARE_ANALYTIC_CSV`, `CHARLS_ANALYTIC_CSV` and `KLOSA_ANALYTIC_CSV` individually. Set `TABLES_ROOT` to choose the aggregate output directory. For participant data, choose a restricted directory outside the repository. The legacy default data directory is `analysis_code/data`; do not distribute it. Aggregate outputs default to `analysis_code/outputs/tables`.

## Execution and outputs

`run_all.py` first runs the scoring combination/boundary tests, then runs:

1. `share_primary_models.py`: primary grouped and per-point SHARE models and the existing CASP-12 secondary model.
2. `share_barrier_models.py`: three SHARE barrier models on their common complete-case subset.
3. `charls_context_check.py` and `klosa_context_check.py`: outcome-specific contextual models with positive baseline respondent weights and positive-cost high-expenditure thresholds.
4. `all_four_sensitivity.py`: the unchanged grouped model restricted to all four observed exposure components.
5. `share_revision_checks.py`: age 65/75 models, education-by-disadvantage summaries, the RH789 descriptive count audit and component-observation support.
6. `reproduce_source_data.py`: every existing figure/table aggregate, including score 0–4, all four fixed Wave 6 attenuation steps, country/leave-one-country-out/subgroup analyses, joint components for both SHARE outcomes, adjusted marginal means, outcome support, full Table 1 with standardized differences, attrition, missingness, sample flow and external threshold/group/rank checks. Outputs are under `$TABLES_ROOT/source_data`, with `results.json`, `external_group_checks.json` and `share_table1_full.csv`. The existing CSV schemas and names are retained, including the full descriptive export; static figure metadata are copied from `../source_data`.

The RH789 audit retains nonnegative raw values, including 0 and 999, for descriptive reporting. RH789 does not contribute to the exposure score. The corrected continuity component is 1 if RH015=5 or RH018=5, 0 only if both equal 1, and missing otherwise. The late/non-continuous component is 1 if valid start age exceeds 25 years or RH015=5 or RH018=5; it is 0 when childhood initiation (RH016=1) or valid start age at most 25 years is observed together with RH018=1, provided no adverse criterion applies; all other cases are missing. Valid start ages are 0–100 years. Childhood disadvantage is 1 for RH016=5 and for verified structural nonadministration following RH015=5; it is 0 for RH016=1. The input reader preserves original empty-cell indicators before converting negative or unknown responses to missing. The structural branch requires originally blank RH016 and RH018 cells, with no contradictory observed responses. DK, refusal and unknown responses remain missing; cleaned NaN values without source-empty evidence never trigger this rule. Scores are summed without rescaling only when at least three components are observed. The earlier source-response sensitivity has been incorporated into the corrected primary scoring and is no longer a separate current analysis. `share_scoring_correction_audit.csv` retains the previous correction history unchanged. `share_structural_skip_correction_audit.csv` records this structural-skip correction as aggregate transitions and inclusion counts; neither audit is an additional fitted model. Chronic burden is the sum of available binary diagnosis indicators and is missing when all 13 are missing. The supplied harmonized loneliness and CASP-12 scores are used as provided, without study imputation or rescoring.

Aggregate source files supporting the final tables and figures are in `../source_data/`. Source variable definitions and the correction to the original constant high-cost indicators are documented in the manuscript supplement and repository README.

The external thresholds are unweighted 75th percentiles among positive costs, calculated before outcome-specific complete-case filtering (CHARLS age ≥45 first; all KLoSA input records). `external_group_checks.json` records the resulting exposure-group counts and model-matrix ranks. The SHARE leave-one-country-out display retains the original reference: the mean of the 26 leave-one-country-out estimates for each contrast, stored as `mean_loo_reference`; `delta_from_mean_loo` records each deviation from this reference. Figure S2 labels it as the LOO mean.

To regenerate only the aggregate source tables in a separate destination:

```sh
python scripts/reproduce_source_data.py --input-dir "$COHORT_DATA_ROOT" --output-dir "$TABLES_ROOT/source_data"
```

`--template-dir` selects the existing aggregate CSV layout. `--legacy-metadata` is for historical baseline verification only; normal runs write the corrected scoring definitions.

The full descriptive export includes available-case denominators and the age-eligible score-computability comparison already reported in Supplementary Table S10. `share_score_computability.csv` is written alongside `results.json` in the aggregate output folder.

To regenerate the optional historical scoring-correction comparison from two local restricted files:

```sh
python scripts/scoring_correction_audit.py --previous /path/to/previous/share_analysis_dataset.csv --current "$COHORT_DATA_ROOT/share_analysis_dataset.csv" --output-dir "$TABLES_ROOT/correction_audit" --output-stem share_structural_skip_correction_audit
```

This command writes only aggregate counts/transitions. It verifies that non-scoring input columns are unchanged and does not export participant identifiers.

Every aggregate-suite model records the sample and weight fingerprints, formula, matrix dimensions and rank, and any nonestimable terms in `results.json`. Nonestimable coefficients and intervals are left missing and rendered as “Not estimable” in text summaries. Each Wave 6 attenuation ladder uses a single common complete-case sample throughout.
