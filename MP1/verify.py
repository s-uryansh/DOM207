import hashlib
import struct
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import pandas as pd
import pdfplumber
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "outputs"
SOURCE_SHA256 = "889165c20c3e18d685418332a874cf3c88a88299892e97d755ca6cf2d20483c1"


def rounded(value):
    return str(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def displayed_p(value):
    return f"{value:.2e}" if value < .001 else f"{value:.3f}"


def png_width(path):
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", data[16:24])[0]


def components(colour):
    if colour is None:
        return None
    if isinstance(colour, (int, float)):
        return (float(colour),)
    return tuple(float(value) for value in colour)


def is_black(colour):
    values = components(colour)
    return values is None or all(abs(value) < 1e-6 for value in values)


def is_white(colour):
    values = components(colour)
    return values is None or all(abs(value - 1) < 1e-6 for value in values)


def inside_image(item, images):
    return any(
        item["x0"] >= image["x0"] - 1
        and item["x1"] <= image["x1"] + 1
        and item["top"] >= image["top"] - 1
        and item["bottom"] <= image["bottom"] + 1
        for image in images
    )


def main():
    source_path = ROOT / "Restaurant.xlsx"
    assert hashlib.sha256(source_path.read_bytes()).hexdigest() == SOURCE_SHA256

    source = pd.read_excel(source_path, sheet_name="Serve", usecols="A:G")
    clean = pd.read_csv(OUTPUT / "cleaned_restaurant.csv")
    primary = pd.read_csv(OUTPUT / "hypothesis_tests.csv")
    context = pd.read_csv(OUTPUT / "context_tests.csv")
    sensitivity = pd.read_csv(OUTPUT / "sensitivity.csv")
    tip_robustness = pd.read_csv(OUTPUT / "tip_rate_robustness.csv")

    assert len(source) == len(clean) == 365
    assert clean["SourceRow"].tolist() == list(range(2, len(source) + 2))
    assert clean["SourceRow"].is_unique
    assert int(clean["AnalysisReady"].sum()) == 362

    duplicate_rows = clean.loc[clean["DuplicateBlock"], "SourceRow"].astype(int).tolist()
    assert duplicate_rows == list(range(303, 311))
    assert clean.loc[clean["TipSuspect"], "SourceRow"].astype(int).tolist() == [296]
    expected_tip_errors = clean["AnalysisReady"] & clean["Tip"].gt(3 * clean["Amount"])
    assert clean["TipEntryError"].astype(bool).equals(expected_tip_errors)
    assert int(clean["TipEntryError"].sum()) == 3
    tip_errors = clean.loc[clean["TipEntryError"], ["SourceRow", "Tip"]]
    assert set(tip_errors["SourceRow"].astype(int)) == {91, 105, 232}
    assert tip_errors["Tip"].min() >= 288
    per_head_rows = clean["AnalysisReady"].astype(bool) & clean["CorePartySize"].astype(bool)
    assert clean.loc[per_head_rows, "PerHead"].notna().all()

    expected_primary = {f"H{number}" for number in range(1, 9)}
    assert set(primary["Hypothesis"]) == expected_primary
    assert primary["Decision"].tolist() == [
        "Reject H0" if value < .05 else "Do not reject H0"
        for value in primary["AdjustedP"]
    ]
    rejected = set(primary.loc[primary["AdjustedP"].lt(.05), "Hypothesis"])
    assert rejected == {"H1", "H3", "H4", "H5"}
    assert set(context["Hypothesis"]) == {f"C{number}" for number in range(1, 8)}
    assert context["Decision"].tolist() == [
        "Reject H0" if value < .05 else "Do not reject H0"
        for value in context["AdjustedP"]
    ]

    indexed_primary = primary.set_index("Hypothesis")
    indexed_context = context.set_index("Hypothesis")
    assert indexed_primary.loc["H1", "RawP"] < .0001
    assert indexed_primary.loc["H2", "RawP"] > .05
    assert indexed_primary.loc["H3", "RawP"] < .0001
    assert indexed_primary.loc["H4", "Effect"] < 0
    assert indexed_primary.loc["H5", "Effect"] < 0
    assert (indexed_primary.loc[["H6", "H7", "H8"], "AdjustedP"] > .05).all()
    assert indexed_context.loc["C5", "AdjustedP"] > .05
    assert set(sensitivity["Scenario"]) == {
        "Baseline", "Drop DuplicateBlock", "Drop TipEntryError",
        "Drop DuplicateBlock and TipSuspect",
    }
    assert int(sensitivity.loc[sensitivity["Scenario"].eq("Drop DuplicateBlock"), "N"].iloc[0]) == 354
    assert int(sensitivity.loc[
        sensitivity["Scenario"].eq("Drop DuplicateBlock and TipSuspect"), "N"
    ].iloc[0]) == 353
    capped = tip_robustness.loc[tip_robustness["Scenario"].eq("Tip rate at or below 100%")].iloc[0]
    assert int(capped["N"]) == 355 and capped["TipRateBillRho"] < 0 and capped["RawP"] < .05

    expected_outputs = [
        "cleaned_restaurant.csv", "data_quality.csv", "day_summary.csv",
        "time_summary.csv", "party_summary.csv", "day_time_summary.csv",
        "day_service_mix.csv", "tip_rate_quartile_summary.csv",
        "lunch_contrast_summary.csv", "duplicate_audit.csv",
        "hypothesis_tests.csv", "context_tests.csv", "day_posthoc_tests.csv",
        "sensitivity.csv", "tip_rate_robustness.csv", "tip_rate_context.csv",
        "figure_disclosures.csv",
    ]
    assert all((OUTPUT / name).stat().st_size > 0 for name in expected_outputs)
    assert not pd.read_csv(OUTPUT / "tip_rate_context.csv").empty
    figure_names = [
        "bill_distributions.png", "segment_matrix.png",
        "party_opportunity.png", "amount_tip_relationship.png",
    ]
    for name in figure_names:
        figure = OUTPUT / "figures" / name
        assert figure.stat().st_size > 20_000
        assert png_width(figure) >= 1_400

    pdf_path = ROOT / "Foodie_India_MP1_Report.pdf"
    reader = PdfReader(pdf_path)
    report_text = "\n".join(page.extract_text() for page in reader.pages)
    report_flat = " ".join(report_text.split())
    sections = [
        "Section: Introduction",
        "Section: Data (pre)processing",
        "Section: Data visualization",
        "Section: Analysis",
        "Section: Discussions and Recommendations",
        "Section: References",
    ]
    positions = [report_text.index(section) for section in sections]
    assert positions == sorted(positions)
    for identity in ["2310110038", "Anant Atreya", "2310110314", "Suryansh Rohil"]:
        assert identity in report_text
    assert "DOM207-DOM3007-DOM6401: MP1" in report_text
    assert all(float(page.mediabox.width) < float(page.mediabox.height) for page in reader.pages)
    assert all(
        abs(float(page.mediabox.width) - 612) < .01
        and abs(float(page.mediabox.height) - 792) < .01
        for page in reader.pages
    )
    assert "n=351" in report_flat and "n=347" in report_flat
    assert "the two bases differ because 4 valid-Day rows" in report_flat
    assert "flat-dollar" in report_flat
    assert "Party size may include children or shared dishes; per-head spend is an" in report_flat
    assert "approximation of per-diner spend." in report_flat
    assert "injected" not in report_flat.lower()

    within_lunch = report_text.index("lunch days differ")
    within_dinner = report_text.index("dinner days do not")
    pooled_interpretation = report_text.index("former pooled Thursday-Sunday interpretation")
    assert within_lunch < within_dinner < pooled_interpretation
    assert "Sunday bill-building" not in report_text
    for number in range(1, 10):
        assert report_text.count(f"[{number}]") >= 2

    lunch = pd.read_csv(OUTPUT / "lunch_contrast_summary.csv")
    party = pd.read_csv(OUTPUT / "party_summary.csv")
    weekend = lunch.loc[lunch["DayGroup"].eq("Weekend (Sat+Sun)")].iloc[0]
    weekday = lunch.loc[lunch["DayGroup"].eq("Weekday (Thur+Fri)")].iloc[0]
    two = party.loc[party["Partysize"].eq(2), "PerHeadMedian"].iloc[0]
    four = party.loc[party["Partysize"].eq(4), "PerHeadMedian"].iloc[0]
    for expected_text in [
        f"median bill {weekend['BillMedian']:.2f}",
        f"versus {weekday['BillMedian']:.2f}",
        f"median per-head spend is {rounded(two)}",
        f"and {rounded(four)} for four-person parties",
        f"weekend per-head spend has median {rounded(weekend['PerHeadMedian'])}",
    ]:
        assert expected_text in report_flat

    # Output-to-report checks cover all primary statistics, all sensitivity rows,
    # and the core R1/R2 evidence without duplicating analytical constants here.
    for _, row in primary.iterrows():
        assert f"{row['Statistic']:,.3f}" in report_flat
    for _, row in sensitivity.iterrows():
        assert row["Scenario"] in report_flat
        assert displayed_p(row["DayRawP"]) in report_flat
        assert f"{row['BillTipRho']:.3f}" in report_flat
        assert f"{row['TipRateBillRho']:.3f}" in report_flat
    day_time = pd.read_csv(OUTPUT / "day_time_summary.csv")
    thursday_lunch = day_time[
        day_time["Day"].eq("Thur") & day_time["Time"].eq("Lunch")
    ].iloc[0]
    for evidence in [
        f"median bill {weekend['BillMedian']:.2f}",
        f"median per-head spend ({rounded(weekend['PerHeadMedian'])}",
        f"largest lunch cell (n={int(thursday_lunch['Transactions'])})",
        f"per-head median ({rounded(thursday_lunch['PerHeadMedian'])}",
    ]:
        assert evidence in report_flat

    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            for char in page.chars:
                if not inside_image(char, page.images) and not is_black(char.get("non_stroking_color")):
                    raise AssertionError(
                        f"Page {page_number}: coloured text {char.get('non_stroking_color')}"
                    )
            for rectangle in page.rects:
                if (
                    rectangle.get("fill")
                    and not inside_image(rectangle, page.images)
                    and not is_white(rectangle.get("non_stroking_color"))
                ):
                    raise AssertionError(
                        f"Page {page_number}: non-white filled rectangle "
                        f"{rectangle.get('non_stroking_color')}"
                    )

    print(
        f"PASS: unchanged source, {len(clean)} preserved rows, revised tests, "
        f"figures, outputs, and {len(reader.pages)} portrait PDF pages verified."
    )


if __name__ == "__main__":
    main()
