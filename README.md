# DOM207 Projects

<p align="center">
  <a href="https://github.com/s-uryansh/DOM207"><img alt="Course" src="https://img.shields.io/badge/course-DOM207%20%2F%20DOM3007%20%2F%20DOM6401-1F6FEB?style=for-the-badge"></a>
  <a href="https://www.python.org/"><img alt="Python 3.11+" src="https://img.shields.io/badge/python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white"></a>
  <a href="MP1/"><img alt="MP1: restaurant analytics" src="https://img.shields.io/badge/MP1-restaurant%20analytics-F39C12?style=for-the-badge"></a>
  <a href="MP3/"><img alt="MP3: country clustering" src="https://img.shields.io/badge/MP3-country%20clustering-8E44AD?style=for-the-badge"></a>
  <a href="MP4/"><img alt="MP4: female labor-force participation" src="https://img.shields.io/badge/MP4-female%20labor-force%20participation-16A085?style=for-the-badge"></a>
  <a href="https://github.com/s-uryansh/DOM207/commits"><img alt="Last commit" src="https://img.shields.io/github/last-commit/s-uryansh/DOM207?style=for-the-badge"></a>
  <a href="https://github.com/s-uryansh/DOM207"><img alt="Top language" src="https://img.shields.io/github/languages/top/s-uryansh/DOM207?style=for-the-badge"></a>
</p>

<p align="center">
  Reproducible coursework for <strong>DOM207 / DOM3007 / DOM6401</strong> — three applied data-analysis projects and the weekly class exercises.
</p>

---

## Contents

- [Projects](#projects)
- [MP1 — Foodie India restaurant analytics](#mp1--foodie-india-restaurant-analytics)
- [MP3 — IMF ICT-worker clustering](#mp3--imf-ict-worker-clustering)
- [MP4 — Female labor-force participation](#mp4--female-labor-force-participation)
- [Class code](#class-code)
- [Repository layout](#repository-layout)
- [Requirements](#requirements)
- [Reproducibility and data handling](#reproducibility-and-data-handling)
- [Academic note](#academic-note)

## Projects

| Folder | Focus | Core methods | Deliverables |
|---|---|---|---|
| [`MP1/`](MP1/) | Restaurant transaction analysis for Foodie India | Cleaning, descriptive summaries, hypothesis tests, post-hoc and sensitivity analysis | Landscape PDF report, 17 CSV result tables, 4 figures, automated verification |
| [`MP3/`](MP3/) | IMF consulting study: grouping 37 countries by ICT-worker issues | Standardization, PCA, Ward/average hierarchical clustering, k-means, GMM, silhouette and bootstrap stability | Reproducible `analysis.py`, formal `report.docx` |
| [`MP4/`](MP4/) | Government of India study: factors associated with female labor-force participation | Logit and probit maximum-likelihood estimation, average marginal effects, stratified five-fold cross-validation, sensitivity and influence diagnostics | Reproducible `analysis.py`, IEEE conference `Report.tex`, 4 figures |
| [`class_codes/`](class_codes/) | Weekly tutorial and participation work | OLS regression and applied statistics exercises | Analysis scripts and read-only datasets |

## MP1 — Foodie India restaurant analytics

MP1 turns 365 restaurant transactions into a traceable management report. It examines bill amounts, service periods, party sizes, per-head spending, tipping patterns, data-quality issues, and weekday/weekend differences, then translates the evidence into controlled and reversible operating pilots.

### Run it

```bash
cd MP1
./run.sh
```

The launcher creates a project-local `.venv`, installs the pinned packages, runs the analysis, and verifies the results. The first run may take a few minutes. A successful run prints a line beginning with `PASS`.

### What you get

- `MP1/Foodie_India_MP1_Report.pdf` — final six-section report;
- `MP1/outputs/` — cleaned data, summaries, and test results;
- `MP1/outputs/figures/` — the four decision figures.

The original `Restaurant.xlsx` is never modified; the pipeline preserves a `SourceRow` link for every cleaned record and `verify.py` checks the workbook hash and all 365 source rows.

### Developer commands

```bash
cd MP1
python analysis.py
python verify.py
```

### Documentation

- [`MP1/README.md`](MP1/README.md) — quick start and project structure;
- [`MP1/Docs/PROJECT.md`](MP1/Docs/PROJECT.md) — end-to-end workflow and findings;
- [`MP1/Docs/ANALYSIS.md`](MP1/Docs/ANALYSIS.md) — cleaning and statistical methods;
- [`MP1/Docs/VERIFICATION.md`](MP1/Docs/VERIFICATION.md) — every automated check.

## MP3 — IMF ICT-worker clustering

MP3 is a consulting study for the IMF. It groups 37 countries on nine ICT-worker issues using two scores per issue (18 features), compares clustering on Score A, Score B, and both scores combined, and tests whether the resulting country groups are stable and interpretable.

The analysis deliberately reports its limits: the sample is small, the score construction is not fully known, k-means assumes roughly spherical clusters, and cluster labels are arbitrary across runs.

### Run it

```bash
cd MP3
python analysis.py
```

The script prints the full evidence trail: correlations, outlier counts, PCA variance, multicollinearity checks, silhouette and elbow results, cross-method agreement (ARI), bootstrap stability, final cluster membership, regional composition, and borderline countries. Dendrograms are rendered to a temporary directory for inspection.

### Dependencies

MP3 intentionally has no pinned requirements file. The script uses the following stack:

```bash
python -m pip install pandas numpy openpyxl scipy scikit-learn matplotlib seaborn
```

### Inputs and deliverables

- `MP3/dataset/ICTIndiv.xlsx` — country scores (read-only);
- `MP3/dataset/ICTInvFldDesc.pdf` — field and issue definitions;
- `MP3/task.pdf` — assignment brief;
- `MP3/analysis.py` — reproducible analysis;
- `MP3/report.docx` — formal client report.

## MP4 — Female labor-force participation

MP4 is a Government of India study that estimates which observed characteristics are associated with women's participation in the job market. It turns 753 records from `IWomenJob.xlsx` into a prespecified logistic model, average marginal effects, out-of-fold validation, and a set of sensitivity and influence diagnostics, then translates the evidence into recommendations the client can act on.

### Run it

```bash
cd MP4
python analysis.py
```

The script prints the full evidence trail: data checks, descriptive statistics, full logit coefficients, average marginal effects, probit and linear-probability comparisons, block likelihood-ratio tests, fit and cross-validation summaries, sensitivity coefficients, multicollinearity (VIF) diagnostics, influence and leave-one-out checks, and the four figures. The figures are written to `MP4/figures/`.

### What you get

- `MP4/analysis.py` — single-file, reproducible analysis;
- `MP4/Report.tex` — IEEE conference-format report source;
- `MP4/report.pdf` — compiled report (reference artifact);
- `MP4/figures/` — participation, predictor-profile, interaction, and ROC/calibration figures.

The original `IWomenJob.xlsx` is never modified. The script recomputes `nwifeinc` from `faminc`, `sal`, and `hours`, and reports the maximum absolute difference against the supplied column (within the $10^{-4}$ comparison tolerance).

### Dependencies

MP4 intentionally has no pinned requirements file. The script uses the following stack:

```bash
python -m pip install pandas numpy openpyxl scipy scikit-learn matplotlib statsmodels
```

### Documentation

- [`MP4/AGENTS.md`](MP4/AGENTS.md) — assignment instructions and report-writing conventions;
- [`MP4/MP4Specs.pdf`](MP4/MP4Specs.pdf) — the project specification;
- [`MP4/reference/IEEE.tex`](MP4/reference/IEEE.tex) — the IEEE report structure reference.

## Class code

### GPA determinants

`class_codes/Class Participation/gpa_determinants.py` fits an OLS model of university GPA against high-school GPA, admission score, missed lectures, club membership, and parental education using `SNUPerf.xlsx`.

```bash
cd "class_codes/Class Participation"
python gpa_determinants.py
```

Requires `pandas`, `statsmodels`, and `openpyxl`.

### Tutorial datasets

`class_codes/Tutorial/Dataset/` contains the datasets used in class:

| File | Contents |
|---|---|
| `CompanyAge.txt` | Company age observations |
| `MonSales.txt` | Monthly sales data |
| `Production.csv` | Production data |
| `StartupMonth.txt` | Startup-month observations |

## Repository layout

```text
DOM207/
├── README.md
├── MP1/
│   ├── analysis.py              # Compatibility entry point
│   ├── foodie_india/            # Cleaning, summaries, tests, figures, pipeline
│   ├── Docs/                    # Project, analysis, and verification notes
│   ├── outputs/                 # Generated CSV tables and figures
│   ├── Restaurant.xlsx          # Immutable source workbook
│   ├── Foodie_India_MP1_Report.pdf
│   ├── run.sh                   # One-command setup, analysis, verification
│   └── verify.py                # Acceptance checks
├── MP3/
│   ├── analysis.py              # Full clustering analysis
│   ├── dataset/                 # Immutable source data and field descriptions
│   ├── report.docx              # Formal client report
│   └── task.pdf                 # Assignment brief
├── MP4/
│   ├── analysis.py              # Full participation analysis
│   ├── IWomenJob.xlsx           # Immutable source workbook
│   ├── Report.tex               # IEEE conference report source
│   ├── report.pdf               # Compiled report (reference artifact)
│   ├── figures/                 # Generated figures
│   ├── reference/               # IEEE report structure reference
│   └── MP4Specs.pdf             # Assignment specification
└── class_codes/
    ├── Class Participation/     # GPA regression exercise and dataset
    └── Tutorial/                # Tutorial datasets
```

## Requirements

| Part | Python | Setup |
|---|---|---|
| MP1 | Python 3 | `./run.sh` creates `.venv` and installs `requirements.txt` |
| MP3 | Python 3.11+ | Install the packages listed above |
| MP4 | Python 3.11+ | Install the packages listed above |
| Class code | Python 3 | Install `pandas`, `statsmodels`, and `openpyxl` |

MP1 ships a `.gitignore` covering virtual environments, caches, and local editor files.

## Reproducibility and data handling

- Source workbooks are treated as immutable: `MP1/Restaurant.xlsx`, `MP3/dataset/ICTIndiv.xlsx`, and `MP4/IWomenJob.xlsx` are only read.
- MP1 verifies the source hash, row count, anomaly flags, generated artifacts, and report content.
- MP3 fixes `random_state=42`, compares multiple clustering methods, and reports stability and sensitivity instead of presenting one fragile solution.
- MP4 fixes `random_state=2026`, recomputes `nwifeinc` from the raw inputs and reports the residual against the supplied column, and reports out-of-fold AUC, block likelihood-ratio tests, sensitivity coefficients, VIF diagnostics, and leave-one-out influence instead of presenting one fragile solution.
- Generated outputs are committed for review; rerunning the scripts regenerates them.
- No credentials, secrets, or external services are required.

## Academic note

This repository contains coursework for DOM207 / DOM3007 / DOM6401. It is shared for reference and reproducibility. If you are taking the course, please submit your own work.
