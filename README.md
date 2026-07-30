# Life-course dental-care disadvantage and later-life loneliness

Analysis code and aggregate source data for the manuscript:

**Life-course dental-care disadvantage and later-life loneliness across 26 European countries: a SHARE cohort analysis**

## Contents

- `analysis_code/`: Python scripts for the SHARE primary models, SHARE barrier models, all-four-component sensitivity analysis, and CHARLS/KLoSA contextual affordability analyses.
- `source_data/`: de-identified aggregate source data underlying the manuscript tables, main figures, and supplementary figures.

## Data access

This repository does not contain individual-level SHARE, CHARLS, or KLoSA records. Individual-level data must be obtained from the original cohort data providers and used under their data-use conditions.

The aggregate CSV files in `source_data/` are provided to support inspection of the manuscript tables and figures. They should not be used to attempt reconstruction or re-identification of individual participant records.

## Reproducing analyses

The scripts require local, analysis-ready CSV files prepared from approved access to the underlying cohort data. Configure input paths in `analysis_code/config/paths.py` or with the environment variables described in `analysis_code/README.md`.

The analyses were run in Python 3.12. Package requirements are listed in `analysis_code/requirements.txt`; the environment record is provided in `analysis_code/requirements_exact.txt`.

## License

The MIT license applies to the analysis code in `analysis_code/`. The aggregate source data are provided for manuscript inspection and reuse with citation of this repository, while respecting the access and redistribution conditions of the original cohort data providers.
