POOLED_HIGH = 0.1530039511839767

POOLED_HIGH_LCL = 0.0918401393521375

POOLED_HIGH_UCL = 0.2141677630158161

BETA_LABEL = r"$\it{\beta}$ coefficient"

COLORS = {
    "ink": "#1f2933",
    "muted": "#667480",
    "grid": "#dfe5ea",
    "zero": "#81909d",
    "low": "#5b9671",
    "mid": "#c9932d",
    "high": "#c24e6d",
    "teal": "#2d7f99",
    "neutral": "#8a96a3",
    "pale": "#f6f8fa",
}

COUNTRY_CODE = {
    "Austria": "AT",
    "Belgium": "BE",
    "Bulgaria": "BG",
    "Croatia": "HR",
    "Cyprus": "CY",
    "Czech Republic": "CZ",
    "Denmark": "DK",
    "Estonia": "EE",
    "Finland": "FI",
    "France": "FR",
    "Germany": "DE",
    "Greece": "GR",
    "Hungary": "HU",
    "Israel": "IL",
    "Italy": "IT",
    "Latvia": "LV",
    "Lithuania": "LT",
    "Luxembourg": "LU",
    "Malta": "MT",
    "Poland": "PL",
    "Romania": "RO",
    "Slovakia": "SK",
    "Slovenia": "SI",
    "Spain": "ES",
    "Sweden": "SE",
    "Switzerland": "CH",
}

def blend_with_white(color: str, white_fraction: float):
    rgb = mpl.colors.to_rgb(color)
    white_fraction = min(max(white_fraction, 0.0), 1.0)
    return tuple((1.0 - white_fraction) * channel + white_fraction for channel in rgb)

def clean_axis(ax) -> None:
    ax.tick_params(colors=COLORS["ink"], labelsize=7, length=3, width=0.8)
    ax.xaxis.label.set_color(COLORS["ink"])
    ax.yaxis.label.set_color(COLORS["ink"])
    ax.title.set_color(COLORS["ink"])

def draw_panel_letter(ax, letter: str, x: float = -0.075, y: float = 1.15) -> None:
    ax.text(x, y, letter, transform=ax.transAxes, fontsize=12, fontweight="bold", va="top", ha="left", color=COLORS["ink"])

def draw_panel_a(ax, dist: pd.DataFrame, support: pd.DataFrame) -> None:
    order = ["low_0_1", "mid_2", "high_3_4"]
    colors = [COLORS["low"], COLORS["mid"], COLORS["high"]]
    labels = ["Low\n0-1", "Mid\n2", "High\n3-4"]
    group_col = "disadvantage_group" if "disadvantage_group" in dist.columns else "life-course dental-care disadvantage group"
    support_col = "disadvantage_group" if "disadvantage_group" in support.columns else "life-course dental-care disadvantage group"
    vals = dist.set_index(group_col).loc[order]
    x = np.arange(len(order))
    means = vals["adjusted_mean_loneliness"].to_numpy()
    lows = vals["ci_low"].to_numpy()
    highs = vals["ci_high"].to_numpy()
    shares = vals["weighted_share_pct"].to_numpy()
    max_support = max(float(support["weighted_share_pct"].max()), 1.0)

    ax.set_title("Observed loneliness scores and standardised means", loc="left", fontsize=10, pad=8)
    for i, color in enumerate(colors):
        group_support = support.loc[support[support_col].eq(order[i])]
        for row in group_support.itertuples(index=False):
            width = 0.26 * float(row.weighted_share_pct) / max_support
            alpha = 0.13 + 0.18 * float(row.weighted_share_pct) / max_support
            ax.plot(
                [i - width, i + width],
                [row.loneliness_score, row.loneliness_score],
                color=blend_with_white(color, 1.0 - alpha),
                linewidth=5.0,
                solid_capstyle="round",
                zorder=1,
            )
        mean = means[i]
        ax.errorbar(
            i,
            mean,
            yerr=[[mean - lows[i]], [highs[i] - mean]],
            fmt="o",
            ms=6.5,
            color=color,
            ecolor=color,
            elinewidth=1.45,
            capsize=2.6,
            mec="white",
            mew=0.75,
            zorder=5,
        )
        ax.text(i, mean + 0.060, f"{mean:.3f}", ha="center", va="bottom", fontsize=7.5, color=COLORS["ink"],
                path_effects=[pe.withStroke(linewidth=1.4, foreground="white")])
    ax.plot(x, means, color="#77818a", linewidth=1.05, zorder=3)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    for i, share in enumerate(shares):
        ax.text(
            i,
            -0.36,
            f"{share:.1f}%; n = {int(vals.iloc[i]['n']):,}",
            transform=ax.get_xaxis_transform(),
            ha="center",
            va="top",
            fontsize=6.8,
            color=COLORS["muted"],
            clip_on=False,
        )
    ax.set_ylabel("Loneliness score", fontsize=9)
    ax.set_ylim(0.97, 3.06)
    ax.set_yticks([1.0, 1.5, 2.0, 2.5, 3.0])
    ax.set_xlim(-0.46, 2.46)
    ax.grid(axis="y", color=COLORS["grid"], linewidth=0.8)
    ax.text(0.98, 0.90, "Horizontal marks: weighted observed score support; point/whisker: adjusted mean and 95% CI",
            transform=ax.transAxes, ha="right", va="center", fontsize=7.2, color=COLORS["muted"])
    clean_axis(ax)

def draw_panel_b(ax, primary: pd.DataFrame) -> None:
    order = ["High vs low", "Mid vs low", "Per 1-point"]
    color_map = {"High vs low": COLORS["high"], "Mid vs low": COLORS["mid"], "Per 1-point": COLORS["teal"]}
    df = primary.set_index("short_label").loc[order]
    y = np.arange(len(order))[::-1]
    ax.set_title("Primary adjusted contrasts", loc="left", fontsize=10, pad=8)
    ax.axvline(0, color=COLORS["zero"], linestyle=(0, (3, 2)), linewidth=1)
    for yi, label in zip(y, order):
        row = df.loc[label]
        color = color_map[label]
        ax.errorbar(row["estimate"], yi, xerr=[[row["estimate"] - row["lcl"]], [row["ucl"] - row["estimate"]]],
                    fmt="D", color=color, ecolor=color, ms=7, capsize=3, elinewidth=1.5, mec="white", mew=0.6)
        ax.text(row["ucl"] + 0.010, yi, f"{row['estimate']:.3f}", va="center", fontsize=7.5, color=COLORS["ink"])
    ax.set_yticks(y)
    ax.set_yticklabels(order, fontsize=8)
    ax.set_xlabel(BETA_LABEL, fontsize=9)
    ax.set_xlim(-0.025, 0.285)
    ax.set_ylim(-0.4, len(order) - 0.6)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.8)
    clean_axis(ax)

def draw_panel_c(ax, score: pd.DataFrame) -> None:
    score = score.sort_values("score")
    x = score["score"].to_numpy()
    estimates = score["estimate"].to_numpy()
    lows = score["lcl"].to_numpy()
    highs = score["ucl"].to_numpy()
    share = score["weighted_share_pct"].to_numpy()
    ax.set_title("Score-specific adjusted contrasts", loc="left", fontsize=10, pad=8)
    ax.axhline(0, color=COLORS["zero"], linestyle=(0, (3, 2)), linewidth=1)
    ax.plot(x, estimates, color=blend_with_white(COLORS["teal"], 0.52), lw=0.95, zorder=2)
    for xi, estimate, low, high in zip(x, estimates, lows, highs):
        ax.plot([xi, xi], [low, high], color=COLORS["teal"], lw=1.25, zorder=2)
        ax.scatter([xi], [estimate], s=31, facecolor=COLORS["teal"], edgecolor="white", linewidth=0.55, zorder=3)
    ax.bar(x, share / share.max() * 0.024, bottom=-0.150, width=0.34, color="#d9ecf1", edgecolor="white", linewidth=0.25)
    ax.text(0.04, 0.08, "Pale bars show weighted score support; score 4 = 1.1%", transform=ax.transAxes,
            ha="left", va="bottom", fontsize=5.6, color=COLORS["muted"])
    ax.set_xlabel("Disadvantage score (reference = 0)", fontsize=9)
    ax.set_ylabel(BETA_LABEL, fontsize=9)
    ax.set_xticks([1, 2, 3, 4])
    ax.set_xlim(0.7, 4.3)
    ax.set_ylim(-0.16, 0.26)
    ax.grid(axis="y", color=COLORS["grid"], linewidth=0.8)
    clean_axis(ax)

def draw_panel_d(ax, atten: pd.DataFrame) -> None:
    rows = [
        ("Core", "current_sample_ladder", 0),
        ("+ education/health", "current_sample_ladder", 1),
        ("+ marital", "current_sample_ladder", 2),
        ("R6 bridge", "r6_proxy_ladder", 3),
        ("+ behaviour", "r6_proxy_ladder", 4),
        ("+ EURO-D", "r6_proxy_ladder", 5),
        ("+ prior loneliness", "r6_proxy_ladder", 6),
    ]
    y_positions = {label: len(rows) - 1 - idx for idx, (label, _, __) in enumerate(rows)}
    ax.set_title("Adjustment and specification ladder", loc="left", fontsize=10, pad=8)
    ax.axvline(0, color=COLORS["zero"], linestyle=(0, (3, 2)), linewidth=1)
    ax.axhspan(-0.5, 3.5, color=blend_with_white("#f9edf1", 0.32), zorder=0)
    ax.text(0.006, 3.35, "Wave 6 proxy subset", fontsize=7.1, color=COLORS["muted"], va="top")
    for _, row in atten.iterrows():
        if row["model_label"] not in y_positions:
            continue
        y = y_positions[row["model_label"]]
        color, marker, offset = (COLORS["mid"], "o", -0.10) if row["contrast"] == "Mid vs low" else (COLORS["high"], "D", 0.10)
        ax.errorbar(row["estimate"], y + offset, xerr=[[row["estimate"] - row["lcl"]], [row["ucl"] - row["estimate"]]],
                    fmt=marker, ms=5.5, color=color, ecolor=color, capsize=2, elinewidth=1.4, mec="white", mew=0.5, zorder=3)
    handles = [
        Line2D([0], [0], marker="o", color=COLORS["mid"], lw=1.2, markersize=4.8, label="Mid vs low"),
        Line2D([0], [0], marker="D", color=COLORS["high"], lw=1.2, markersize=4.8, label="High vs low"),
    ]
    ax.legend(handles=handles, loc="upper right", bbox_to_anchor=(1.0, 1.16), ncol=2, fontsize=7.1,
              handlelength=1.5, handletextpad=0.35, columnspacing=1.0, borderaxespad=0)
    ax.set_yticks([y_positions[row[0]] for row in rows])
    ax.set_yticklabels([row[0] for row in rows], fontsize=7.7)
    ax.set_xlabel(BETA_LABEL, fontsize=9)
    ax.set_xlim(-0.035, 0.285)
    ax.set_ylim(-0.55, len(rows) - 0.18)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.8)
    clean_axis(ax)

def draw_panel_e(ax, country: pd.DataFrame) -> None:
    ordered = country.sort_values("estimate").reset_index(drop=True)
    y = np.arange(len(ordered))
    ax.set_title("Country-specific high-vs-low estimates", loc="left", fontsize=10, pad=8)
    ax.axvspan(POOLED_HIGH_LCL, POOLED_HIGH_UCL, color=blend_with_white(COLORS["high"], 0.88), zorder=0)
    ax.axvline(POOLED_HIGH, color=COLORS["high"], linewidth=1.05, zorder=1)
    ax.axvline(0, color=COLORS["zero"], linestyle=(0, (3, 2)), linewidth=0.95, zorder=1)
    for idx in range(len(ordered)):
        if idx % 2 == 0:
            ax.axhspan(idx - 0.5, idx + 0.5, color=COLORS["pale"], zorder=0)
    for yi, row in zip(y, ordered.itertuples(index=False)):
        significant = bool(row.significant_positive)
        negative = row.estimate < 0
        color = COLORS["high"] if significant else (COLORS["teal"] if negative else "#d8b7bf")
        ax.plot([row.lcl, row.ucl], [yi, yi], color=(COLORS["high"] if significant else COLORS["neutral"]), lw=0.95, zorder=2)
        ax.scatter([row.estimate], [yi], s=30, facecolor=color, edgecolor=COLORS["ink"], linewidth=0.45, zorder=3)
    labels = [f"{COUNTRY_CODE.get(row.country_label, '')}  {row.country_label}" for row in ordered.itertuples(index=False)]
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=6.2)
    ax.invert_yaxis()
    ax.set_xlim(-0.32, 1.23)
    ax.set_xlabel("Country-specific high vs low " + BETA_LABEL, fontsize=8.6)
    ax.set_xticks([-0.25, 0.00, 0.25, 0.50, 0.75, 1.00, 1.20])
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.75)
    ax.text(0.99, 1.022, "25/26 estimates > 0; 9/26 CIs exclude 0", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=6.9, color=COLORS["muted"], clip_on=False)
    ax.text(POOLED_HIGH + 0.015, -0.82, f"pooled {POOLED_HIGH:.3f}", ha="left", va="center", fontsize=6.5, color=COLORS["high"])
    clean_axis(ax)

def draw_figure_2() -> None:
    dist = read_source_csv("figure_2_adjusted_distribution.csv")
    primary = read_source_csv("figure_2_primary_models.csv")
    score = read_source_csv("figure_2_score_specification.csv")
    atten = read_source_csv("figure_2_attenuation.csv")
    country = read_source_csv("figure_2_country_variability.csv")
    support = read_source_csv("figure_2_outcome_support_distribution.csv")

    fig = plt.figure(figsize=(7.45, 10.85), constrained_layout=False)
    gs = fig.add_gridspec(4, 2, height_ratios=[1.18, 0.98, 1.16, 4.65], width_ratios=[1.0, 1.08], hspace=0.68, wspace=0.48)
    ax_a = fig.add_subplot(gs[0, :])
    ax_b = fig.add_subplot(gs[1, 0])
    ax_c = fig.add_subplot(gs[1, 1])
    ax_d = fig.add_subplot(gs[2, :])
    ax_e = fig.add_subplot(gs[3, :])

    draw_panel_a(ax_a, dist, support)
    draw_panel_b(ax_b, primary)
    draw_panel_c(ax_c, score)
    draw_panel_d(ax_d, atten)
    draw_panel_e(ax_e, country)

    draw_panel_letter(ax_a, "A", x=-0.118, y=1.17)
    draw_panel_letter(ax_b, "B", x=-0.075, y=1.18)
    draw_panel_letter(ax_c, "C", x=-0.075, y=1.18)
    draw_panel_letter(ax_d, "D", x=-0.075, y=1.15)
    draw_panel_letter(ax_e, "E", x=-0.075, y=1.08)

    save_pub_figure(fig, FIG_DIR / "Figure_2_EJPH")
    plt.close(fig)
