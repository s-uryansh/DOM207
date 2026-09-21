import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .config import COLORS, DAY_ORDER, FIGURES, TIME_ORDER


def boxplot_outlier_count(values):
    q1, q3 = values.quantile([.25, .75])
    iqr = q3 - q1
    return int(((values < q1 - 1.5 * iqr) | (values > q3 + 1.5 * iqr)).sum())


def relative_luminance(rgb):
    channels = [value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4 for value in rgb]
    return .2126 * channels[0] + .7152 * channels[1] + .0722 * channels[2]


def annotate_sample_sizes(axis, groups):
    for position, values in enumerate(groups, 1):
        axis.annotate(f"n={len(values)}", (position, 1.01), xycoords=("data", "axes fraction"), ha="center", va="bottom", color="#202020", fontsize=9, clip_on=False)


def create_figures(base, party, day_time):
    plt.style.use("default")
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.titleweight": "bold",
        "text.color": "#202020",
        "axes.labelcolor": "#202020",
        "axes.edgecolor": "#202020",
        "xtick.color": "#202020",
        "ytick.color": "#202020",
    })

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    box_style = {
        "patch_artist": True,
        "boxprops": {"facecolor": COLORS["blue"], "edgecolor": "#202020", "alpha": .68},
        "medianprops": {"color": "#202020", "linewidth": 1.5},
        "whiskerprops": {"color": "#202020"},
        "capprops": {"color": "#202020"},
    }
    day_values = [base.loc[base["Day"].eq(day), "Amount"].dropna() for day in DAY_ORDER]
    axes[0].boxplot(day_values, tick_labels=DAY_ORDER, showfliers=False, **box_style)
    axes[0].set(xlabel="Day", ylabel="Bill amount")
    axes[0].set_title("Bill amount by day (pooled)", pad=32)
    axes[0].grid(axis="y", color="#d0d0d0", linewidth=.6)
    annotate_sample_sizes(axes[0], day_values)

    time_values = [base.loc[base["Time"].eq(period), "Amount"].dropna() for period in TIME_ORDER]
    time_style = {**box_style, "boxprops": {"facecolor": COLORS["teal"], "edgecolor": "#202020", "alpha": .7}}
    axes[1].boxplot(time_values, tick_labels=TIME_ORDER, showfliers=False, **time_style)
    axes[1].set(xlabel="Service period", ylabel="Bill amount")
    axes[1].set_title("Bill amount by service period", pad=32)
    axes[1].grid(axis="y", color="#d0d0d0", linewidth=.6)
    annotate_sample_sizes(axes[1], time_values)
    fig.tight_layout(rect=(0, 0, 1, .88))
    fig.savefig(FIGURES / "bill_distributions.png", dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    medians = day_time.pivot(index="Day", columns="Time", values="BillMedian").reindex(index=DAY_ORDER, columns=TIME_ORDER).astype(float)
    counts = day_time.pivot(index="Day", columns="Time", values="Transactions").reindex(index=DAY_ORDER, columns=TIME_ORDER).astype(float)
    fig, ax = plt.subplots(figsize=(8, 4.5), constrained_layout=True)
    cmap = plt.get_cmap("Blues")
    norm = plt.Normalize(np.nanmin(medians.to_numpy()), np.nanmax(medians.to_numpy()))
    image = ax.imshow(medians, cmap=cmap, norm=norm, aspect="auto")
    for row in range(len(DAY_ORDER)):
        for column in range(len(TIME_ORDER)):
            value = medians.iloc[row, column]
            label = "No data" if pd.isna(value) else f"Median {value:.2f}\nn={int(counts.iloc[row, column])}"
            luminance = relative_luminance(cmap(norm(value))[:3]) if pd.notna(value) else 1
            black_contrast = (luminance + .05) / .05
            white_contrast = 1.05 / (luminance + .05)
            text_color = "#000000" if black_contrast >= white_contrast else "#ffffff"
            assert max(black_contrast, white_contrast) >= 4.5
            ax.text(column, row, label, ha="center", va="center", color=text_color, fontweight="bold")
    ax.set_xticks(range(len(TIME_ORDER)), TIME_ORDER)
    ax.set_yticks(range(len(DAY_ORDER)), DAY_ORDER)
    ax.set(title="Day x service-period bill matrix", xlabel="Service period", ylabel="Day")
    colorbar = fig.colorbar(image, ax=ax, label="Median bill amount")
    colorbar.ax.tick_params(colors="#202020")
    fig.savefig(FIGURES / "segment_matrix.png", dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    fig, ax1 = plt.subplots(figsize=(8.5, 4.9))
    x = party.index.astype(int).to_numpy()
    bars = ax1.bar(x, party["Transactions"], color=COLORS["blue"], alpha=.78, label="Transactions")
    ax1.set(xlabel="Party size", ylabel="Transactions", title="Party mix and median per-head spend")
    ax1.set_xticks(x)
    ax1.set_ylim(0, party["Transactions"].max() * 1.16)
    ax1.grid(axis="y", color="#d0d0d0", linewidth=.6)
    for bar, count in zip(bars, party["Transactions"].astype(int)):
        ax1.annotate(f"n={count}", (bar.get_x() + bar.get_width() / 2, bar.get_height()), xytext=(0, 4), textcoords="offset points", ha="center", va="bottom", color="#202020", fontsize=9)
    ax2 = ax1.twinx()
    line = ax2.plot(x, party["PerHeadMedian"], color=COLORS["gold"], marker="o", linewidth=2.5, label="Median per-head spend")[0]
    ax2.set_ylabel("Median bill per head")
    ax2.set_ylim(0, max(10, party["PerHeadMedian"].max() * 1.12))
    ax1.legend([bars, line], ["Transactions", "Median per-head spend"], loc="upper center", bbox_to_anchor=(.5, -.16), ncol=2, frameon=False, labelcolor="#202020")
    fig.tight_layout(rect=(0, .08, 1, 1))
    fig.savefig(FIGURES / "party_opportunity.png", dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    tip_base = base[~base["TipEntryError"]].copy()
    tip_base["TrendBin"] = pd.qcut(tip_base["Amount"], 8, duplicates="drop")
    trend = tip_base.groupby("TrendBin", observed=True).agg(Amount=("Amount", "median"), TipRatePct=("TipRatePct", "median"))
    above_cap = tip_base[tip_base["TipRatePct"] > 30].copy()
    fig, ax = plt.subplots(figsize=(8.5, 4.8), constrained_layout=True)
    ax.scatter(tip_base["Amount"], tip_base["TipRatePct"], s=23, alpha=.5, color=COLORS["teal"], edgecolors="none")
    ax.plot(trend["Amount"], trend["TipRatePct"], color=COLORS["red"], marker="o", linewidth=2.8, label="8-bin median (descriptive only)")
    ax.set_xscale("log")
    ax.set_ylim(0, 30)
    ax.set(title="Tip rate and bill amount", xlabel="Bill amount (log scale)", ylabel="Tip rate (%)")
    ax.grid(color="#d0d0d0", linewidth=.6, which="both")
    ax.legend(frameon=False, labelcolor="#202020")
    fig.savefig(FIGURES / "amount_tip_relationship.png", dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    rates = ", ".join(str(int(np.floor(value + .5))) for value in above_cap["TipRatePct"].sort_values())
    return pd.DataFrame([
        ("Figure 1 day panel", sum(boxplot_outlier_count(values) for values in day_values), "Outliers hidden using the 1.5 x IQR plotting rule; observations remain in tests"),
        ("Figure 1 service-period panel", sum(boxplot_outlier_count(values) for values in time_values), "Outliers hidden using the 1.5 x IQR plotting rule; observations remain in tests"),
        ("Figure 1 pooled day base", int(base["Day"].notna().sum()), "All analysis-ready rows with valid Day"),
        ("Figure 2 stratified base", int(base[["Day", "Time"]].notna().all(axis=1).sum()), "Analysis-ready rows with valid Day and Time"),
        ("Figure 4 probable errors removed", int(base["TipEntryError"].sum()), "Probable tip-entry errors removed"),
        ("Figure 4 rates above 30% cap", len(above_cap), f"Rounded rates: {rates}%"),
    ], columns=["Figure", "Records", "Disclosure"])
