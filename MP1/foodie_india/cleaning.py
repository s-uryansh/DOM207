import numpy as np
import pandas as pd

from .config import DAY_ORDER, ROOT, TIME_ORDER


def parse_numeric(series):
    cleaned = series.astype("string").str.strip().str.replace("`", "", regex=False)
    cleaned = cleaned.str.replace(r"(?<=\d)[,-](?=\d{2}$)", ".", regex=True)
    return pd.to_numeric(cleaned, errors="coerce")


def load_and_clean():
    raw = pd.read_excel(ROOT / "Restaurant.xlsx", sheet_name="Serve", usecols="A:G")
    expected = ["Amount", "Tip", "Gender", "Smoker", "Day", "Time", "Partysize"]
    if list(raw.columns) != expected:
        raise ValueError(f"Unexpected workbook columns: {list(raw.columns)}")

    clean = raw.copy()
    clean.insert(0, "SourceRow", np.arange(2, len(clean) + 2))
    for column in ["Amount", "Tip"]:
        clean[column] = parse_numeric(clean[column])

    mappings = {
        "Gender": {
            "M": "Male", "Mal": "Male", "Mle": "Male", "F": "Female", "Fe": "Female",
            "Fmle": "Female", "Femle": "Female", "Fem": "Female",
        },
        "Smoker": {"N": "No", "Y": "Yes", "s": "Yes"},
        "Day": {
            "Thurs": "Thur", "Th": "Thur", "T": "Thur", "Trhurs": "Thur",
            "Saturday": "Sat", "Friday": "Fri", "Ft": "Fri",
            "sun": "Sun", "San": "Sun", "Sn": "Sun",
        },
        "Time": {
            "L": "Lunch", "Lan": "Lunch", "Lu": "Lunch", "Diner": "Dinner",
            "Di": "Dinner", "DD": "Dinner", "DDD": "Dinner", "D": "Dinner",
            "Din": "Dinner", "er": "Dinner",
        },
    }
    valid = {
        "Gender": ["Female", "Male"],
        "Smoker": ["No", "Yes"],
        "Day": DAY_ORDER,
        "Time": TIME_ORDER,
    }
    normalization_counts = {}
    for column, mapping in mappings.items():
        before = clean[column].copy()
        clean[column] = clean[column].replace(mapping)
        normalization_counts[column] = int(
            (before.fillna("<NA>") != clean[column].fillna("<NA>")).sum()
        )
        clean.loc[~clean[column].isin(valid[column]), column] = pd.NA

    clean["AnalysisReady"] = (clean["Amount"].gt(0) & clean["Tip"].ge(0)).fillna(False)
    clean["TipRatePct"] = np.where(
        clean["AnalysisReady"], 100 * clean["Tip"] / clean["Amount"], np.nan
    )
    clean["CorePartySize"] = (
        clean["Partysize"].notna()
        & clean["Partysize"].between(1, 6)
        & clean["Partysize"].mod(1).eq(0)
    ).fillna(False)
    clean["PerHead"] = np.where(
        clean["AnalysisReady"] & clean["CorePartySize"],
        clean["Amount"] / clean["Partysize"],
        np.nan,
    )
    clean["DuplicateBlock"] = clean["SourceRow"].between(303, 310)
    clean["TipSuspect"] = clean["SourceRow"].eq(296)
    clean["TipEntryError"] = (
        clean["AnalysisReady"] & clean["Tip"].gt(3 * clean["Amount"])
    ).fillna(False)
    clean["TipRateSensitivity"] = clean["AnalysisReady"] & clean["TipRatePct"].le(100)

    other_high_rates = (
        clean["AnalysisReady"] & ~clean["TipEntryError"] & clean["TipRatePct"].gt(100)
    )
    sensitivity_n = int((clean["AnalysisReady"] & ~clean["DuplicateBlock"]).sum())
    quality = pd.DataFrame([
        ("Source records", len(raw), "Retained; source workbook unchanged"),
        (
            "Exact duplicate-looking rows (7 exact; 8-row pasted block at Excel rows 303-310)",
            int(raw.duplicated().sum()),
            "All retained; pasted copy flagged as DuplicateBlock",
        ),
        ("Amount text formats repaired", int(raw["Amount"].astype("string").str.contains(r"\d[,-]\d{2}$", na=False).sum()), "Comma/internal hyphen converted to decimal"),
        ("Tip text formats repaired", int(raw["Tip"].astype("string").str.contains("`", regex=False, na=False).sum()), "Trailing backtick removed"),
        ("Categorical values normalized", sum(normalization_counts.values()), "Only unambiguous variants mapped, including San/Sn to Sun"),
        ("Ambiguous/missing day", int(clean["Day"].isna().sum()), "Excluded only from day analysis"),
        ("Ambiguous/missing time", int(clean["Time"].isna().sum()), "Excluded only from time analysis"),
        ("Ambiguous/missing smoker status", int(clean["Smoker"].isna().sum()), "Excluded only from smoker analysis"),
        ("Non-positive/unparseable amount", int((clean["Amount"].isna() | clean["Amount"].le(0)).sum()), "Excluded from monetary analysis"),
        ("Missing/negative tip", int((clean["Tip"].isna() | clean["Tip"].lt(0)).sum()), "Excluded from tip analysis"),
        ("Analysis-ready amount/tip records", int(clean["AnalysisReady"].sum()), "Primary analytical base"),
        ("Probable tip entry errors", int(clean["TipEntryError"].sum()), "Tip exceeds three times bill; excluded from tip-rate versus bill test"),
        ("Suspect original-block tip", int(clean["TipSuspect"].sum()), "SourceRow 296 has tip 13.55; retained in primary analysis and tested in sensitivity"),
        ("Other flagged tip rates above 100%", int(other_high_rates.sum()), "Retained; flagged but not asserted as errors"),
        ("Core party-size records (1-6)", int((clean["AnalysisReady"] & clean["CorePartySize"]).sum()), "Used for party-size and per-head analysis"),
        ("Pasted-block sensitivity sample", sensitivity_n, "Drops SourceRow 303-310 only; primary conclusions re-estimated"),
    ], columns=["Check", "Records", "Treatment"])
    return raw, clean, quality
