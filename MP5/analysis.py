import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.stattools import durbin_watson
from statsmodels.stats.diagnostic import het_breuschpagan, normal_ad
from statsmodels.stats.outliers_influence import variance_inflation_factor
from scipy import stats

df = pd.read_excel("AusREInvest.xlsx", sheet_name="Data")
os.makedirs("figures", exist_ok=True)
df = df.sort_values("year").reset_index(drop=True)

df["pinv"] = df["relinvest"] / df["pop"]
df["lpinv"] = np.log(df["pinv"])
df["lprice"] = np.log(df["hsprcindx"])
df["trend"] = df["tmperd"].astype(float)
df["trend2"] = df["trend"] ** 2

n = len(df)
Xnames = ["lprice", "trend", "trend2"]

def fit(formula, data):
    return smf.ols(formula, data=data).fit()

def vif_table(data, cols):
    X = sm.add_constant(data[cols])
    return pd.DataFrame({"vif": [variance_inflation_factor(X.values, j) for j in range(X.shape[1])]}, index=X.columns)

m1 = fit("lpinv ~ lprice + trend + trend2", df)
m2 = fit("lpinv ~ lprice + trend", df)
m3 = fit("lpinv ~ lprice", df)
m4 = fit("lpinv ~ lprice + trend + trend2 + lprice:trend", df)
m5 = fit("pinv ~ hsprcindx + trend + trend2", df)

resid = m1.resid
fitted = m1.fittedvalues
bp = het_breuschpagan(resid, sm.add_constant(np.column_stack([df["lprice"], df["trend"], df["trend2"]])))
dw = durbin_watson(resid)
jb = normal_ad(resid)

fig1, ax = plt.subplots(figsize=(8.5, 4.2))
ax.plot(df["year"], df["pinv"], marker="o", label="Per-head investment")
ax.set_xlabel("Year"); ax.set_ylabel("Per-head RE investment (AUS$ per person)")
ax.set_title("Per-head real estate investment, 1975-2016")
ax.grid(True, alpha=0.3); ax.legend()
fig1.tight_layout(); fig1.savefig("figures/pinv_ts.png", dpi=150); plt.close(fig1)

fig2, ax = plt.subplots(figsize=(8.5, 4.2))
ax.plot(df["year"], df["hsprcindx"], marker="o", color="tab:red", label="Housing price index")
ax.set_xlabel("Year"); ax.set_ylabel("Price index (2006 = 1)")
ax.set_title("Housing price index, 1975-2016")
ax.grid(True, alpha=0.3); ax.legend()
fig2.tight_layout(); fig2.savefig("figures/price_ts.png", dpi=150); plt.close(fig2)

fig3, ax = plt.subplots(figsize=(8.5, 4.2))
ax.scatter(df["lprice"], df["lpinv"], label="observations")
xg = np.linspace(df["lprice"].min(), df["lprice"].max(), 100)
pred_m3 = m3.predict(pd.DataFrame({"lprice": xg}))
ax.plot(xg, pred_m3, color="tab:red", label="log-log fit (no trend)")
ax.set_xlabel("log(housing price index)"); ax.set_ylabel("log(per-head investment)")
ax.set_title("Per-head investment vs price index")
ax.grid(True, alpha=0.3); ax.legend()
fig3.tight_layout(); fig3.savefig("figures/scatter.png", dpi=150); plt.close(fig3)

fig4, ax = plt.subplots(figsize=(8.5, 4.2))
ax.scatter(fitted, resid, s=20)
ax.axhline(0, color="tab:red", lw=1)
ax.set_xlabel("Fitted values"); ax.set_ylabel("Residuals")
ax.set_title("Residuals vs fitted (main specification)")
ax.grid(True, alpha=0.3)
fig4.tight_layout(); fig4.savefig("figures/resid_fit.png", dpi=150); plt.close(fig4)

fig5, ax = plt.subplots(figsize=(8.5, 4.2))
osm, osr = stats.probplot(resid, fit=False)
ax.scatter(osm, osr, s=20)
ax.plot([osm.min(), osm.max()], [osm.min(), osm.max()], color="tab:red", lw=1)
ax.set_xlabel("Theoretical quantiles"); ax.set_ylabel("Sample quantiles")
ax.set_title("Normal Q-Q plot of residuals")
ax.grid(True, alpha=0.3)
fig5.tight_layout(); fig5.savefig("figures/qq.png", dpi=150); plt.close(fig5)

fig6, ax = plt.subplots(figsize=(8.5, 4.2))
specs = ["m1", "m2", "m3", "m4"]
models = [m1, m2, m3, m4]
labels = ["Price+trend+trend^2", "Price+trend", "Price only", "Price+trend+interaction"]
coefs = [m.params["lprice"] for m in models]
ses = [m.bse["lprice"] for m in models]
ypos = np.arange(len(specs))
ax.errorbar(coefs, ypos, xerr=ses, fmt="o", color="tab:blue", capsize=4, label="price coefficient ± 1 SE")
ax.axvline(0, color="tab:red", lw=1)
ax.set_yticks(ypos); ax.set_yticklabels(labels)
ax.invert_yaxis()
ax.set_xlabel("Price index coefficient (log-log)")
ax.set_title("Price coefficient across specifications")
ax.grid(True, alpha=0.3); ax.legend()
fig6.tight_layout(); fig6.savefig("figures/coefs.png", dpi=150); plt.close(fig6)

fig7, ax = plt.subplots(figsize=(8.5, 4.2))
ax.scatter(df["year"], m1.fittedvalues, label="fitted", marker="o", alpha=0.7)
ax.scatter(df["year"], df["lpinv"], label="observed", marker="x", alpha=0.7)
ax.plot(df["year"], m1.fittedvalues, color="tab:red", lw=1, alpha=0.5)
ax.set_xlabel("Year"); ax.set_ylabel("log(per-head investment)")
ax.set_title("Observed vs fitted, main specification")
ax.grid(True, alpha=0.3); ax.legend()
fig7.tight_layout(); fig7.savefig("figures/fitted.png", dpi=150); plt.close(fig7)

print("n =", n)
print("\nDescriptive:")
print(df[["relinvest","pop","pinv","hsprcindx"]].describe().round(4).to_string())
print("\nCorrelations:")
print(df[["pinv","lpinv","lprice","trend","hsprcindx"]].corr().round(4).to_string())
print("\nVIF (main spec):")
print(vif_table(df, Xnames).round(3).to_string())
print("\nMain specification (m1):")
print(m1.summary().as_text())
print("\nElasticity (lprice coef m1):", round(m1.params["lprice"],4), "SE:", round(m1.bse["lprice"],4), "p:", round(m1.pvalues["lprice"],4))
print("\nm2:", m2.params["lprice"], m2.bse["lprice"], m2.pvalues["lprice"], "R2:", round(m2.rsquared,4))
print("\nm3:", m3.params["lprice"], m3.bse["lprice"], m3.pvalues["lprice"], "R2:", round(m3.rsquared,4))
print("\nm4 interaction p:", round(m4.pvalues["lprice:trend"],4))
print("\nDiagnostics m1:")
print("BP lm:", round(bp[0],4), "p:", round(bp[1],4))
print("BP f:", round(bp[2],4), "p:", round(bp[3],4))
print("Durbin-Watson:", round(dw,4))
print("Anderson-Darling stat:", round(jb[0],4), "p:", round(jb[1],4))
print("R2:", round(m1.rsquared,4), "Adj R2:", round(m1.rsquared_adj,4))
print("\nTrend coef m1:", round(m1.params["trend"],4), "SE:", round(m1.bse["trend"],4), "p:", round(m1.pvalues["trend"],4))
print("Trend2 coef m1:", round(m1.params["trend2"],4), "SE:", round(m1.bse["trend2"],4), "p:", round(m1.pvalues["trend2"],4))
