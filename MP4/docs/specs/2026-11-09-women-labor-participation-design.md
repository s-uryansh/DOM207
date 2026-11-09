# Women’s Labor-Force Participation Analysis

## Objective

Estimate which observed household, human-capital, and local-labor-market characteristics are associated with the binary participation indicator in the supplied client workbook. The report will use the Government of India consulting scenario specified in the assignment. It will describe the 753 supplied records and will not claim causal effects or population representativeness beyond what the documentation establishes.

## Data and preprocessing

- Read the `IWomenJob` sheet from `IWomenJob.xlsx`. Do not alter the workbook or add observations.
- Validate row count, column names, binary coding of `inlf` and `city`, missing values, predictor ranges, and basic logical consistency.
- Treat `.` in `sal` as structurally unavailable for nonparticipants. Do not enter `sal` or `hours` directly as participation predictors because they are defined by the employment decision. Exclude `repsal` because it is a reported wage at the 2020 interview, after the 2019 participation reference period.
- Recompute `nwifeinc = (faminc - sal * hours) / 1000`, substituting zero for unavailable `sal` only where `hours` is zero. Compare the recalculated values with the supplied field for all 753 rows using a stated floating-point tolerance. Retain the source values and report any discrepancies.
- Explain that `nwifeinc` is intended to measure household income other than the woman's own earnings. Its construction is not independent of participation: nonparticipants have zero hours and unavailable salary, so their value equals `faminc / 1000`; participants have estimated own earnings subtracted. Treat its coefficient as an adjusted association, not a clean causal income effect.
- Do not remove observations solely because they are extreme. Report influence checks and sensitivity fits before drawing conclusions.

## Hypotheses fixed before model fitting

1. Each additional child under six is associated with lower participation. The `kidslt6` count is linear in the primary model. A positive `kidslt6` by `nwifeinc` interaction is expected if additional household resources soften the care-cost constraint; the marginal effect of the count will be reported at representative income values.
2. Higher `nwifeinc` is associated with lower participation through an income effect, under the labor-supply model in which leisure is a normal good. The data and construction do not identify this effect causally.
3. Education and actual labor-market experience are associated with higher participation. Experience may have a concave association as accumulated human capital rises at a decreasing rate or depreciates during time away from work.
4. The education association may be stronger in city residence, where the mix and availability of paid work can differ. The education by city interaction tests that difference.
5. Age enters quadratically because participation can vary over the life cycle as family responsibilities, health, and retirement proximity change. The quadratic describes curvature over the observed ages, not a universal life-cycle pattern.

These directional hypotheses and model blocks will be fixed before fitting outcome models. All findings will be described as associations.

## Model strategy

Use logit as the primary model because `inlf` is binary. The prespecified main-effects model includes `kidslt6`, `kidsge6`, centered age and its square, education, centered experience and its square, `nwifeinc`, `mtr`, `unem`, and `city`. The full model adds `kidslt6` by `nwifeinc` and education by `city`. Center age, experience, education, and `nwifeinc` before constructing powers or products. Report likelihood-ratio tests for the quadratic and interaction blocks. Keep the prespecified full model as the main model regardless of individual p-values, and report average marginal effects and predicted probabilities alongside logit coefficients.

The required `nwifeinc` is the primary non-wife income measure. Keep `faminc` out of the primary model because it includes the woman's own earnings for participants. Fit a sensitivity model that substitutes `faminc` for `nwifeinc`, and label it as a construction-sensitive comparison rather than a preferred measure. Do not include `faminc` and `nwifeinc` together.

Keep `mtr` in the primary model as a supplied tax-incentive covariate, scaled so one model unit represents a 10 percentage-point rate increase. Flag that a rate defined for a woman on payroll may be partly determined after participation. Fit a second model without `mtr`, report VIFs for both `mtr` and `nwifeinc` plus their pairwise correlation, and compare the remaining probability-scale effects.

Explain other exclusions in a variable-inclusion table. `hussal` overlaps with household resources represented by `nwifeinc`, so omit it from the main model. Add `husage`, `hused`, and `hushrs` together in a spouse-characteristics sensitivity model; report their VIFs because husband hours also overlap with household resources. `momed` and `daded` are family-background measures that may overlap with the woman's education. Add them together in a family-background sensitivity model rather than omit them without explanation.

Fit probit and linear-probability models as link and outcome-scale checks. Use HC3 standard errors for the linear-probability model and report the share of its fitted values outside [0, 1]. Binary outcomes have variance that depends on the conditional probability; do not treat homoskedastic OLS errors as a suitable primary model.

## Diagnostics and validation

- Report the outcome counts, missingness, structural salary unavailability, cross-tabulation of `kidslt6` by `city`, and agreement of the derived `nwifeinc` with the supplied field. Treat `kidslt6` as a linear count in the primary model and compare it with a categorical count specification if the observed cell counts support that comparison.
- Assess multicollinearity with centered-term VIFs and a predictor correlation matrix, including the `mtr` and `nwifeinc` relationship.
- Check logit convergence and quasi-complete separation, including sparse child-count by city cells. Assess leverage, Pregibon or Cook-type influence measures, and whether deleting any single record materially changes interaction estimates and marginal effects. Report findings rather than presuming no influential record exists.
- Report in-sample calibration and ROC AUC, plus stratified five-fold out-of-fold ROC AUC with a fixed random seed. Do not present in-sample classification accuracy as evidence of predictive validity.
- Use likelihood-ratio tests for prespecified blocks. Compare probability-scale effects across logit, probit, HC3 LPM, and the named sensitivity specifications.
- The primary full model has 13 slope parameters and an intercept. Report the 428 participation cases and 325 nonparticipation cases, with events and non-events per slope parameter. The ratio describes sample size relative to model size but does not establish adequate specification.
- State the data documentation's limits on sampling frame and weights in a professional limitations subsection. Do not characterize the client scenario or workbook as artificial.

## Figures and report

The one analysis script will save figures under `figures/` when run from this project directory. Planned figures are a participation outcome summary, participation profiles for the main predictors, marginal predicted probabilities for the child and non-wife-income interaction, and cross-validated ROC and calibration diagnostics. Retain only figures that help interpret a result.

Rewrite `Report.tex` using the required sections: Introduction, Data preprocessing, Data visualization, Hypotheses or theory building, Analysis, Recommendations, and References. Answer directly what `nwifeinc` measures, why its construction matters, how its estimate changes the interpretation, and how the `faminc` sensitivity model differs. Include a title page with the supplied students, roll numbers, course, and instructor information already present in the report template.

Recommendations must cite the estimated marginal effects and relevant sensitivity results. Childcare or early-childhood support recommendations require a negative child-count association that remains in the specified checks. Retraining recommendations require evidence of a positive but concave experience association. Urban recommendations require evidence from the city effect or education by city interaction. State that the observational associations do not estimate the effects of those interventions.

## Deliverables and boundaries

- One Python analysis file, with all analysis in that file.
- Updated `Report.tex` and figures generated by the script.
- No changes to the supplied workbook or reference PDF.
- Do not add unrelated data or assert causal effects or representativeness beyond the sample documentation.
