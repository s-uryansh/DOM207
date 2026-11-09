from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import chi2, norm
from scipy.special import expit
from sklearn.calibration import calibration_curve
from sklearn.metrics import brier_score_loss, roc_auc_score, roc_curve
from sklearn.model_selection import StratifiedKFold
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tools.sm_exceptions import PerfectSeparationError


SEED = 2026
COLS = [
    "inlf", "hours", "kidslt6", "kidsge6", "age", "ed", "sal", "repsal",
    "hushrs", "husage", "hused", "hussal", "faminc", "mtr", "momed",
    "daded", "unem", "city", "exper", "nwifeinc",
]
def load_data(path):
    d = pd.read_excel(path, sheet_name="IWomenJob")
    if len(d) != 753 or set(d.columns) != set(COLS):
        raise ValueError("Unexpected workbook dimensions or columns")
    raw = d["sal"]
    sal = pd.to_numeric(raw.mask(raw.astype(str).str.strip().eq(".")), errors="coerce")
    bad = raw.notna() & sal.isna() & ~raw.astype(str).str.strip().eq(".")
    if bad.any():
        raise ValueError("Unrecognized values in sal")
    d["sal"] = sal
    d["nwifeinc_source"] = pd.to_numeric(d["nwifeinc"], errors="raise")
    miss_sal = d["sal"].isna()
    if not d["inlf"].isin([0, 1]).all() or not d["city"].isin([0, 1]).all():
        raise ValueError("inlf and city must be binary")
    validate_consistency(d)
    if not (miss_sal == d["inlf"].eq(0)).all() or not d.loc[miss_sal, "hours"].eq(0).all():
        raise ValueError("Unexpected structural salary missingness")
    d["nwifeinc"] = (d["faminc"] - d["sal"].fillna(0) * d["hours"]) / 1000
    diff = float((d["nwifeinc"] - d["nwifeinc_source"]).abs().max())
    if d.drop(columns=["sal"]).isna().any().any():
        raise ValueError("Missing values in analysis data")
    return d, diff


def validate_consistency(d):
    counts = d[["kidslt6", "kidsge6"]].to_numpy()
    if (d["hours"] < 0).any() or (d["exper"] < 0).any() or (d["faminc"] < 0).any():
        raise ValueError("Hours, experience, and family income must be nonnegative")
    if (counts < 0).any() or not np.equal(counts, np.round(counts)).all():
        raise ValueError("Child variables must be nonnegative integer counts")
    if not d["mtr"].between(0, 1).all():
        raise ValueError("mtr must lie between zero and one")


def make_design(d, centers=None, income_col="nwifeinc", drop_mtr=False, extra=(), kids_factor=False):
    inc = d[income_col] / 1000 if income_col == "faminc" else d[income_col]
    centers = {
        "age": d["age"].mean(),
        "exper": d["exper"].mean(),
        "ed": d["ed"].mean(),
        "income": inc.mean(),
    } if centers is None else centers
    z = d.copy()
    z["mtr"] = z["mtr"] * 10
    z["age_c"] = z["age"] - centers["age"]
    z["exper_c"] = z["exper"] - centers["exper"]
    z["ed_c"] = z["ed"] - centers["ed"]
    inc_name = f"{income_col}_c"
    z[inc_name] = inc - centers["income"]
    z["age_sq"] = z["age_c"] ** 2
    z["exper_sq"] = z["exper_c"] ** 2
    z["ed_city"] = z["ed_c"] * z["city"]
    if kids_factor:
        z["kids_1"] = z["kidslt6"].eq(1).astype(int)
        z["kids_2plus"] = z["kidslt6"].ge(2).astype(int)
        z["kid1_income"] = z["kids_1"] * z[inc_name]
        z["kid2plus_income"] = z["kids_2plus"] * z[inc_name]
        kids = ["kids_1", "kids_2plus"]
        kid_terms = ["kid1_income", "kid2plus_income"]
    else:
        z["kid_income"] = z["kidslt6"] * z[inc_name]
        kids = ["kidslt6"]
        kid_terms = ["kid_income"]
    base = kids + ["kidsge6", "age_c", "ed_c", "exper_c", inc_name, "mtr", "unem", "city"]
    if drop_mtr:
        base.remove("mtr")
    base += list(extra)
    quad_cols = ["age_sq", "exper_sq"]
    full_cols = base + quad_cols + kid_terms + ["ed_city"]
    linear = sm.add_constant(z[base], has_constant="add")
    quad = sm.add_constant(z[base + quad_cols], has_constant="add")
    full = sm.add_constant(z[full_cols], has_constant="add")
    return {"linear": linear, "quadratic": quad, "full": full, "centers": centers}


def fit_one(y, x, link="logit"):
    model = sm.Logit if link == "logit" else sm.Probit
    return model(y, x, missing="raise").fit(disp=False, maxiter=200)


def lr_test(small, large):
    stat = max(0.0, 2 * (large.llf - small.llf))
    df = int(large.df_model - small.df_model)
    return stat, df, float(chi2.sf(stat, df))


def fit_models(d):
    x = make_design(d)
    y = d["inlf"]
    out = {f"logit_{key}": fit_one(y, x[key]) for key in ("linear", "quadratic", "full")}
    out["probit_full"] = fit_one(y, x["full"], "probit")
    out["lpm"] = sm.OLS(y, x["full"], missing="raise").fit(cov_type="HC3")
    out["design"] = x
    out["lr_quadratic"] = lr_test(out["logit_linear"], out["logit_quadratic"])
    out["lr_interaction"] = lr_test(out["logit_quadratic"], out["logit_full"])
    return out


def vif_table(x):
    cols = [col for col in x.columns if col != "const"]
    vals = [variance_inflation_factor(x.to_numpy(), x.columns.get_loc(col)) for col in cols]
    return pd.Series(vals, index=cols, name="VIF").sort_values(ascending=False)


def spouse_vifs(d):
    spouse = make_design(d, extra=("husage", "hused", "hushrs"))["full"]
    wage = make_design(d, extra=("husage", "hused", "hushrs", "hussal"))["full"]
    return {
        "spouse": vif_table(spouse),
        "wage": vif_table(wage),
        "correlation": {
            "nwifeinc_hussal": float(d["nwifeinc"].corr(d["hussal"])),
            "nwifeinc_hushrs": float(d["nwifeinc"].corr(d["hushrs"])),
        },
    }


def ame_value(params, name, x, link="logit"):
    b = pd.Series(params, index=x.columns)
    mat = x.to_numpy()
    eta = mat @ b.to_numpy()
    p = norm.cdf(eta) if link == "probit" else expit(eta) if link == "logit" else eta
    inc_col = "nwifeinc_c" if "nwifeinc_c" in x else "faminc_c"
    inc_term = inc_col
    if name == "city":
        x0 = x.copy()
        x1 = x.copy()
        x0["city"] = 0
        x0["ed_city"] = 0
        x1["city"] = 1
        x1["ed_city"] = x["ed_c"]
        eta0 = x0.to_numpy() @ b.to_numpy()
        eta1 = x1.to_numpy() @ b.to_numpy()
        pred = norm.cdf if link == "probit" else expit if link == "logit" else lambda z: z
        return float(np.mean(pred(eta1) - pred(eta0)))
    if name == "kidslt6":
        deriv = b[name] + b["kid_income"] * x[inc_col]
    elif name == "kidsge6":
        deriv = b[name]
    elif name == "age":
        deriv = b["age_c"] + 2 * b["age_sq"] * x["age_c"]
    elif name == "ed":
        deriv = b["ed_c"] + b["ed_city"] * x["city"]
    elif name == "exper":
        deriv = b["exper_c"] + 2 * b["exper_sq"] * x["exper_c"]
    elif name in ("nwifeinc", "faminc"):
        deriv = b[inc_term] + b["kid_income"] * x["kidslt6"]
    else:
        deriv = b[name]
    scale = norm.pdf(eta) if link == "probit" else p * (1 - p) if link == "logit" else np.ones(len(x))
    return float(np.mean(scale * deriv))


def average_effects(model, x):
    b = np.asarray(model.params)
    cov = np.asarray(model.cov_params())
    cls = model.model.__class__.__name__.lower()
    link = "probit" if cls == "probit" else "linear" if cls == "ols" else "logit"
    inc_name = "nwifeinc" if "nwifeinc_c" in x else "faminc"
    cols = {
        "kidslt6": "kidslt6", "kidsge6": "kidsge6", "age": "age_c", "ed": "ed_c",
        "exper": "exper_c", inc_name: f"{inc_name}_c", "mtr": "mtr", "unem": "unem", "city": "city",
    }
    names = [name for name, col in cols.items() if col in x]
    rows = []
    for name in names:
        val = ame_value(b, name, x, link)
        grad = np.empty(len(b))
        for idx in range(len(b)):
            step = 1e-5 * max(1.0, abs(b[idx]))
            bp = b.copy()
            bm = b.copy()
            bp[idx] += step
            bm[idx] -= step
            grad[idx] = (ame_value(bp, name, x, link) - ame_value(bm, name, x, link)) / (2 * step)
        se = float(np.sqrt(max(0.0, grad @ cov @ grad)))
        rows.append((name, val, se, val - 1.96 * se, val + 1.96 * se))
    return pd.DataFrame(rows, columns=["term", "ame", "se", "low", "high"]).set_index("term")


def fit_sensitivities(d):
    specs = {
        "no_mtr": make_design(d, drop_mtr=True),
        "faminc": make_design(d, income_col="faminc"),
        "spouse": make_design(d, extra=("husage", "hused", "hushrs")),
        "parents": make_design(d, extra=("momed", "daded")),
    }
    cat = d["kidslt6"].where(d["kidslt6"] < 2, 2)
    tab = pd.crosstab(cat, d["inlf"])
    if len(tab) == 3 and tab.ge(1).all().all() and tab.sum(axis=1).ge(10).all():
        specs["kids_factor"] = make_design(d, kids_factor=True)
    out = {name: fit_one(d["inlf"], spec["full"]) for name, spec in specs.items()}
    out["designs"] = specs
    return out


def cross_validation(d):
    y = d["inlf"].to_numpy()
    oof = np.full(len(d), np.nan)
    fold_auc = []
    conv = []
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    for tr, te in cv.split(np.zeros(len(d)), y):
        xtr = make_design(d.iloc[tr])
        xte = make_design(d.iloc[te], centers=xtr["centers"])
        res = fit_one(y[tr], xtr["full"])
        oof[te] = res.predict(xte["full"])
        fold_auc.append(roc_auc_score(y[te], oof[te]))
        conv.append(bool(res.mle_retvals.get("converged", False)))
    cal_true, cal_pred = calibration_curve(y, oof, n_bins=10, strategy="quantile")
    return {
        "auc": float(roc_auc_score(y, oof)),
        "fold_auc": np.asarray(fold_auc),
        "oof": pd.Series(oof, index=d.index),
        "cal_true": cal_true,
        "cal_pred": cal_pred,
        "converged": all(conv),
    }


def influence_summary(model):
    inf = model.get_influence()
    cook = np.asarray(inf.cooks_distance[0])
    hat = np.asarray(inf.hat_matrix_diag)
    resid = np.asarray(inf.resid_studentized)
    resid_dev = np.asarray(model.resid_dev)
    dfb = np.asarray(inf.dfbetas)
    return {
        "cook": cook,
        "hat": hat,
        "resid": resid,
        "resid_dev": resid_dev,
        "dfbetas": dfb,
        "max_cook_idx": int(np.nanargmax(cook)),
        "max_hat_idx": int(np.nanargmax(hat)),
        "max_resid_idx": int(np.nanargmax(np.abs(resid))),
        "max_dev_idx": int(np.nanargmax(np.abs(resid_dev))),
        "cook_threshold_count": int(np.sum(cook > 4 / len(cook))),
        "max_dfbeta": dict(zip(model.model.exog_names, np.nanmax(np.abs(dfb), axis=0))),
    }


def sparse_cells(d):
    tab = pd.crosstab([d["kidslt6"], d["city"]], d["inlf"])
    tab.columns = ["not_participating", "participating"]
    tab["n"] = tab.sum(axis=1)
    tab["pure"] = tab[["not_participating", "participating"]].eq(0).any(axis=1)
    return tab


def leave_one_out(d, x, model):
    y = d["inlf"].to_numpy()
    b = np.asarray(model.params)
    names = model.model.exog_names
    full_ame = {name: ame_value(b, name, x) for name in ("kidslt6", "nwifeinc", "city")}
    keys = ["kid_income", "ed_city"]
    max_b = {key: (0.0, -1) for key in keys}
    max_ame = {key: (0.0, -1) for key in full_ame}
    ok = 0
    failed = []
    for idx in range(len(d)):
        keep = np.arange(len(d)) != idx
        xi = x.iloc[keep]
        try:
            res = fit_one(y[keep], xi)
        except (PerfectSeparationError, np.linalg.LinAlgError, ValueError, FloatingPointError):
            failed.append(idx)
            continue
        if not res.mle_retvals.get("converged", False):
            failed.append(idx)
            continue
        ok += 1
        for key in keys:
            delta = abs(float(res.params[key] - model.params[key]))
            if delta > max_b[key][0]:
                max_b[key] = (delta, idx)
        for key in full_ame:
            val = ame_value(res.params, key, xi)
            delta = abs(val - full_ame[key])
            if delta > max_ame[key][0]:
                max_ame[key] = (delta, idx)
    return {"fit_count": len(d), "successful": ok, "failed": failed, "coef_changes": max_b, "ame_changes": max_ame,
            "max_kid_ame_change": max_ame["kidslt6"][0], "max_income_ame_change": max_ame["nwifeinc"][0]}


def in_sample_performance(y, model, x):
    p = np.asarray(model.predict(x))
    actual, pred = calibration_curve(y, p, n_bins=10, strategy="quantile")
    return {
        "pred": p,
        "auc": float(roc_auc_score(y, p)),
        "brier": float(brier_score_loss(y, p)),
        "cal_true": actual,
        "cal_pred": pred,
    }


def coefficient_table(model):
    ci = np.asarray(model.conf_int())
    tab = pd.DataFrame({
        "coef": model.params,
        "se": model.bse,
        "p": model.pvalues,
        "low": ci[:, 0],
        "high": ci[:, 1],
    })
    tab["odds_ratio"] = np.exp(tab["coef"])
    tab["or_low"] = np.exp(tab["low"])
    tab["or_high"] = np.exp(tab["high"])
    return tab


def child_effect_profile(d, model, x):
    cls = model.model.__class__.__name__.lower()
    link = "probit" if cls == "probit" else "linear" if cls == "ols" else "logit"
    rows = []
    for q in (0.25, 0.5, 0.75):
        income = float(d["nwifeinc"].quantile(q))
        z = x.copy()
        z["nwifeinc_c"] = income - d["nwifeinc"].mean()
        z["kid_income"] = z["kidslt6"] * z["nwifeinc_c"]
        rows.append((q, income, ame_value(model.params, "kidslt6", z, link)))
    return pd.DataFrame(rows, columns=["quantile", "income_level", "ame_kidslt6"])


def make_figures(d, models, cv, perf, outdir):
    plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Liberation Serif"], "font.size": 8})
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.6))
    counts = d["inlf"].value_counts().reindex([0, 1])
    ax[0].bar(["Not participating", "Participating"], counts, color=["#8c9aa8", "#176b65"])
    for idx, value in enumerate(counts):
        ax[0].text(idx, value + 8, str(int(value)), ha="center")
    ax[0].set_ylabel("Women")
    ax[0].set_title("Participation status")
    rates = d.groupby("kidslt6")["inlf"].agg(["mean", "size"])
    ax[1].bar(rates.index.astype(str), rates["mean"], color="#176b65")
    ax[1].set_xticks(np.arange(len(rates)), [f"{idx}\n(n={int(size)})" for idx, size in rates["size"].items()])
    ax[1].set(xlabel="Children under six", ylabel="Participation share", ylim=(0, 1), title="Participation by young children")
    fig.tight_layout()
    path = out / "participation.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    paths.append(path)

    fig, ax = plt.subplots(2, 2, figsize=(8.5, 6.2))
    for a, col, label in zip(ax.flat, ["age", "ed", "exper", "nwifeinc"], ["Age (years)", "Education (years)", "Experience (years)", "Nonwife income (thousands)"]):
        vals = [d.loc[d["inlf"].eq(v), col] for v in (0, 1)]
        a.boxplot(vals, tick_labels=["No", "Yes"], showfliers=False)
        a.set(title=label, xlabel="Participated", ylabel=label)
    fig.tight_layout()
    path = out / "profiles.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    paths.append(path)

    vals = np.linspace(d["nwifeinc"].quantile(0.05), d["nwifeinc"].quantile(0.95), 60)
    rows = []
    for kids in (0, 1, 2):
        grid = pd.DataFrame({
            "kidslt6": kids, "kidsge6": d["kidsge6"].median(), "age": d["age"].mean(),
            "ed": d["ed"].mean(), "exper": d["exper"].mean(), "nwifeinc": vals,
            "mtr": d["mtr"].median(), "unem": d["unem"].median(), "city": 0,
        })
        x = make_design(grid, centers=models["design"]["centers"])["full"]
        rows.append(models["logit_full"].predict(x))
    fig, ax = plt.subplots(figsize=(3.4, 2.6))
    for kids, prob in zip((0, 1, 2), rows):
        ax.plot(vals, prob, label=f"{kids} child" if kids == 1 else f"{kids} children", linewidth=2)
    ax.set(xlabel="Nonwife income (thousands)", ylabel="Participation probability", ylim=(0, 1), title="Predicted probability by child count")
    ax.legend(frameon=False)
    fig.tight_layout()
    path = out / "interaction.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    paths.append(path)

    fpr, tpr, _ = roc_curve(d["inlf"], cv["oof"])
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.8))
    ax[0].plot(fpr, tpr, color="#176b65", linewidth=2, label=f"5-fold AUC = {cv['auc']:.3f}")
    fpr_in, tpr_in, _ = roc_curve(d["inlf"], perf["pred"])
    ax[0].plot(fpr_in, tpr_in, color="#8c9aa8", linewidth=1.5, linestyle=":", label=f"In-sample AUC = {perf['auc']:.3f}")
    ax[0].plot([0, 1], [0, 1], color="#777777", linestyle="--")
    ax[0].set(xlabel="False positive rate", ylabel="True positive rate", title="Out-of-fold ROC", xlim=(0, 1), ylim=(0, 1))
    ax[0].legend(frameon=False)
    ax[1].plot(cv["cal_pred"], cv["cal_true"], marker="o", color="#176b65")
    ax[1].plot([0, 1], [0, 1], color="#777777", linestyle="--")
    ax[1].set(xlabel="Mean predicted probability", ylabel="Observed participation share", title="Out-of-fold calibration", xlim=(0, 1), ylim=(0, 1))
    fig.tight_layout()
    path = out / "roc_calibration.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    paths.append(path)
    return paths


def sensitivity_table(models):
    terms = [
        "kidslt6", "kids_1", "kids_2plus", "kidsge6", "nwifeinc_c", "faminc_c",
        "mtr", "kid_income", "kid1_income", "kid2plus_income", "ed_city",
        "husage", "hused", "hushrs", "momed", "daded",
    ]
    rows = []
    for name, model in models.items():
        if name == "designs":
            continue
        for term in terms:
            if term in model.params.index:
                rows.append((name, term, model.params[term], model.bse[term], model.pvalues[term]))
    return pd.DataFrame(rows, columns=["model", "term", "coef", "se", "p"])


def print_results(d, diff, models, sens, cv, perf, vif, spouse_collinearity, cells, influence, loo, figures):
    full = models["logit_full"]
    x = models["design"]["full"]
    ame = average_effects(full, x)
    probit_ame = average_effects(models["probit_full"], x)
    lpm_ame = average_effects(models["lpm"], x)
    kid_profile = child_effect_profile(d, full, x)
    out_range = ((models["lpm"].fittedvalues < 0) | (models["lpm"].fittedvalues > 1)).mean()
    print("DATA CHECKS")
    print(f"Rows: {len(d)}; participation: {int(d.inlf.sum())}; nonparticipation: {int(d.inlf.eq(0).sum())}")
    print(f"Participation share: {d.inlf.mean():.4f}; salary unavailable: {int(d.sal.isna().sum())}; max nwifeinc difference: {diff:.8f}")
    print("Missing values:")
    print(d.isna().sum().to_string())
    print("Selected descriptive statistics:")
    print(d[["age", "ed", "exper", "kidslt6", "kidsge6", "nwifeinc", "mtr", "unem"]].describe().round(3).to_string())
    print("Participation by child count:")
    print(d.groupby("kidslt6")["inlf"].agg(["count", "mean"]).round(4).to_string())
    print("\nFULL LOGIT COEFFICIENTS")
    print(coefficient_table(full).round(4).to_string())
    print("\nAVERAGE MARGINAL EFFECTS")
    print(ame.round(4).to_string())
    print("\nCHILD-COUNT EFFECT AT NON-WIFE INCOME QUANTILES")
    print(kid_profile.round(4).to_string(index=False))
    print("\nPROBIT AVERAGE MARGINAL EFFECTS")
    print(probit_ame.round(4).to_string())
    print("\nHC3 LINEAR-PROBABILITY EFFECTS")
    print(lpm_ame.round(4).to_string())
    print(f"\nLPM predictions outside [0, 1]: {out_range:.4%}")
    print("\nPRESPECIFIED BLOCK TESTS")
    print(f"Quadratic block LR={models['lr_quadratic'][0]:.4f}, df={models['lr_quadratic'][1]}, p={models['lr_quadratic'][2]:.6f}")
    print(f"Interaction block LR={models['lr_interaction'][0]:.4f}, df={models['lr_interaction'][1]}, p={models['lr_interaction'][2]:.6f}")
    print("\nFIT AND CROSS-VALIDATION")
    print(f"Logit converged: {full.mle_retvals.get('converged', False)}; McFadden R2: {full.prsquared:.4f}; AIC: {full.aic:.3f}; BIC: {full.bic:.3f}")
    print(f"In-sample AUC: {perf['auc']:.4f}; Brier score: {perf['brier']:.4f}")
    print(f"Five-fold out-of-fold AUC: {cv['auc']:.4f}; fold AUCs: {np.round(cv['fold_auc'], 4).tolist()}; all folds converged: {cv['converged']}")
    print(f"Events per slope: {d.inlf.sum() / 13:.2f}; non-events per slope: {d.inlf.eq(0).sum() / 13:.2f}")
    print("\nSENSITIVITY COEFFICIENTS")
    print(sensitivity_table(sens).round(4).to_string(index=False))
    print("\nMULTICOLLINEARITY")
    print(vif.round(3).to_string())
    print(f"Correlation between mtr and nwifeinc: {d.mtr.corr(d.nwifeinc):.4f}")
    print("Spouse-control VIFs:")
    print(spouse_collinearity["spouse"].loc[["nwifeinc_c", "hushrs", "husage", "hused"]].round(3).to_string())
    print("Spouse wage VIFs and income correlations:")
    print(spouse_collinearity["wage"].loc[["nwifeinc_c", "hussal"]].round(3).to_string())
    print(spouse_collinearity["correlation"])
    print("\nKIDS UNDER SIX BY CITY CELLS")
    print(cells.to_string())
    print("\nINFLUENCE")
    print(f"Largest Cook distance: row {influence['max_cook_idx'] + 2}, value {influence['cook'][influence['max_cook_idx']]:.6f}")
    print(f"Cook distance above 4/n: {influence['cook_threshold_count']}")
    print(f"Largest leverage: row {influence['max_hat_idx'] + 2}, value {influence['hat'][influence['max_hat_idx']]:.6f}")
    print(f"Largest absolute deviance residual: row {influence['max_dev_idx'] + 2}, value {influence['resid_dev'][influence['max_dev_idx']]:.4f}")
    print("Maximum absolute DFBETA by term:")
    print(pd.Series(influence["max_dfbeta"]).round(4).to_string())
    print("\nLEAVE-ONE-OUT CHECK")
    print(f"Successful refits: {loo['successful']}; failed or nonconverged: {len(loo['failed'])}")
    print(f"Largest interaction coefficient changes: {loo['coef_changes']}")
    print(f"Largest average effect changes: {loo['ame_changes']}")
    print("\nFIGURES")
    for path in figures:
        print(path)


def run_analysis(path, outdir):
    d, diff = load_data(path)
    models = fit_models(d)
    sens = fit_sensitivities(d)
    cv = cross_validation(d)
    perf = in_sample_performance(d["inlf"], models["logit_full"], models["design"]["full"])
    vif = vif_table(models["design"]["full"])
    spouse_collinearity = spouse_vifs(d)
    cells = sparse_cells(d)
    influence = influence_summary(models["logit_full"])
    loo = leave_one_out(d, models["design"]["full"], models["logit_full"])
    figures = make_figures(d, models, cv, perf, outdir)
    print_results(d, diff, models, sens, cv, perf, vif, spouse_collinearity, cells, influence, loo, figures)
    return {"data": d, "models": models, "sensitivities": sens, "cv": cv, "performance": perf,
            "vif": vif, "spouse_vifs": spouse_collinearity, "cells": cells, "influence": influence,
            "leave_one_out": loo, "figures": figures}


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    run_analysis(root / "IWomenJob.xlsx", root / "figures")
