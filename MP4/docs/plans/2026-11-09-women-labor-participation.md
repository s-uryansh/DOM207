# Women’s Labor-Force Participation Implementation Plan

> **For agentic workers:** Use this plan task by task. Checkboxes track completion.

**Goal:** Complete the specified participation analysis in one Python script and rewrite `Report.tex` from its computed results.

**Architecture:** `analysis.py` will load and validate the supplied workbook, fit the prespecified models, print results, and save figures in `figures/`. `Report.tex` will present the model, evidence, limitations, and findings without changing the workbook or `report.pdf`.

**Tech Stack:** Python, pandas, numpy, statsmodels, scikit-learn, matplotlib, openpyxl, LaTeX.

---

## File map

- Create `analysis.py`: the single analysis program, including data checks, model fitting, diagnostics, plots, and printed tables.
- Modify `Report.tex`: the client report with all required headings and references.
- Generate `figures/participation.png`, `figures/profiles.png`, `figures/interaction.png`, and `figures/roc_calibration.png` from the script.
- Keep the approved design at `docs/specs/2026-11-09-women-labor-participation-design.md` as the analysis contract. Do not create a separate test module or alter `IWomenJob.xlsx` or `report.pdf`.

## Task 1: Data loading and checks

Create `load_data(path)` in `analysis.py`. Read sheet `IWomenJob`, require the documented 20 columns and 753 rows, coerce `sal` values `.` to missing, and verify `inlf` and `city` are binary. Confirm the salary placeholders occur only where `inlf == 0`, then use zero for those values only in the required formula. Recompute `nwifeinc`, compare all rows with the supplied column using absolute tolerance `1e-4`, and retain the supplied column separately for the comparison. Reject missing values in model fields and print counts and range checks.

Check the loader with:

```bash
python3 -c 'import analysis as a; d, q = a.load_data("IWomenJob.xlsx"); assert len(d) == 753; assert d.inlf.sum() == 428; assert d.inlf.eq(0).sum() == 325; assert q <= 1e-4'
```

Expected: exit status 0 and the stated row and outcome counts.

## Task 2: Design matrices and prespecified models

Create `make_design(d, centers=None)` to center `age`, `exper`, `ed`, and `nwifeinc`, then construct `age_sq`, `exper_sq`, `kid_income`, and `ed_city`. Scale `mtr` so one model unit represents a 10 percentage-point increase. Return nested linear, quadratic, and full design matrices. The full matrix has 13 slope terms: `kidslt6`, `kidsge6`, `age_c`, `age_sq`, `ed_c`, `exper_c`, `exper_sq`, `nwifeinc_c`, `mtr`, `unem`, `city`, `kid_income`, and `ed_city`.

Fit full-sample logit and probit with statsmodels. Test the quadratic and interaction blocks with nested likelihood-ratio tests. Report average marginal effects and predicted probability contrasts. Check centered design columns for expected values and dimensions with:

```bash
python3 -c 'import analysis as a; d, _ = a.load_data("IWomenJob.xlsx"); x = a.make_design(d); assert x["full"].shape == (753, 14); assert x["full"].columns[0] == "const"'
```

The 14 columns include the intercept. Fit the HC3 linear-probability model and report the share of fitted values below zero or above one.

## Task 3: Sensitivity analyses and diagnostics

Fit the prespecified alternatives: omit `mtr`; substitute `faminc` for `nwifeinc` and its interaction; add `husage`, `hused`, and `hushrs`; add `momed` and `daded`; and treat `kidslt6` as categories when cells permit. Never place `faminc` and `nwifeinc` together. Print VIFs and the pairwise `mtr` to `nwifeinc` correlation.

Report sparse `kidslt6` by `city` cells, logit convergence and separation checks, leverage and influence measures, and leave-one-record checks for interaction effects. Calculate in-sample calibration and ROC AUC. Use stratified five-fold out-of-fold predictions with a fixed seed for cross-validated AUC and calibration. Keep fold centering based on training rows only. Compare coefficient signs and probability-scale effects across the main, probit, LPM, and sensitivity fits.

## Task 4: Figures and printed results

Save the four planned figures under `figures/`. Use predicted probabilities for the interaction plot and out-of-fold predictions for ROC and calibration plots. Print data checks, variable inclusion reasons, model tables, LR tests, marginal effects, diagnostic values, sensitivity contrasts, and the exact figure paths. Run `python3 analysis.py` from this directory and retain its output for report writing.

## Task 5: Report and verification

Rewrite `Report.tex` after the output is reviewed. Include the title page, abstract, and required sections: Introduction, Data preprocessing, Data visualization, Hypotheses or theory building, Analysis, Recommendations, and References. Cite each figure and report the recalculated `nwifeinc` comparison, its construction caveat, all named sensitivity models, cross-validated AUC, LPM out-of-range rate, influence checks, events per slope, and data provenance limits. Tie each recommendation to its estimated marginal effect and sensitivity result. Do not claim intervention effects.

Run:

```bash
python3 -m py_compile analysis.py
python3 analysis.py
pdflatex -output-directory=/tmp/opencode Report.tex
```

Expected: the script completes, all four figures exist, and LaTeX compiles in `/tmp/opencode`. Confirm `report.pdf` remains unchanged and every `\\includegraphics` path exists. Do not commit or compile into the project directory unless requested.
