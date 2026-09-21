# How the overall project works

The project turns Foodie India's supplied transaction workbook into traceable analysis, a formal management report, and reversible operating pilots.

## Components

| Component | Purpose |
|---|---|
| `Restaurant.xlsx` | Immutable source workbook |
| `analysis.py` | Small compatibility entry point |
| `foodie_india/` | Cleaning, summaries, tests, figures, configuration, and pipeline modules |
| `outputs/` | Auditable derived data and results |
| `Foodie_India_MP1_Report.pdf` | Final six-section landscape report |
| `verify.py` | Source-integrity, analytical, artifact, and report checks |
| `MP1Specs.pdf` | Assignment requirements |

## End-to-end flow

```text
Restaurant.xlsx
    -> schema validation and row-preserving cleaning
    -> analysis eligibility and anomaly flags
    -> descriptive and service-mix summaries
    -> primary and context test families
    -> post-hoc and sensitivity analyses
    -> four decision figures
    -> formal report interpretation and reversible pilots
    -> verify.py acceptance checks
```

`analysis.py` calls `foodie_india.pipeline`, which coordinates the focused modules without changing their processing order. No module writes to the workbook. Every cleaned row keeps `SourceRow`, which links it to its Excel row. The final PDF is a reviewed submission artifact; the analysis pipeline regenerates all supporting CSVs and figures but does not rewrite the PDF.

## Running the project

```bash
./run.sh
```

The launcher creates `.venv`, installs the pinned requirements, runs `analysis.py`, and runs `verify.py`. The original two Python commands remain available for developers.

## How to audit a report claim

- Cleaning counts and treatments: `outputs/data_quality.csv`
- Row-level data and flags: `outputs/cleaned_restaurant.csv`
- Pasted-block comparison: `outputs/duplicate_audit.csv`
- Day/service-period composition: `outputs/day_service_mix.csv`
- Segment and per-head summaries: `outputs/day_summary.csv`, `time_summary.csv`, `party_summary.csv`, and `day_time_summary.csv`
- Weekend/weekday lunch bill, per-head, and party-size comparison: `outputs/lunch_contrast_summary.csv`
- Tip-rate quartiles: `outputs/tip_rate_quartile_summary.csv`
- Eight primary tests: `outputs/hypothesis_tests.csv`
- Seven context tests: `outputs/context_tests.csv`
- Lunch-only day comparisons: `outputs/day_posthoc_tests.csv`
- Duplicate, tip-error, and suspect-tip sensitivities: `outputs/sensitivity.csv`
- Tip-rate cap robustness: `outputs/tip_rate_robustness.csv`
- Tip-rate flat-dollar diagnostics: `outputs/tip_rate_context.csv`
- Figure disclosures: `outputs/figure_disclosures.csv`

## Main findings

The pooled day difference is not interpreted as an independent day effect because lunch share varies from 78.4% on Thursday to 16.0% on Sunday. Day distributions differ within lunch but not within dinner. Weekend lunch has a median bill of 24.67 across 39 observations, compared with 16.27 across 89 Thursday and Friday lunch observations.

Per-head spend has a negative association with party size. Weekend lunch also has higher observed per-head spend than weekday lunch despite a larger mean party size. Tip rate has a negative association with bill amount after three probable decimal-loss tip errors are removed, partly reflecting near-flat dollar tips. No adjusted tip-rate difference is established by waiter gender, smoker status, service period, or day.

## Decision boundary

The report recommends only controlled pilots with a justification, action, success metric, and stop rule. The workbook cannot support causal claims, profit forecasts, return-on-investment estimates, permanent capacity changes, or site selection because it lacks dates, locations, costs, margins, capacity, footfall, and operating exposure.
