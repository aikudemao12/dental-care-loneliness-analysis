# Life-course dental-care disadvantage and loneliness among adults aged 50 years and older: a 26-country cohort analysis

Analysis code and aggregate source data for **Life-course dental-care disadvantage and loneliness among adults aged 50 years and older: a 26-country cohort analysis**.

Release: `EJPH-R1-20261019-v2` (see `VERSION`). This version identifies the Figure S2 reference as the mean of the 26 leave-one-country-out estimates, without changing numerical results, and synchronises figure font settings with the supplementary code archive. It retains the correction to the descriptive South/east Europe grouping by replacing Luxembourg with Greece and retaining all other memberships. The corresponding Table 1 and Supplementary Table S3 source rows have been regenerated. The grouping is used for descriptive summaries; models adjust for country. The operational country list is given in `analysis_code/README.md`.

## Contents and access

- `analysis_code/`: local input preparation and model scripts, including the age 65/75 analyses, all-four-component sensitivity and descriptive revision checks.
- `source_data/`: aggregate data supporting manuscript tables and figures.

Individual-level SHARE, CHARLS and KLoSA records must be obtained from their official data providers under their data-use conditions. They are not redistributed here. The local input builder writes restricted CSVs to an ignored data directory. Do not commit those inputs or individual-level outputs.

## Reproduction

See `analysis_code/README.md` for the source variable requirements, configurable local input paths and execution order. `build_analysis_inputs.py` prepares the model inputs from approved harmonized SHARE, Wave 7 retrospective-health, harmonized CHARLS and harmonized KLoSA CSVs. `run_all.py` then runs the reported models, descriptive summaries and revision checks.

The SHARE continuity and late-uptake components were corrected so that unresolved source responses remain missing. The four domains, observed-component sum, group thresholds and model specifications are retained. The third component is described accurately as **late uptake or non-continuous regular care**: it includes initiation after age 25, never having regular care and discontinuity after initiation. It overlaps with the adult-continuity component. The score sums observed adverse components without rescaling when at least three are observed. For never-regular-care respondents (RH015=5), verified structural non-administration of RH016 establishes childhood disadvantage=1. Original blank source cells are distinguished from refusal, do-not-know and unknown responses. The all-four-component sensitivity requires four nonmissing derived components; it includes never-regular-care respondents whose postponement component is observed.

## Correction to the external visiting and expenditure analyses

The revised CHARLS and KLoSA models define the high-cost threshold at the unweighted 75th percentile among **strictly positive** dental out-of-pocket costs: 600 RMB and 100 units of 10,000 Korean won, respectively. Zero costs remain in the reference category. Thresholds are calculated before model complete-case selection; CHARLS first restricts baseline age to at least 45 years, and KLoSA uses the existing full input.

In the original all-cost calculation, the 75th percentile was zero in both cohorts. The resulting high-cost indicator was constant at one and collinear with the intercept; its displayed coefficient did not estimate a high-versus-low-cost contrast. The revised files correct that calculation and replace the external high-cost estimates. Outcome coding is unchanged. The preceding correction of unresolved SHARE responses reduced the primary sample from 30,908 to 30,782. Applying the verified structural childhood-care branch then retained those participants and added 15, giving 30,797. Aggregate correction audits retain both stages; current results are provided in the source files.

## Environment and license

The analyses use Python 3.12; requirements are listed in `analysis_code/requirements.txt` and the original environment record in `analysis_code/requirements_exact.txt`. The MIT license applies to analysis code. Aggregate source data are provided for manuscript inspection and reuse with citation while respecting the cohort providers' restrictions.
