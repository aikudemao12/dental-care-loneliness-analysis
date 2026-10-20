# Manuscript figures

From the repository root:

```sh
python -m pip install -r analysis_code/figures/requirements.txt
python analysis_code/figures/render_figures.py --source-data source_data --output outputs/Figures
```

The command renders Figure 2 and Figures S1–S5 from the aggregate CSV files. The layout modules define panels, labels and final spacing. All six canvases are 7.5 inches wide, with a minimum text size of 10 pt. Raster exports use 600 dpi. PDF and EPS/SVG exports retain vector elements. Arial is preferred, with Helvetica and DejaVu Sans fallbacks; font availability can affect text metrics. The submitted exports used Python 3.12 and Matplotlib 3.11.2.

Figure 1 is an editable diagram in `Figure_1_EJPH.drawio`. Open it in diagrams.net and export PDF or a 600 dpi image with the diagram bounds retained. Its flow counts are provided in `source_data/figure_1_sample_flow.csv` at repository root. The statistical renderer does not redraw this diagram.

Use `--figures` followed by figure stems to export a subset. Rendering uses the supplied aggregates and does not refit models.
