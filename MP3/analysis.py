# MP3 IMF: cluster 37 countries on 9 ICT-worker issues
from pathlib import Path
import tempfile
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.mixture import GaussianMixture
from sklearn.metrics import silhouette_score, silhouette_samples, adjusted_rand_score
from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "dataset" / "ICTIndiv.xlsx"
RANDOM_STATE = 42
TMP = Path(tempfile.mkdtemp(prefix="mp3figs_"))

df = pd.read_excel(DATA)
issues = ["FC", "JI", "SE", "WS", "WO", "WH", "WE", "TI", "TA"]
scoreA = [f"{i}_FSMean" for i in issues]
scoreB = [f"{i}_Smean" for i in issues]

print("A vs B corr:", ", ".join(f"{i}={df[f'{i}_FSMean'].corr(df[f'{i}_Smean']):.4f}" for i in issues))
print(f"Unused: Code (ID 1-46), Num (sample size {df['Num'].min()}-{df['Num'].max()})")

Xa = StandardScaler().fit_transform(df[scoreA].to_numpy(float))
Xb = StandardScaler().fit_transform(df[scoreB].to_numpy(float))
Xboth = StandardScaler().fit_transform(np.hstack([Xa, Xb]))

for name, X in [("A", Xa), ("B", Xb)]:
    z = np.abs((X - X.mean(0)) / X.std(0))
    print(f"Outliers |z|>3 {name}: {int((z > 3).sum())} retained")

for name, X in [("A", Xa), ("B", Xb), ("Both", Xboth)]:
    pca = PCA(random_state=RANDOM_STATE).fit(X)
    cum = np.cumsum(pca.explained_variance_ratio_)
    k80 = int(np.searchsorted(cum, 0.80) + 1)
    print(f"PCA {name}: PC1={pca.explained_variance_ratio_[0]:.3f}, PC2={pca.explained_variance_ratio_[1]:.3f}, PC3={pca.explained_variance_ratio_[2]:.3f}, 80% at {k80}")

print(f"Max off-diag corr A: {np.abs(np.corrcoef(Xa, rowvar=False) - np.eye(9)).max():.3f}")
print(f"Max off-diag corr B: {np.abs(np.corrcoef(Xb, rowvar=False) - np.eye(9)).max():.3f}")

print("Silhouette k=2..6:")
for name, X in [("A", Xa), ("B", Xb), ("Both", Xboth)]:
    sils = [silhouette_score(X, KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10).fit_predict(X)) for k in range(2,7)]
    print(f"  {name}: " + " ".join(f"k={k}:{s:.3f}" for k,s in zip(range(2,7), sils)))

print("Elbow inertia k=2..8:")
for name, X in [("A", Xa), ("B", Xb), ("Both", Xboth)]:
    iners = [KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10).fit(X).inertia_ for k in range(2,9)]
    print(f"  {name}: " + " ".join(f"k={k}:{v:.1f}" for k,v in zip(range(2,9), iners)))

for name, X in [("A", Xa), ("B", Xb), ("Both", Xboth)]:
    Z = linkage(X, method="ward")
    plt.figure(figsize=(10, 5))
    dendrogram(Z, labels=df["Country"].tolist(), leaf_rotation=90)
    plt.title(f"Dendrogram Ward - Score {name}")
    plt.tight_layout()
    plt.savefig(TMP / f"dend_{name}.png", dpi=300)
    plt.close()

k = 2
def cluster_labels(X):
    km = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10).fit(X)
    ward = fcluster(linkage(X, method="ward"), t=k, criterion="maxclust") - 1
    avg = AgglomerativeClustering(n_clusters=k, linkage="average").fit_predict(X)
    gmm = GaussianMixture(n_components=k, random_state=RANDOM_STATE).fit_predict(X)
    return {"kmeans": km.labels_, "ward": ward, "average": avg, "gmm": gmm, "km_obj": km}

resA = cluster_labels(Xa)
resB = cluster_labels(Xb)
resBoth = cluster_labels(Xboth)

print("Cross-method ARI k=2 (ward vs kmeans):", 
      f"A={adjusted_rand_score(resA['ward'], resA['kmeans']):.3f}",
      f"B={adjusted_rand_score(resB['ward'], resB['kmeans']):.3f}",
      f"Both={adjusted_rand_score(resBoth['ward'], resBoth['kmeans']):.3f}")

print("Cross-score ARI k-means:")
for kk in [2, 3, 4]:
    kmA = KMeans(n_clusters=kk, random_state=RANDOM_STATE, n_init=10).fit_predict(Xa)
    kmB = KMeans(n_clusters=kk, random_state=RANDOM_STATE, n_init=10).fit_predict(Xb)
    kmBoth = KMeans(n_clusters=kk, random_state=RANDOM_STATE, n_init=10).fit_predict(Xboth)
    print(f"  k={kk}: A-B={adjusted_rand_score(kmA, kmB):.3f}, A-Both={adjusted_rand_score(kmA, kmBoth):.3f}, B-Both={adjusted_rand_score(kmB, kmBoth):.3f}")

sil_vals = silhouette_samples(Xboth, resBoth["kmeans"])
sil_df = pd.DataFrame({"Country": df["Country"], "cluster": resBoth["kmeans"], "silhouette": sil_vals})
borderline = sil_df[sil_df["silhouette"] < 0.1].sort_values("silhouette")
print(f"Borderline sil<0.1: {borderline['Country'].tolist()}")
print(f"C0 mean sil: {sil_df[sil_df.cluster==0].silhouette.mean():.3f}, C1: {sil_df[sil_df.cluster==1].silhouette.mean():.3f}")

print("Bootstrap stability (200 resamples):")
for kk in [2, 3, 4]:
    aris = []
    rng = np.random.default_rng(RANDOM_STATE)
    for _ in range(200):
        idx = rng.choice(len(Xboth), len(Xboth), replace=True)
        km1 = KMeans(n_clusters=kk, random_state=RANDOM_STATE, n_init=10).fit_predict(Xboth[idx])
        km2 = KMeans(n_clusters=kk, random_state=RANDOM_STATE, n_init=10).fit_predict(Xboth[idx])
        aris.append(adjusted_rand_score(km1, km2))
    print(f"  k={kk}: mean ARI={np.mean(aris):.3f}")

final_labels = resBoth["kmeans"]
df["cluster"] = final_labels
print("Final clusters (Both, k-means, k=2):")
for c in sorted(set(final_labels)):
    members = df.loc[df.cluster == c, "Country"].tolist()
    print(f"  Cluster {c} ({len(members)}): {members}")

print("Cluster means Score B (C0, C1, diff):")
c0 = df[df.cluster==0][scoreB].mean().round(3)
c1 = df[df.cluster==1][scoreB].mean().round(3)
print("  " + ", ".join(f"{i}: {c0[i]:.3f}/{c1[i]:.3f}/{c0[i]-c1[i]:.3f}" for i in scoreB))

print("Cluster means Score A (C0, C1, diff):")
c0 = df[df.cluster==0][scoreA].mean().round(3)
c1 = df[df.cluster==1][scoreA].mean().round(3)
print("  " + ", ".join(f"{i}: {c0[i]:.3f}/{c1[i]:.3f}/{c0[i]-c1[i]:.3f}" for i in scoreA))

regions = {
    "EastAsia": ["China", "Japan", "South Korea", "Taiwan"],
    "SEAsia": ["Malaysia", "Thailand", "Vietnam"],
    "SouthAsia": ["Bangladesh", "India", "Pakistan"],
    "MidEast": ["Iran", "Jordan", "Turkey"],
    "EastEU": ["Hungary", "Lithuania", "Macedonia", "Poland", "Romania", "Russia"],
    "WestEU": ["Finland", "France", "Germany", "Greece", "Italy", "Portugal", "UK"],
    "N America": ["Canada", "USA"],
    "LatAm": ["Argentina", "Brazil", "Mexico", "Peru"],
    "Africa": ["Egypt", "Ghana", "Nigeria", "South Africa"],
    "Oceania": ["New Zealand"]
}
print("Region x Cluster:")
for region, countries in regions.items():
    c0 = sum(1 for cn in countries if cn in df.loc[df.cluster==0, "Country"].values)
    c1 = sum(1 for cn in countries if cn in df.loc[df.cluster==1, "Country"].values)
    if c0+c1 > 0:
        print(f"  {region}: C0={c0}, C1={c1}")

g = df.groupby("cluster")["Num"].agg(["mean", "min", "max", "median"]).round(1)
print(f"Sample size C0: mean={g.loc[0,'mean']}, min={g.loc[0,'min']}, max={g.loc[0,'max']}, med={g.loc[0,'median']}")
print(f"Sample size C1: mean={g.loc[1,'mean']}, min={g.loc[1,'min']}, max={g.loc[1,'max']}, med={g.loc[1,'median']}")

for kk in [3, 4]:
    km = KMeans(n_clusters=kk, random_state=RANDOM_STATE, n_init=10).fit_predict(Xboth)
    print(f"k={kk}:")
    for c in range(kk):
        members = df.loc[km==c, "Country"].tolist()
        print(f"  C{c} ({len(members)}): {members}")