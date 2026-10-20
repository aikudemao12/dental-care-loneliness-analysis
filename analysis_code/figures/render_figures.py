"""Render Figure 2 and Supplementary Figures S1–S5 from aggregate data."""
from pathlib import Path
import argparse
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image
import plot_core as core
from final_layout import edit

JOBS = [
    ("Figure_2_EJPH", "layout_f2.py", "draw_figure_2"),
    ("Supplementary_Figure_S1_EJPH", "layout_supp.py", "draw_supplementary_s1"),
    ("Supplementary_Figure_S2_EJPH", "layout_s2.py", "draw_supplementary_s2"),
    ("Supplementary_Figure_S3_EJPH", "layout_supp.py", "draw_supplementary_s3"),
    ("Supplementary_Figure_S4_EJPH", "layout_supp.py", "draw_supplementary_s4"),
    ("Supplementary_Figure_S5_EJPH", "layout_supp.py", "draw_supplementary_s5"),
]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--figures", nargs="*")
    args = parser.parse_args()
    core.SOURCE, core.OUTPUT = args.source_data, args.output
    args.output.mkdir(parents=True, exist_ok=True)
    close = plt.close
    plt.close = lambda *a, **k: None
    try:
        for name, module, function in JOBS:
            if args.figures and name not in args.figures:
                continue
            core.ACTIVE.clear()
            core.style()
            env = core.load_module(module)
            if name == "Figure_2_EJPH":
                row = core.read_csv("figure_2_primary_models.csv").set_index("short_label").loc["High vs low"]
                env.update(POOLED_HIGH=float(row.estimate), POOLED_HIGH_LCL=float(row.lcl), POOLED_HIGH_UCL=float(row.ucl))
            env[function]()
            fig = core.FIGURES[name]
            core.refine(fig, name)
            before = core.numeric_artists(fig)
            edit(fig, name)
            assert core.numeric_artists(fig) == before
            core.interval_checks(fig, name)
            fig.savefig(args.output / (name + ".pdf"), metadata={"Title": name, "Creator": "", "Producer": ""})
            fig.savefig(args.output / (name + ".png"), dpi=600, metadata={"Software": ""})
            with Image.open(args.output / (name + ".png")) as image:
                image.convert("RGB").save(args.output / (name + ".tif"), compression="tiff_lzw", dpi=(600, 600))
            if name.startswith("Figure_2"):
                fig.savefig(args.output / (name + ".eps"), metadata={"Creator": "Manuscript figure"})
            else:
                fig.savefig(args.output / (name + ".svg"), metadata={"Creator": "", "Date": None})
            close(fig)
            print(name)
    finally:
        plt.close = close

if __name__ == "__main__":
    main()
