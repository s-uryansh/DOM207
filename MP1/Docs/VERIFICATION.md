# How verification works

Run the complete workflow with one command:

```bash
./run.sh
```

For development, `python analysis.py` followed by `python verify.py` performs the same analysis and verification after the environment is installed.

`verify.py` uses assertions and prints `PASS` only after every check succeeds.

## Source integrity and row preservation

The verifier confirms:

- `Restaurant.xlsx` matches the recorded SHA-256 of the original workbook;
- the workbook and cleaned output contain 365 records;
- `SourceRow` is unique and contains Excel rows 2 through 366 in order; and
- 362 records are `AnalysisReady`.

This detects workbook modification and accidental row deletion, duplication, or reordering.

## Cleaning and anomaly flags

The verifier confirms:

- `DuplicateBlock` marks exactly SourceRow 303-310;
- `TipSuspect` marks exactly SourceRow 296;
- `TipEntryError` is equivalent to the implemented positive-bill rule;
- exactly three probable tip errors are flagged at SourceRows 91, 105, and 232, with tips of at least 288; and
- every analysis-ready core-party row has a calculated `PerHead` value.

## Statistical results

The verifier requires primary hypotheses H1-H8 and context tests C1-C7. It recalculates every decision label from the output's adjusted p-value, then confirms the expected primary rejection set: H1, H3, H4, and H5.

It additionally checks the required result directions: lunch days differ, dinner days do not, weekend lunch differs, per-head spend falls with party size, bill-tip-rate association is negative, and the gender, smoker, service-period, and day tip-rate tests remain null after adjustment.

The four required sensitivity scenarios must exist. Dropping the eight-row block must produce n=354, and dropping both that block and `TipSuspect` must produce n=353.
The verifier also confirms that the rate-at-or-below-100% robustness sample has n=355 and retains a statistically significant negative bill-tip-rate association.

## Files and figures

All required CSV outputs, including `tip_rate_context.csv`, must exist and be non-empty. The four required PNG figures must each exceed 20,000 bytes and be at least 1,400 pixels wide.

## Final PDF

The verifier extracts PDF text and confirms:

- the six required sections occur in order;
- both names, both roll numbers, and the course code are present;
- every page is landscape;
- the within-lunch result appears before the within-dinner result and before the former pooled Thursday-Sunday interpretation;
- both day-analysis bases (n=351 and n=347) and their explanation are present;
- the weekend-lunch per-head result, flat-dollar caveat, and party-size caveat match generated outputs;
- all nine references are cited in the report body;
- the removed Sunday bill-building recommendation is absent; and
- key weekend-lunch and per-head numbers match their generated CSV outputs.

Using `pdfplumber`, the verifier also checks that text outside figure image rectangles is black and that filled rectangles outside figures are white. Failures identify the page and offending colour.

## Failure behavior

If an assertion fails, Python stops at the failed check and prints a traceback. Run `python analysis.py` first. If verification still fails, inspect the named source, CSV, figure, or report requirement rather than weakening the assertion.

The verifier checks reproducibility invariants and important output-to-report links. It complements, rather than replaces, manual review of chart legibility and business wording.
