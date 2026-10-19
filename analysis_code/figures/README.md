# Manuscript figures

`render_figures.py` renders Figure 1, Figure 2 and Supplementary Figures S1–S5 from the aggregate source tables. It retains the initial-submission panel arrangements and image dimensions, using corrected data and the revised display terminology.

From the repository root:

```sh
python -m pip install -r analysis_code/figures/requirements.txt
python analysis_code/figures/render_figures.py --source-data source_data --output outputs/Figures --qa outputs/figure_qa
```

The `initial_*.py` files supply the historical drawing functions and are loaded by the renderer. Run the renderer, rather than those layout fragments. The renderer reads the current aggregate tables and updates numerical annotations, including the pooled coefficient, score support and fixed Wave 6 sample size.

`initial_f1_geometry.json` preserves the author's original vector paths and editable text geometry. `initial_plot_geometry.json` preserves the original plot-area positions. Neither file contains participant records. `component_prevalence_denominators.json` supplies the independently checked aggregate denominators for the available-case component prevalence labels and verifies their association with the source table through its SHA256 digest.

Main figures are exported as PDF, EPS, PNG and TIFF; supplementary figures as PDF, SVG, PNG and TIFF. PNG and TIFF files use 600 dpi. Arial is used when available, followed by Helvetica and DejaVu Sans. A different installed font may change text metrics.

Optional `--alignment-tools PATH` enables the external `audit_panel_alignment.py` validator when available. The `--figures` option accepts one or more full figure stems to render a subset. The supplied aggregate tables remain authoritative for estimates and confidence intervals; this renderer does not refit statistical models.
