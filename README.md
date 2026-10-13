# Life-course dental-care disadvantage and loneliness among older adults

Analysis code and aggregate source data for **Life-course dental-care disadvantage and loneliness among older adults: a 26-country SHARE cohort analysis**.

## Contents and access

- `analysis_code/`: local input preparation and model scripts, including the age 65/75 analyses, all-four-component sensitivity and descriptive revision checks.
- `source_data/`: aggregate data supporting manuscript tables and figures.

Individual-level SHARE, CHARLS and KLoSA records must be obtained from their official data providers under their data-use conditions. They are not redistributed here. The local input builder writes restricted CSVs to an ignored data directory. Do not commit those inputs or individual-level outputs.

## Reproduction

See `analysis_code/README.md` for the source variable requirements, configurable local input paths and execution order. `build_analysis_inputs.py` prepares the model inputs from approved harmonized SHARE, Wave 7 retrospective-health, harmonized CHARLS and harmonized KLoSA CSVs. `run_all.py` then runs the reported core models and revision checks.

The SHARE exposure algorithm is unchanged from the submitted analysis. The third component is described accurately as **late uptake or non-continuous regular care**: it includes initiation after age 25, never having regular care and discontinuity after initiation. It overlaps with the adult-continuity component. The score sums observed adverse components without rescaling when at least three are observed. Structural childhood-care skips for never-regular-care respondents remain missing; the all-four-component sensitivity therefore excludes that group.

## Correction to the external affordability analyses

The revised CHARLS and KLoSA models define the high-cost threshold at the 75th percentile among **strictly positive** dental out-of-pocket costs: 600 RMB and 100 units of 10,000 Korean won, respectively. Zero costs remain in the reference category. CHARLS models restrict baseline age to at least 45 years before threshold formation.

In the original all-cost calculation, the 75th percentile was zero in both cohorts. The resulting high-cost indicator was constant at one and collinear with the intercept; its displayed coefficient did not estimate a high-versus-low-cost contrast. The revised files correct that calculation and replace the external high-cost estimates. Outcome coding is unchanged. SHARE model estimates are unchanged.

## Environment and license

The analyses use Python 3.12; requirements are listed in `analysis_code/requirements.txt` and the original environment record in `analysis_code/requirements_exact.txt`. The MIT license applies to analysis code. Aggregate source data are provided for manuscript inspection and reuse with citation while respecting the cohort providers' restrictions.
