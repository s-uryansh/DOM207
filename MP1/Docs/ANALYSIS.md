# How the analysis works

`analysis.py` is the stable command-line entry point. It delegates to the modules in `foodie_india/`, which read `Restaurant.xlsx`, clean a copy in memory, analyze eligible records, and write every supporting result under `outputs/`. The source workbook is never changed.

## 1. Input validation and cleaning

The script reads columns A:G from worksheet `Serve` and requires these fields: `Amount`, `Tip`, `Gender`, `Smoker`, `Day`, `Time`, and `Partysize`. It stops if the schema differs.

The cleaning rules are:

- add `SourceRow` for traceability;
- repair obvious decimal formats and a trailing backtick in monetary fields;
- normalize only unambiguous category variants;
- map `San` and `Sn` to `Sun` while leaving `S`, `SS`, and `SSS` missing;
- mark monetary rows ready only when `Amount > 0` and `Tip >= 0`;
- define core party size as an integer from 1 through 6; and
- calculate `TipRatePct` and `PerHead` only where their inputs are eligible.

All 365 records are preserved in `cleaned_restaurant.csv`; 362 are `AnalysisReady`.

## 2. Anomaly flags

`DuplicateBlock` is true for Excel rows 303-310. These eight records reproduce rows 295-302. Five copied rows are exact, while three differ slightly; the copy is the cleaner version. The original SourceRow 296 contains tip 13.55 and is marked `TipSuspect`, while its copy contains 3.55. Both are retained in the primary analysis and removed only in disclosed sensitivity scenarios. Two unrelated exact pairs occur at Excel rows 198/199 and 254/316.

`TipEntryError` is true when an analysis-ready tip exceeds three times its positive bill. Exactly three tips are flagged: 300, 288, and 3487 on bills near 21-22. They are probable decimal-loss errors and are excluded from the primary bill-versus-tip-rate test. Four additional rates above 100% remain flagged but are not asserted to be errors.

`TipRateSensitivity` identifies valid rates no greater than 100% for robustness review.

## 3. Descriptive outputs

Bill and per-head summaries are produced by day, service period, party size, and day x service period. Separate outputs provide:

- lunch and dinner share by day;
- weekend versus weekday lunch summaries;
- median tip rate by bill quartile;
- pasted-block row comparisons; and
- figure-specific disclosure counts.

The day/service mix is essential: Thursday is 78.4% lunch, whereas Sunday is 16.0% lunch. Pooled day comparisons therefore mix day and service-period effects.

## 4. Statistical test families

All tests are two-sided and use Benjamini-Hochberg adjustment within their disclosed family.

### Primary family: eight tests

| ID | Question | Method |
|---|---|---|
| H1 | Does bill amount differ by day within lunch? | Kruskal-Wallis |
| H2 | Does bill amount differ by day within dinner? | Kruskal-Wallis |
| H3 | Does weekend lunch differ from Thursday and Friday lunch? | Mann-Whitney U |
| H4 | Is party size associated with per-head spend? | Spearman correlation |
| H5 | Is bill amount associated with tip rate after probable errors are removed? | Spearman correlation |
| H6 | Does tip rate differ by waiter gender? | Mann-Whitney U |
| H7 | Does tip rate differ by smoker status? | Mann-Whitney U |
| H8 | Does tip rate differ by service period? | Mann-Whitney U |

H1, H3, H4, and H5 reject their null hypotheses after adjustment. H2 and H6-H8 do not.

### Context family: seven tests

The context family contains the pooled day test, pooled dinner/lunch bill comparison, bill-tip correlation, party-size/bill correlation, tip rate by day, the exploratory two-person versus four-person per-head comparison, and C7: weekend versus weekday lunch per-head spend. C7 also reports the group medians, sample sizes, and mean party sizes in `lunch_contrast_summary.csv`. These provide context and are not treated as standalone causal findings.

Lunch-only pairwise day comparisons are adjusted as a separate post-hoc set. Every test reports epsilon-squared, rank-biserial correlation, or Spearman rho as appropriate.

## 5. Sensitivity analysis

`outputs/sensitivity.csv` re-estimates the pooled day test, bill-tip correlation, and bill-tip-rate correlation for:

- the baseline 362 analysis-ready rows;
- 354 rows after dropping `DuplicateBlock`; and
- 359 rows after dropping `TipEntryError`; and
- 353 rows after dropping both `DuplicateBlock` and `TipSuspect`.

The pooled day result and bill-tip correlation are stable when the copied block is removed. The negative bill-tip-rate relationship is stable after probable tip errors are removed.

`outputs/tip_rate_robustness.csv` separately confirms that the negative bill-tip-rate association remains when analysis is restricted to the 355 rates at or below 100%.

`outputs/tip_rate_context.csv` reports tip rate versus per-head spend, tip rate versus party size, median tip amount, and the share of tips in 0.50 increments. These diagnostics support the report's caveat that the bill-rate decline partly reflects a flat-dollar tipping pattern and does not establish that larger spenders are less generous.

## 6. Figures

- `bill_distributions.png`: pooled day and service-period boxplots with n above each box; plotting outliers are hidden only visually and counted in `figure_disclosures.csv`.
- `segment_matrix.png`: day x service-period median bill heatmap with cell n and luminance-based label contrast.
- `party_opportunity.png`: transaction counts and median per-head spend by party size, a zero-based per-head axis, n labels, and the legend below the plot.
- `amount_tip_relationship.png`: tip rate versus bill on a logarithmic bill axis, excluding the three probable tip errors, capping the visible rate axis at 30%, and showing an eight-bin median trend labeled descriptive only.

The figures do not contain footnote prose. All exclusions and interpretation limits appear in the report captions.

## 7. Interpretation

The analysis supports testing weekend lunch, improving Thursday lunch value per head, and using flexible two-top seating. It does not support a default four-person bundle, demographic tip segmentation, raw-tip staff rankings, causal claims, or permanent expansion decisions.
