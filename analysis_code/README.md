# Analysis code

These materials provide core statistical scripts for the main SHARE models, the all-four-component sensitivity analysis, the SHARE barrier models and the CHARLS/KLoSA contextual affordability analyses reported in the manuscript. They do not contain restricted individual-level SHARE, CHARLS or KLoSA records.

The scripts assume analysis-ready CSV datasets prepared from the official cohort data using the variable definitions reported in the manuscript and supplementary material. Readers who have approved access to the restricted cohort data can configure local input paths in `config/paths.py` or through environment variables.

Expected inputs:
- `SHARE_ANALYTIC_CSV`: SHARE analysis-ready dataset with the model variables used in `scripts/share_primary_models.py`, `scripts/all_four_sensitivity.py` and `scripts/share_barrier_models.py`. SHARE barrier models require either derived barrier indicators (`financial_barrier`, `structural_info_barrier`, `attitudinal_barrier`) or the raw barrier items listed in Supplementary Table S1.
- `CHARLS_ANALYTIC_CSV`: CHARLS analysis-ready dataset for contextual affordability analyses.
- `KLOSA_ANALYTIC_CSV`: KLoSA analysis-ready dataset for contextual affordability analyses.

Suggested order:
1. Configure local input and output paths.
2. Run `python scripts/share_primary_models.py`.
3. Run `python scripts/share_barrier_models.py`.
4. Run `python scripts/charls_context_check.py` and `python scripts/klosa_context_check.py`.
5. Run `python scripts/all_four_sensitivity.py`.

Aggregate source data supporting the manuscript tables and figures are supplied separately in `../source_data/`.
