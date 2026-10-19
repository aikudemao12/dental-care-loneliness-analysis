COLORS = {
    "ink": "#1f2933",
    "muted": "#667480",
    "grid": "#dfe5ea",
    "zero": "#81909d",
    "low": "#5b9671",
    "mid": "#c9932d",
    "high": "#c24e6d",
    "teal": "#2d7f99",
    "country": "#9aa5ad",
    "land": "#e8e8e8",
    "border": "#cfd7dc",
    "sea": "#fcfdfe",
}

BETA_LABEL = r"$\it{\beta}$ coefficient"

def clean_axis(ax):
    ax.tick_params(colors=COLORS["ink"], labelsize=7, length=3, width=0.8)
    ax.xaxis.label.set_color(COLORS["ink"])
    ax.yaxis.label.set_color(COLORS["ink"])
    ax.title.set_color(COLORS["ink"])

def draw_supplementary_s2():
    loo = read_source_csv("supplementary_figure_s2_leave_one_country_out.csv")
    contrasts = [("Mid vs low", COLORS["teal"], "a", "Mid disadvantage vs low"), ("High vs low", COLORS["high"], "b", "High disadvantage vs low")]
    fig, axes = plt.subplots(1, 2, figsize=(7.25, 5.9), sharey=False)
    fig.suptitle("Supplementary Fig. S2 | Leave-one-country-out influence", x=0.02, y=0.985, ha="left", fontsize=10.5, fontweight="bold")
    for ax, (contrast, color, letter, title) in zip(axes, contrasts):
        df = loo[loo["contrast"] == contrast].copy()
        df["abs_delta"] = df["delta_from_pooled"].abs()
        df = df.sort_values("delta_from_pooled").reset_index(drop=True)
        y = np.arange(len(df))
        pooled = float(df["pooled_reference"].iloc[0])
        ax.axvline(0, color="#a9b1b8", linewidth=0.85)
        ax.axvline(pooled, color=color, linestyle=(0, (4, 2)), linewidth=1.2)
        for idx in range(len(df)):
            if idx % 2 == 0:
                ax.axhspan(idx - 0.5, idx + 0.5, color="#f1f4f6", zorder=0)
        max_idx = int(df["abs_delta"].idxmax())
        for yi, row in df.iterrows():
            is_max = yi == max_idx
            ax.plot([row["ci_low"], row["ci_high"]], [yi, yi], color=(color if is_max else "#8e99a3"), lw=(1.35 if is_max else 0.85), zorder=2)
            ax.scatter([row["coef"]], [yi], s=(23 if is_max else 15), facecolor=color, edgecolor="white", linewidth=0.45, zorder=3)
        labels = []
        for yi, row in df.iterrows():
            labels.append(row["omitted_country_label"] + (" *" if yi == max_idx else ""))
        ax.set_yticks(y)
        ax.set_yticklabels(labels, fontsize=6.6)
        ax.invert_yaxis()
        ax.set_title(title, loc="left", fontsize=9.3, pad=10)
        ax.text(-0.11, 1.065, letter, transform=ax.transAxes, fontsize=9.5, fontweight="bold", ha="left", va="bottom")
        delta = df.loc[max_idx, "delta_from_pooled"]
        country = df.loc[max_idx, "omitted_country_label"]
        ax.text(0.98, 0.035, f"largest |delta|: {country} {delta:+.3f}", transform=ax.transAxes,
                ha="right", va="bottom", fontsize=6.4, color=COLORS["muted"])
        ax.text(pooled + 0.004, -0.80, f"pooled {pooled:.3f}", color=color, fontsize=6.6, ha="left", va="center")
        ax.grid(axis="x", color=COLORS["grid"], lw=0.75)
        ax.set_xlabel(BETA_LABEL, fontsize=8.5)
        if contrast == "Mid vs low":
            ax.set_xlim(-0.02, 0.105)
        else:
            ax.set_xlim(0.075, 0.235)
        ax.set_ylim(len(df) - 0.4, -1.05)
        clean_axis(ax)
    fig.subplots_adjust(left=0.14, right=0.98, top=0.88, bottom=0.08, wspace=0.34)
    out = FIG_DIR / "Supplementary_Figure_S2_EJPH"
    save_pub_figure(fig, out, ["png", "tif", "pdf", "svg"])
    plt.close(fig)
