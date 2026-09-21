from .cleaning import load_and_clean
from .config import FIGURES, OUTPUT
from .figures import create_figures
from .statistics import (
    hypothesis_tests,
    sensitivity_results,
    tip_rate_context,
    tip_rate_robustness,
)
from .summaries import describe_segments, duplicate_audit


def main():
    OUTPUT.mkdir(exist_ok=True)
    FIGURES.mkdir(exist_ok=True)
    raw, clean, quality = load_and_clean()
    base = clean[clean["AnalysisReady"]].copy()
    day, time, party, day_time, mix, tip_quartiles, lunch_contrast = describe_segments(base)
    duplicates = duplicate_audit(raw)
    primary, context, posthoc = hypothesis_tests(base)
    sensitivity = sensitivity_results(base)
    tip_robustness = tip_rate_robustness(base)
    tip_context = tip_rate_context(base)
    disclosures = create_figures(base, party, day_time)

    exports = [
        ("cleaned_restaurant.csv", clean, False),
        ("data_quality.csv", quality, False),
        ("day_summary.csv", day, True),
        ("time_summary.csv", time, True),
        ("party_summary.csv", party, True),
        ("day_time_summary.csv", day_time, False),
        ("day_service_mix.csv", mix, False),
        ("tip_rate_quartile_summary.csv", tip_quartiles, False),
        ("lunch_contrast_summary.csv", lunch_contrast, True),
        ("duplicate_audit.csv", duplicates, False),
        ("hypothesis_tests.csv", primary, False),
        ("context_tests.csv", context, False),
        ("day_posthoc_tests.csv", posthoc, False),
        ("sensitivity.csv", sensitivity, False),
        ("tip_rate_robustness.csv", tip_robustness, False),
        ("tip_rate_context.csv", tip_context, False),
        ("figure_disclosures.csv", disclosures, False),
    ]
    for filename, frame, include_index in exports:
        frame.to_csv(OUTPUT / filename, index=include_index)
    print(f"Generated analysis outputs from {len(raw)} source records; {len(base)} are analysis-ready.")
