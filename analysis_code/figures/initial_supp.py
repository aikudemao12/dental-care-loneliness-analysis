COLORS = {
    "ink": "#1f2933",
    "muted": "#667480",
    "grid": "#dfe5ea",
    "zero": "#87929c",
    "teal": "#2f8f86",
    "blue": "#1f5f8b",
    "violet": "#7465a5",
    "rose": "#bd4b4b",
    "ochre": "#bd8424",
    "other": "#aab3bb",
    "band": "#f0f3f5",
}

BETA_LABEL = r"$\it{\beta}$ coefficient"

BETA_LONELINESS_LABEL = r"$\it{\beta}$ coefficient for loneliness"

def clean_axis(ax) -> None:
    ax.tick_params(colors=COLORS["ink"], labelsize=7, length=3, width=0.75)
    ax.xaxis.label.set_color(COLORS["ink"])
    ax.yaxis.label.set_color(COLORS["ink"])
    ax.title.set_color(COLORS["ink"])

def panel_letter(ax, letter: str, x: float = -0.11, y: float = 1.09) -> None:
    ax.text(x, y, letter, transform=ax.transAxes, fontsize=10.5, fontweight="bold",
            ha="left", va="bottom", color=COLORS["ink"])

def label_with_stroke(ax, x, y, text, **kwargs) -> None:
    effects = kwargs.pop("path_effects", [pe.withStroke(linewidth=1.6, foreground="white")])
    ax.text(x, y, text, path_effects=effects, **kwargs)

def draw_supplementary_s1() -> None:
    miss = read_source_csv("supplementary_figure_s1_missingness.csv")
    attr = read_source_csv("supplementary_figure_s1_attrition.csv")

    label_map = {
        "disadv_childhood": "No regular childhood care",
        "disadvantage_group": "Dental-care disadvantage group",
        "disadvantage_score": "Dental-care disadvantage score",
        "disadv_late_uptake": "Late or absent uptake",
        "disadv_adult_pattern": "No stable adult regular care",
        "disadv_postponed": "Lifetime postponement",
        "r7lnlys3": "Wave 7 loneliness",
        "r8casp12": "Wave 8 CASP-12",
        "r8lnlys3": "Wave 8 loneliness",
        "r7casp12": "Wave 7 CASP-12",
        "current_smoker": "Current smoking",
        "drink_freq": "Recent drinking (past 7 days)",
        "bmi": "Body mass index",
        "chronic_burden": "Chronic disease burden",
        "married_partnered": "Married or partnered",
        "r7agey": "Age, years",
        "education_level": "Education level",
        "female": "Female",
        "r8wtresp": "Wave 8 respondent weight",
    }
    domain_colors = {
        "Exposure": COLORS["teal"],
        "Outcome": COLORS["violet"],
        "Covariate": COLORS["blue"],
        "Other": COLORS["other"],
    }
    miss = miss.assign(display_label=miss["variable"].map(label_map).fillna(miss["variable"]))
    miss = miss.sort_values("missing_pct_display", ascending=False).head(14).iloc[::-1].reset_index(drop=True)

    attr_label = {
        "Wave 7 CASP-12": "Wave 7 CASP-12",
        "Education level": "Education level",
        "BMI": "Body mass index",
        "Female": "Female",
        "Married or partnered": "Married or partnered",
        "Chronic burden": "Chronic disease burden",
        "Age, years": "Age, years",
    }
    attr = attr.dropna(subset=["standardized_difference"]).copy()
    attr["display_label"] = attr["variable"].map(attr_label).fillna(attr["variable"])
    attr = attr.sort_values("standardized_difference", ascending=False).reset_index(drop=True)

    fig = plt.figure(figsize=(7.25, 5.35), constrained_layout=False)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.06, 1.0], wspace=0.54)
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    fig.suptitle("Supplementary Fig. S1 | Missingness and attrition balance",
                 x=0.02, y=0.985, ha="left", fontsize=10.5, fontweight="bold", color=COLORS["ink"])

    y = np.arange(len(miss))
    ax_a.barh(
        y,
        miss["missing_pct_display"],
        color=[domain_colors[d] for d in miss["domain"]],
        height=0.67,
        edgecolor="white",
        linewidth=0.35,
    )
    for yi, val in zip(y, miss["missing_pct_display"]):
        ax_a.text(min(val + 1.3, 98.0), yi, f"{val:.1f}", ha="left", va="center", fontsize=7.1, color=COLORS["ink"])
    ax_a.set_yticks(y)
    ax_a.set_yticklabels(miss["display_label"], fontsize=7.3)
    ax_a.set_xlim(0, 100)
    ax_a.set_xlabel("Missing records, %", fontsize=8.3)
    ax_a.set_title("Largest missingness domains", loc="left", fontsize=9.4, pad=9)
    ax_a.grid(axis="x", color=COLORS["grid"], linewidth=0.75)
    ax_a.set_axisbelow(True)
    handles = [Line2D([0], [0], marker="s", linestyle="", markersize=5.6,
                      markerfacecolor=domain_colors[k], markeredgecolor=domain_colors[k], label=k)
               for k in ["Exposure", "Outcome", "Covariate", "Other"]]
    ax_a.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.0, -0.145), ncol=4,
                fontsize=7.0, handletextpad=0.35, columnspacing=0.95, borderaxespad=0)
    panel_letter(ax_a, "a", x=-0.08, y=1.055)
    clean_axis(ax_a)

    yb = np.arange(len(attr))
    for yi in yb:
        if yi % 2 == 1:
            ax_b.axhspan(yi - 0.5, yi + 0.5, color=COLORS["band"], zorder=0)
    bar_colors = [COLORS["rose"] if abs(v) >= 0.10 else COLORS["teal"] for v in attr["standardized_difference"]]
    ax_b.barh(yb, attr["standardized_difference"], color=bar_colors, height=0.62,
              edgecolor="white", linewidth=0.35, zorder=2)
    ax_b.axvline(0, color=COLORS["zero"], linewidth=0.95, zorder=1)
    ax_b.axvline(-0.10, color="#ce6f6f", linestyle=(0, (4, 2)), linewidth=0.95, zorder=1)
    ax_b.axvline(0.10, color="#ce6f6f", linestyle=(0, (4, 2)), linewidth=0.95, zorder=1)
    for yi, val in zip(yb, attr["standardized_difference"]):
        if val < 0:
            ax_b.text(val / 2, yi, f"{val:.3f}", ha="center", va="center", fontsize=6.7, color="white")
        else:
            ax_b.text(min(val + 0.008, 0.306), yi, f"{val:.3f}", ha="left", va="center", fontsize=7.0, color=COLORS["ink"])
    ax_b.set_yticks(yb)
    ax_b.set_yticklabels(attr["display_label"], fontsize=7.3)
    ax_b.invert_yaxis()
    ax_b.set_xlim(-0.155, 0.32)
    ax_b.set_xlabel("Standardised difference", fontsize=8.3)
    ax_b.set_title("Retained vs non-retained balance", loc="left", fontsize=9.4, pad=9)
    ax_b.grid(axis="x", color=COLORS["grid"], linewidth=0.75)
    ax_b.set_axisbelow(True)
    panel_letter(ax_b, "b", x=-0.08, y=1.055)
    clean_axis(ax_b)

    fig.text(0.985, 0.025, "Dashed lines mark |standardised difference| = 0.10",
             ha="right", va="bottom", fontsize=7.0, color=COLORS["muted"])
    fig.subplots_adjust(left=0.12, right=0.985, top=0.86, bottom=0.17)
    save_pub_figure(fig, FIG_DIR / "Supplementary_Figure_S1_EJPH", ["png", "tif", "pdf", "svg"])
    plt.close(fig)

def draw_supplementary_s3() -> None:
    df = read_source_csv("supplementary_figure_s3_subgroups.csv")
    row_order = ["Sex: male", "Sex: female", "Education: lower", "Education: higher"]
    row_labels = {
        "Sex: male": "Male",
        "Sex: female": "Female",
        "Education: lower": "Lower education",
        "Education: higher": "Higher education",
    }
    contrast_specs = [
        ("Mid vs low", COLORS["blue"], "a"),
        ("High vs low", COLORS["rose"], "b"),
    ]

    fig, axes = plt.subplots(1, 2, figsize=(7.25, 3.75), sharey=True)
    fig.suptitle("Supplementary Fig. S3 | Subgroup estimates",
                 x=0.02, y=0.985, ha="left", fontsize=10.5, fontweight="bold", color=COLORS["ink"])
    y = np.arange(len(row_order))
    for ax, (contrast, color, letter) in zip(axes, contrast_specs):
        sub = df[df["contrast"].eq(contrast)].set_index("row_label").loc[row_order].reset_index()
        for yi in y:
            if yi % 2 == 1:
                ax.axhspan(yi - 0.5, yi + 0.5, color=COLORS["band"], zorder=0)
        ax.axvline(0, color=COLORS["zero"], linewidth=0.95, zorder=1)
        for yi, row in zip(y, sub.itertuples(index=False)):
            ax.plot([row.ci_low, row.ci_high], [yi, yi], color=color, linewidth=1.45, zorder=2)
            ax.scatter([row.coef], [yi], s=36, facecolor=color, edgecolor="white", linewidth=0.6, zorder=3)
        ax.set_xlim(-0.035, 0.305)
        ax.set_ylim(len(row_order) - 0.4, -0.6)
        ax.set_title(contrast, loc="left", fontsize=9.4, pad=9)
        ax.set_xlabel(BETA_LONELINESS_LABEL, fontsize=8.2)
        ax.grid(axis="x", color=COLORS["grid"], linewidth=0.75)
        ax.set_axisbelow(True)
        panel_letter(ax, letter, x=-0.11, y=1.06)
        clean_axis(ax)
    first = df[df["contrast"].eq("Mid vs low")].set_index("row_label").loc[row_order].reset_index()
    axes[0].set_yticks(y)
    axes[0].set_yticklabels([f"{row_labels[r.row_label]}\nn = {int(r.n):,}" for r in first.itertuples(index=False)],
                            fontsize=7.2)
    axes[1].tick_params(axis="y", labelleft=False)
    fig.subplots_adjust(left=0.17, right=0.985, top=0.80, bottom=0.18, wspace=0.20)
    save_pub_figure(fig, FIG_DIR / "Supplementary_Figure_S3_EJPH", ["png", "tif", "pdf", "svg"])
    plt.close(fig)

def draw_forest_on_shared_rows(ax, df, color, xlim, title, letter, label_mode: str) -> None:
    y = np.arange(len(df))
    for yi in y:
        if yi % 2 == 1:
            ax.axhspan(yi - 0.5, yi + 0.5, color=COLORS["band"], zorder=0)
    ax.axvline(0, color=COLORS["zero"], linewidth=0.95, zorder=1)
    for yi, row in zip(y, df.itertuples(index=False)):
        ax.plot([row.lcl, row.ucl], [yi, yi], color=color, linewidth=1.45, zorder=2)
        ax.scatter([row.estimate], [yi], s=36, facecolor=color, edgecolor="white", linewidth=0.6, zorder=3)
        x_text = xlim[1] - 0.030 * (xlim[1] - xlim[0])
        label_with_stroke(ax, x_text, yi, f"{row.estimate:.3f}", ha="right", va="center", fontsize=6.8, color=COLORS["ink"])
    ax.set_xlim(*xlim)
    ax.set_ylim(len(df) - 0.4, -0.6)
    ax.set_title(title, loc="left", fontsize=9.4, pad=9)
    ax.set_xlabel(BETA_LABEL, fontsize=8.2)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.75)
    ax.set_axisbelow(True)
    panel_letter(ax, letter, x=-0.10, y=1.06)
    clean_axis(ax)

def draw_supplementary_s4() -> None:
    comp = read_source_csv("supplementary_figure_s4_components_joint.csv")
    prev = component_prevalence()
    order = prev.sort_values("sort_order")["display_label"].tolist()
    y = np.arange(len(order))

    fig = plt.figure(figsize=(7.25, 4.35), constrained_layout=False)
    gs = fig.add_gridspec(1, 3, width_ratios=[1.08, 1.0, 1.0], wspace=0.60)
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1], sharey=ax_a)
    ax_c = fig.add_subplot(gs[0, 2], sharey=ax_a)
    fig.suptitle("Supplementary Fig. S4 | Joint component estimates",
                 x=0.02, y=0.985, ha="left", fontsize=10.5, fontweight="bold", color=COLORS["ink"])

    p = prev.set_index("display_label").loc[order].reset_index()
    ax_a.barh(y, p["weighted_prevalence_pct"], color="#c7deee", edgecolor=COLORS["blue"],
              linewidth=0.85, height=0.58, zorder=2)
    for yi, val in zip(y, p["weighted_prevalence_pct"]):
        ax_a.text(min(val + 1.2, 58.0), yi, f"{val:.1f}", ha="left", va="center", fontsize=7.0, color=COLORS["ink"])
    ax_a.set_yticks(y)
    ax_a.set_yticklabels(order, fontsize=7.2)
    ax_a.set_xlim(0, 60)
    ax_a.set_ylim(len(order) - 0.4, -0.6)
    ax_a.set_xlabel("Weighted prevalence, %", fontsize=8.2)
    ax_a.set_title("Component prevalence", loc="left", fontsize=9.4, pad=9)
    ax_a.grid(axis="x", color=COLORS["grid"], linewidth=0.75)
    ax_a.set_axisbelow(True)
    panel_letter(ax_a, "a", x=-0.08, y=1.06)
    clean_axis(ax_a)

    lon = comp[comp["outcome_label"].eq("Loneliness")].set_index("display_label").loc[order].reset_index()
    casp = comp[comp["outcome_label"].eq("CASP-12")].set_index("display_label").loc[order].reset_index()
    draw_forest_on_shared_rows(ax_b, lon, COLORS["rose"], (-0.065, 0.140), "Joint model: loneliness", "b", "small")
    draw_forest_on_shared_rows(ax_c, casp, COLORS["ochre"], (-1.85, 1.35), "Joint model: CASP-12", "c", "large")
    ax_b.tick_params(axis="y", labelleft=False)
    ax_c.tick_params(axis="y", labelleft=False)
    fig.text(0.985, 0.035, "Outcome scales differ; panels b and c should not be compared by magnitude.",
             ha="right", va="bottom", fontsize=7.0, color=COLORS["muted"])
    fig.subplots_adjust(left=0.18, right=0.985, top=0.80, bottom=0.18)
    save_pub_figure(fig, FIG_DIR / "Supplementary_Figure_S4_EJPH", ["png", "tif", "pdf", "svg"])
    plt.close(fig)

def draw_supplementary_s5() -> None:
    df = read_source_csv("supplementary_figure_s5_external_full.csv")
    panels = [
        ("CHARLS", "Loneliness", "CHARLS: loneliness", "a", (-0.10, 0.78)),
        ("CHARLS", "CESD-10", "CHARLS: depressive symptoms", "b", (-1.35, 2.55)),
        ("KLoSA", "Loneliness", "KLoSA: loneliness", "c", (-0.10, 0.78)),
        ("KLoSA", "CESD-10", "KLoSA: depressive symptoms", "d", (-1.35, 2.55)),
    ]
    exposure_order = ["High OOP burden", "No dental visit"]
    exposure_colors = {"High OOP burden": COLORS["rose"], "No dental visit": COLORS["blue"]}
    y_lookup = {"High OOP burden": 1, "No dental visit": 0}

    fig, axes = plt.subplots(2, 2, figsize=(7.25, 5.15), constrained_layout=False)
    fig.suptitle("Supplementary Fig. S5 | External affordability-context checks",
                 x=0.02, y=0.985, ha="left", fontsize=10.5, fontweight="bold", color=COLORS["ink"])
    for ax, (dataset, outcome, title, letter, xlim) in zip(axes.ravel(), panels):
        sub = df[df["dataset"].eq(dataset) & df["outcome_label"].eq(outcome)].copy()
        ax.axvline(0, color=COLORS["zero"], linewidth=0.95, zorder=1)
        for label in exposure_order:
            row = sub[sub["display_label"].eq(label)].iloc[0]
            y = y_lookup[label]
            color = exposure_colors[label]
            ax.plot([row["lcl"], row["ucl"]], [y, y], color=color, linewidth=1.55, zorder=2)
            ax.scatter([row["estimate"]], [y], s=38, facecolor=color, edgecolor="white", linewidth=0.6, zorder=3)
            label_with_stroke(
                ax,
                xlim[1] - 0.028 * (xlim[1] - xlim[0]),
                y,
                f"{row['estimate']:.3f}",
                ha="right",
                va="center",
                fontsize=6.9,
                color=COLORS["ink"],
            )
        ax.set_xlim(*xlim)
        ax.set_ylim(-0.1, 1.1)
        ax.set_yticks([1, 0])
        ax.set_yticklabels(exposure_order, fontsize=7.3)
        ax.set_title(title, loc="left", fontsize=9.4, pad=9)
        ax.set_xlabel(BETA_LABEL, fontsize=8.2)
        ax.grid(axis="x", color=COLORS["grid"], linewidth=0.75)
        ax.set_axisbelow(True)
        panel_letter(ax, letter, x=-0.10, y=1.06)
        clean_axis(ax)
    fig.subplots_adjust(left=0.15, right=0.985, top=0.84, bottom=0.12, hspace=0.55, wspace=0.42)
    save_pub_figure(fig, FIG_DIR / "Supplementary_Figure_S5_EJPH", ["png", "tif", "pdf", "svg"])
    plt.close(fig)
