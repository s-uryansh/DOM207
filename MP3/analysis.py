from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import dendrogram, fcluster, linkage
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score, silhouette_samples, silhouette_score
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "dataset" / "ICTIndiv.xlsx"
FIGURES_DIR = ROOT / "Report" / "figures"
RANDOM_STATE = 42
CLUSTER_COUNT = 2
ISSUES = ["FC", "JI", "SE", "WS", "WO", "WH", "WE", "TI", "TA"]
SCORE_A = [f"{issue}_FSMean" for issue in ISSUES]
SCORE_B = [f"{issue}_Smean" for issue in ISSUES]
REGIONS = {
    "EastAsia": ["China", "Japan", "South Korea", "Taiwan"],
    "SEAsia": ["Malaysia", "Thailand", "Vietnam"],
    "SouthAsia": ["Bangladesh", "India", "Pakistan"],
    "MidEast": ["Iran", "Jordan", "Turkey"],
    "EastEU": ["Hungary", "Lithuania", "Macedonia", "Poland", "Romania", "Russia"],
    "WestEU": ["Finland", "France", "Germany", "Greece", "Italy", "Portugal", "UK"],
    "N America": ["Canada", "USA"],
    "LatAm": ["Argentina", "Brazil", "Mexico", "Peru"],
    "Africa": ["Egypt", "Ghana", "Nigeria", "South Africa"],
    "Oceania": ["New Zealand"],
}


def save_dendrograms(countries, feature_sets):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    for name, values in feature_sets.items():
        tree = linkage(values, method="ward")
        fig, ax = plt.subplots(figsize=(14, 7))
        dendrogram(
            tree,
            labels=countries,
            orientation="right",
            leaf_font_size=7,
            color_threshold=0,
            above_threshold_color="#222222",
            ax=ax,
        )
        cut_height = np.nextafter(tree[-1, 2], 0)
        ax.axvline(
            cut_height,
            color="#555555",
            linestyle="--",
            linewidth=1.1,
            label="k=2 cut",
        )
        ax.set_title(f"Ward Dendrogram — Score {name}", fontsize=12)
        ax.set_xlabel("Ward linkage distance", fontsize=9)
        ax.set_ylabel("Country", fontsize=9)
        ax.tick_params(axis="y", labelsize=7)
        ax.tick_params(axis="x", labelsize=8)
        ax.legend(loc="lower right", frameon=False, fontsize=8)
        fig.subplots_adjust(left=0.22, right=0.98, top=0.92, bottom=0.12)
        fig.savefig(FIGURES_DIR / f"dend_{name}.png", dpi=300, bbox_inches="tight")
        plt.close(fig)


def fit_cluster_methods(values, n_clusters):
    kmeans = KMeans(
        n_clusters=n_clusters,
        random_state=RANDOM_STATE,
        n_init=10,
    ).fit(values)
    ward = fcluster(linkage(values, method="ward"), t=n_clusters, criterion="maxclust") - 1
    average = AgglomerativeClustering(
        n_clusters=n_clusters,
        linkage="average",
    ).fit_predict(values)
    return {
        "kmeans": kmeans.labels_,
        "ward": ward,
        "average": average,
    }


def print_cluster_means(data, labels, columns, title):
    print(title)
    first = data.loc[labels == 0, columns].mean().round(3)
    second = data.loc[labels == 1, columns].mean().round(3)
    print(
        "  "
        + ", ".join(
            f"{column}: {first[column]:.3f}/{second[column]:.3f}/"
            f"{first[column] - second[column]:.3f}"
            for column in columns
        )
    )


def leave_one_out_stability(data, columns, baseline_labels):
    scores = []

    for idx in range(len(data)):
        subset = data.drop(data.index[idx])
        values = StandardScaler().fit_transform(subset[columns].to_numpy(float))
        labels = KMeans(
            n_clusters=CLUSTER_COUNT,
            random_state=RANDOM_STATE,
            n_init=10,
        ).fit_predict(values)
        scores.append(
            (data.iloc[idx]["Country"], adjusted_rand_score(baseline_labels[np.arange(len(data)) != idx], labels))
        )

    scores.sort(key=lambda item: item[1])
    values = [score for _, score in scores]
    print(
        f"Leave-one-country-out ARI: min={min(values):.3f}, "
        f"median={np.median(values):.3f}, max={max(values):.3f}"
    )
    print("Lowest stability exclusions: " + ", ".join(
        f"{country}={score:.3f}" for country, score in scores[:5]
    ))


def main():
    data = pd.read_excel(DATA_PATH)
    countries = data["Country"].tolist()

    print(
        "A vs B corr:",
        ", ".join(
            f"{issue}={data[f'{issue}_FSMean'].corr(data[f'{issue}_Smean']):.4f}"
            for issue in ISSUES
        ),
    )
    print(
        f"Unused: Code (ID 1-46), Num "
        f"(sample size {data['Num'].min()}-{data['Num'].max()})"
    )

    score_a = StandardScaler().fit_transform(data[SCORE_A].to_numpy(float))
    score_b = StandardScaler().fit_transform(data[SCORE_B].to_numpy(float))
    score_both = StandardScaler().fit_transform(np.hstack([score_a, score_b]))
    feature_sets = {"A": score_a, "B": score_b, "Both": score_both}

    for name, values in {"A": score_a, "B": score_b}.items():
        z_scores = np.abs((values - values.mean(0)) / values.std(0))
        print(f"Outliers |z|>3 {name}: {int((z_scores > 3).sum())} retained")

    for name, values in feature_sets.items():
        pca = PCA(random_state=RANDOM_STATE).fit(values)
        cumulative = np.cumsum(pca.explained_variance_ratio_)
        components_80 = int(np.searchsorted(cumulative, 0.80) + 1)
        ratios = pca.explained_variance_ratio_
        print(
            f"PCA {name}: PC1={ratios[0]:.3f}, PC2={ratios[1]:.3f}, "
            f"PC3={ratios[2]:.3f}, 80% at {components_80}"
        )

    corr_a = np.abs(np.corrcoef(score_a, rowvar=False) - np.eye(len(SCORE_A))).max()
    corr_b = np.abs(np.corrcoef(score_b, rowvar=False) - np.eye(len(SCORE_B))).max()
    print(f"Max off-diag corr A: {corr_a:.3f}")
    print(f"Max off-diag corr B: {corr_b:.3f}")

    print("Silhouette k=2..6:")
    for name, values in feature_sets.items():
        scores = [
            silhouette_score(
                values,
                KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10).fit_predict(values),
            )
            for k in range(2, 7)
        ]
        print("  " + name + ": " + " ".join(
            f"k={k}:{score:.3f}" for k, score in zip(range(2, 7), scores)
        ))

    print("Elbow inertia k=2..8:")
    for name, values in feature_sets.items():
        inertia = [
            KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10).fit(values).inertia_
            for k in range(2, 9)
        ]
        print("  " + name + ": " + " ".join(
            f"k={k}:{value:.1f}" for k, value in zip(range(2, 9), inertia)
        ))

    save_dendrograms(countries, feature_sets)

    clusterings = {
        name: fit_cluster_methods(values, CLUSTER_COUNT)
        for name, values in feature_sets.items()
    }
    print("Cross-method ARI k=2 (hierarchical vs kmeans):")
    for name, result in clusterings.items():
        ward_ari = adjusted_rand_score(result["ward"], result["kmeans"])
        avg_ari = adjusted_rand_score(result["average"], result["kmeans"])
        print(f"  {name}: ward={ward_ari:.3f}, average={avg_ari:.3f}")

    print("Cross-score ARI k-means:")
    for n_clusters in [2, 3, 4]:
        labels_a = KMeans(
            n_clusters=n_clusters,
            random_state=RANDOM_STATE,
            n_init=10,
        ).fit_predict(score_a)
        labels_b = KMeans(
            n_clusters=n_clusters,
            random_state=RANDOM_STATE,
            n_init=10,
        ).fit_predict(score_b)
        labels_both = KMeans(
            n_clusters=n_clusters,
            random_state=RANDOM_STATE,
            n_init=10,
        ).fit_predict(score_both)
        print(
            f"  k={n_clusters}: A-B={adjusted_rand_score(labels_a, labels_b):.3f}, "
            f"A-Both={adjusted_rand_score(labels_a, labels_both):.3f}, "
            f"B-Both={adjusted_rand_score(labels_b, labels_both):.3f}"
        )

    labels = clusterings["Both"]["kmeans"]
    silhouette = silhouette_samples(score_both, labels)
    silhouette_data = pd.DataFrame(
        {"Country": countries, "cluster": labels, "silhouette": silhouette}
    )
    borderline = silhouette_data[silhouette_data["silhouette"] < 0.1]
    borderline = borderline.sort_values("silhouette")
    print(f"Borderline sil<0.1: {borderline['Country'].tolist()}")
    print("Country silhouette ranking (high to low):")
    for row in silhouette_data.sort_values("silhouette", ascending=False).itertuples():
        print(f"  {row.Country}: C{row.cluster}, {row.silhouette:.3f}")
    for cluster in [0, 1]:
        mean_silhouette = silhouette_data.loc[
            silhouette_data["cluster"] == cluster, "silhouette"
        ].mean()
        print(f"C{cluster} mean sil: {mean_silhouette:.3f}")

    data["cluster"] = labels
    print("Final clusters (Both, k-means, k=2):")
    for cluster in sorted(set(labels)):
        members = data.loc[data["cluster"] == cluster, "Country"].tolist()
        print(f"  Cluster {cluster} ({len(members)}): {members}")

    print_cluster_means(data, labels, SCORE_B, "Cluster means Score B (C0, C1, diff):")
    print_cluster_means(data, labels, SCORE_A, "Cluster means Score A (C0, C1, diff):")
    leave_one_out_stability(data, SCORE_A + SCORE_B, labels)

    print("Region x Cluster:")
    for region, members in REGIONS.items():
        cluster_0 = sum(
            country in data.loc[data["cluster"] == 0, "Country"].values
            for country in members
        )
        cluster_1 = sum(
            country in data.loc[data["cluster"] == 1, "Country"].values
            for country in members
        )
        if cluster_0 + cluster_1:
            print(f"  {region}: C0={cluster_0}, C1={cluster_1}")

    sample_sizes = data.groupby("cluster")["Num"].agg(
        ["mean", "min", "max", "median"]
    ).round(1)
    for cluster in [0, 1]:
        stats = sample_sizes.loc[cluster]
        print(
            f"Sample size C{cluster}: mean={stats['mean']}, min={stats['min']}, "
            f"max={stats['max']}, med={stats['median']}"
        )

    for n_clusters in [3, 4]:
        labels = KMeans(
            n_clusters=n_clusters,
            random_state=RANDOM_STATE,
            n_init=10,
        ).fit_predict(score_both)
        print(f"k={n_clusters}:")
        for cluster in range(n_clusters):
            members = data.loc[labels == cluster, "Country"].tolist()
            print(f"  C{cluster} ({len(members)}): {members}")

    print(f"Dendrogram images written to {FIGURES_DIR.relative_to(ROOT)}")
    print("Compile Report.tex.")


if __name__ == "__main__":
    main()
