# Analysis reproduction

The scripts write individual-level analysis-ready inputs only to a local data directory and report aggregate model/descriptive outputs. Approved access to each cohort's source data is required. Individual-level records must not be committed or redistributed.

## Prepare local inputs

Provide CSV exports of these official data sources:

- Harmonized SHARE respondent file: `mergeid`, demographic and Wave 6–8 fields listed in `build_analysis_inputs.py`.
- SHARE Wave 7 retrospective-health module: `mergeid`, `rh015_`, `rh016_`, `rh017_`, `rh018_`, `rh788_`, `rh789_` and `rh026d1`–`rh026d8`.
- Harmonized CHARLS respondent file with unprefixed variables or `h_charls_d_data__` prefixed merged variables.
- Harmonized KLoSA respondent file with unprefixed variables.

Set `SHARE_HARMONIZED_CSV`, `SHARE_WAVE7_RH_CSV`, `CHARLS_HARMONIZED_CSV` and `KLOSA_HARMONIZED_CSV` to approved local source paths, then run:

```sh
python scripts/build_analysis_inputs.py --output-dir data
python scripts/run_all.py
```

The input builder also accepts the flags `--share-harmonized`, `--share-history`, `--charls-harmonized` and `--klosa-harmonized` instead of environment variables. No provider or personal filesystem paths are embedded in the scripts.

If inputs are stored elsewhere, set `COHORT_DATA_ROOT`, or set `SHARE_ANALYTIC_CSV`, `CHARLS_ANALYTIC_CSV` and `KLOSA_ANALYTIC_CSV` individually. Set `TABLES_ROOT` to choose the aggregate output directory. Defaults are `analysis_code/data` and `analysis_code/outputs/tables`, both ignored by Git.

## Execution and outputs

`run_all.py` runs:

1. `share_primary_models.py`: primary grouped and per-point SHARE models and the existing CASP-12 secondary model.
2. `share_barrier_models.py`: three SHARE barrier models on their common complete-case subset.
3. `charls_context_check.py` and `klosa_context_check.py`: outcome-specific contextual models with positive baseline respondent weights and positive-cost high-expenditure thresholds.
4. `all_four_sensitivity.py`: the unchanged grouped model restricted to all four observed exposure components.
5. `share_revision_checks.py`: age 65/75 models, education-by-disadvantage summaries, the RH789 descriptive count audit and component-observation support.

The RH789 audit retains nonnegative raw values, including 0 and 999, for descriptive reporting. RH789 does not contribute to the exposure score. The exposure builder preserves the submitted scoring algorithm and explicitly records RH018 continuity after initiation. It does not fill structural childhood-care skips, change the at-least-three-component rule, or rescale the score. Chronic burden is the sum of available binary diagnosis indicators and is missing when all 13 are missing. The supplied harmonized loneliness and CASP-12 scores are used as provided, without study imputation or rescoring.

Aggregate source files supporting the final tables and figures are in `../source_data/`. Source variable definitions and the correction to the original constant high-cost indicators are documented in the manuscript supplement and repository README.
