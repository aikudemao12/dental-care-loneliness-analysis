Aggregate source data for manuscript tables, figures and reported sensitivity analyses.

The South/east Europe grouping is used for descriptive percentages and standardised differences; regression models adjust for country. The country list is in analysis_code/README.md. Portugal is included in the grouping but is absent from the current primary sample.

These materials contain de-identified aggregate display data only and do not contain individual-level SHARE, CHARLS or KLoSA records.
Individual-level records are available only through the official cohort access procedures described in the manuscript.

Figure 1 source data:
- figure_1_conceptual_framework.csv records the nodes and directed edges used for Figure 1 Panel A.
- figure_1_sample_flow.csv records the participant-flow counts and exclusion notes used for Figure 1 Panel B.
- figure_1_operational_boundary.csv records variable construction, adjustment and weighting boundaries reported in Methods and supplementary material.

Figure 2 source data:
- figure_2_adjusted_distribution.csv, figure_2_primary_models.csv, figure_2_score_specification.csv and figure_2_attenuation.csv provide the plotted SHARE estimates and support values.
- figure_2_country_variability.csv, figure_2_country_specific.csv and figure_2_country_variability_summary.csv provide the ranked country-specific forest-plot display values.

Supplementary figure and table source data:
- supplementary_figure_s1_attrition.csv and supplementary_figure_s1_missingness.csv provide missingness and retained-sample summaries.
- supplementary_figure_s2_leave_one_country_out.csv, supplementary_figure_s3_subgroups.csv, supplementary_figure_s4_component_prevalence.csv, supplementary_figure_s4_components_joint.csv and supplementary_figure_s5_cross_cohort_context_checks.csv provide aggregate display data for supplementary figures.
- supplementary_variable_mapping.csv corresponds to Supplementary Table S1.
- share_barrier_models.csv provides the SHARE financial, structural/information and attitudinal barrier estimates used in Supplementary Table S8 and the main Table 2 contextual visiting and expenditure rows.
- share_all_four_exposure_components_sensitivity.csv provides the sensitivity analysis restricted to participants with all four exposure components observed.
- share_discordant_start_age_sensitivity.csv provides the reported childhood-care/start-age discordance sensitivity and the primary model for comparison. It contains aggregate coefficients, HC3 standard errors, confidence intervals, P values and sample counts, without participant identifiers.
- table_1_source.csv and table_2_source.csv provide aggregate data for the main manuscript tables. share_table1_full.csv provides the full descriptive summary in Supplementary Table S3, Panel A. Descriptive percentages and means (SD) use Wave 8 respondent weights and available cases; counts and data-availability percentages are unweighted. An em dash denotes an SMD that is not estimable because the pooled within-group variance is zero.

The CHARLS and KLoSA source data provide cohort-specific contextual visiting and expenditure analyses. These analyses use dental-access measures that differ from the SHARE life-course dental-care exposure. CHARLS models include Wave 2 respondents aged 45 years or older. High dental out-of-pocket expenditure is defined at the cohort-specific 75th percentile among strictly positive costs (600 RMB in CHARLS; 100 units of 10,000 Korean won in KLoSA), with zero and lower positive costs as the reference. The CHARLS and KLoSA loneliness variables are single CES-D items, not the SHARE three-item R-UCLA score; CESD-10 is the separate 10-item depression scale.

Aggregate numeric values retain the available analysis precision. Manuscript tables and figure labels display estimates rounded to three decimal places; for example, the KLoSA CESD-10 upper confidence limit is shown as 0.186.

Additional analysis data:
- share_age_threshold_sensitivity.csv: reported age65/75 SHARE model estimates.
- share_education_by_disadvantage.csv: education-by-disadvantage counts, weighted within-education proportions and weighted loneliness means.
- share_postponement_count_audit.csv: descriptive RH789 postponement counts in the low group, including recorded 0 and 999 values.
- share_component_observation_support.csv: three/four-observed-component support and never-regular-care counts.

The third score component is labelled late uptake or non-continuous regular care.

Scoring correction: continuity is adverse only with RH015=5 or RH018=5 and is zero only when both equal 1. Late/non-continuous care is zero only with observed early initiation and RH018=1, unless an adverse criterion applies; unknown values remain missing. The >=3-component sum and group thresholds are unchanged.
The source-response rule is incorporated into the primary scoring. The aggregate scoring files document score derivation and questionnaire-routing decisions.
The existing figure/table model and descriptive source CSVs can be regenerated by analysis_code/scripts/reproduce_source_data.py. The reported post hoc discordance sensitivity is regenerated separately by analysis_code/scripts/discordant_start_age_sensitivity.py; both scripts are included in scripts/run_all.py. External thresholds use unweighted positive-cost quartiles before complete-case filtering; CHARLS is first restricted to age >=45.

Structural-skip handling: RH015=5 with originally blank RH016 and RH018, and no contradictory observed responses, identifies childhood disadvantage as 1. The raw-empty flags are captured before negative codes are converted to missing; true DK/refusal/unknown values remain missing. share_structural_skip_correction_audit.csv records aggregate inclusion counts for this rule.
