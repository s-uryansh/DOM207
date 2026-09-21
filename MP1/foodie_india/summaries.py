import numpy as np
import pandas as pd

from .config import DAY_ORDER, TIME_ORDER


def segment_summary(base, group_columns):
    grouped = base.groupby(group_columns, observed=True)
    summary = grouped["Amount"].agg(
        Transactions="size",
        BillMedian="median",
        BillQ1=lambda values: values.quantile(.25),
        BillQ3=lambda values: values.quantile(.75),
        ObservedBillAmount="sum",
    )
    per_head = grouped["PerHead"].agg(PerHeadN="count", PerHeadMedian="median")
    return summary.join(per_head)


def describe_segments(base):
    day = segment_summary(base.dropna(subset=["Day"]), "Day").reindex(DAY_ORDER)
    time = segment_summary(base.dropna(subset=["Time"]), "Time").reindex(TIME_ORDER)
    party = segment_summary(base[base["CorePartySize"]], "Partysize")
    day_time = segment_summary(base.dropna(subset=["Day", "Time"]), ["Day", "Time"]).reset_index()

    counts = pd.crosstab(base["Day"], base["Time"]).reindex(index=DAY_ORDER, columns=TIME_ORDER, fill_value=0)
    mix = pd.DataFrame({
        "Day": DAY_ORDER,
        "Transactions": counts.sum(axis=1).to_numpy(),
        "LunchN": counts["Lunch"].to_numpy(),
        "DinnerN": counts["Dinner"].to_numpy(),
    })
    mix["LunchSharePct"] = 100 * mix["LunchN"] / mix["Transactions"]

    tip_base = base[~base["TipEntryError"]].copy()
    tip_base["BillQuartile"] = pd.qcut(
        tip_base["Amount"],
        4,
        labels=["Q1 (lowest)", "Q2", "Q3", "Q4 (highest)"],
    )
    tip_quartiles = tip_base.groupby("BillQuartile", observed=True).agg(
        Transactions=("TipRatePct", "size"),
        BillMinimum=("Amount", "min"),
        BillMaximum=("Amount", "max"),
        BillMedian=("Amount", "median"),
        TipRateMedianPct=("TipRatePct", "median"),
        TipRateQ1Pct=("TipRatePct", lambda values: values.quantile(.25)),
        TipRateQ3Pct=("TipRatePct", lambda values: values.quantile(.75)),
    ).reset_index()

    lunch = base[base["Time"].eq("Lunch")].copy()
    lunch["DayGroup"] = np.where(lunch["Day"].isin(["Sat", "Sun"]), "Weekend (Sat+Sun)", np.where(lunch["Day"].isin(["Thur", "Fri"]), "Weekday (Thur+Fri)", pd.NA))
    lunch_valid = lunch.dropna(subset=["DayGroup"])
    lunch_contrast = lunch_valid.groupby("DayGroup", observed=True)["Amount"].agg(
        Transactions="size",
        BillMedian="median",
        BillQ1=lambda values: values.quantile(.25),
        BillQ3=lambda values: values.quantile(.75),
    )
    lunch_per_head = lunch_valid[lunch_valid["CorePartySize"]].groupby("DayGroup", observed=True).agg(
        PerHeadN=("PerHead", "size"),
        PerHeadMedian=("PerHead", "median"),
        MeanPartySize=("Partysize", "mean"),
    )
    lunch_contrast = lunch_contrast.join(lunch_per_head).reindex(
        ["Weekend (Sat+Sun)", "Weekday (Thur+Fri)"]
    )
    return day, time, party, day_time, mix, tip_quartiles, lunch_contrast


def duplicate_audit(raw):
    indexed = raw.copy()
    indexed.insert(0, "SourceRow", np.arange(2, len(indexed) + 2))
    rows = []
    for original_row, copy_row in zip(range(295, 303), range(303, 311)):
        original = indexed.loc[indexed["SourceRow"].eq(original_row)].iloc[0]
        copied = indexed.loc[indexed["SourceRow"].eq(copy_row)].iloc[0]
        differences = []
        for column in raw.columns:
            if str(original[column]) != str(copied[column]):
                differences.append(f"{column} {original[column]} -> {copied[column]}")
        wording = "Copy differs: " + "; ".join(differences) if differences else "Exact copy"
        rows.append(["Pasted block", original_row, copy_row, wording])

    duplicate_rows = indexed[indexed[raw.columns].duplicated(keep=False)]
    for _, group in duplicate_rows.groupby(list(raw.columns), dropna=False, sort=False):
        source_rows = group["SourceRow"].tolist()
        if not set(source_rows).issubset(set(range(295, 311))):
            rows.append(["Other exact pair", source_rows[0], source_rows[1], "Exact copy"])
    return pd.DataFrame(rows, columns=["Type", "OriginalSourceRow", "CopySourceRow", "Differences"])
