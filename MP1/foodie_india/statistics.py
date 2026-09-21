import numpy as np
import pandas as pd
from scipy import stats

from .config import DAY_ORDER


def rank_biserial(first, second):
    result = stats.mannwhitneyu(first, second, alternative="two-sided", method="asymptotic")
    effect = 2 * result.statistic / (len(first) * len(second)) - 1
    return result.statistic, result.pvalue, effect, len(first) + len(second)


def kruskal_result(groups):
    result = stats.kruskal(*groups)
    n = sum(map(len, groups))
    effect = (result.statistic - len(groups) + 1) / (n - len(groups))
    return result.statistic, result.pvalue, effect, n


def adjust_family(rows, family):
    columns = ["Hypothesis", "Test", "NullHypothesis", "N", "Statistic", "RawP", "Effect", "EffectMeasure"]
    frame = pd.DataFrame(rows, columns=columns)
    frame.insert(0, "Family", family)
    frame["AdjustedP"] = stats.false_discovery_control(frame["RawP"].to_numpy(), method="bh")
    frame["Decision"] = np.where(frame["AdjustedP"] < .05, "Reject H0", "Do not reject H0")
    return frame


def hypothesis_tests(base):
    lunch = base[base["Time"].eq("Lunch")]
    dinner = base[base["Time"].eq("Dinner")]
    lunch_groups = [lunch.loc[lunch["Day"].eq(day), "Amount"].dropna() for day in DAY_ORDER]
    dinner_groups = [dinner.loc[dinner["Day"].eq(day), "Amount"].dropna() for day in DAY_ORDER]
    lunch_kw = kruskal_result(lunch_groups)
    dinner_kw = kruskal_result(dinner_groups)

    weekend_lunch = lunch.loc[lunch["Day"].isin(["Sat", "Sun"]), "Amount"].dropna()
    weekday_lunch = lunch.loc[lunch["Day"].isin(["Thur", "Fri"]), "Amount"].dropna()
    weekend_test = rank_biserial(weekend_lunch, weekday_lunch)

    party_base = base[base["CorePartySize"]]
    party_per_head = stats.spearmanr(party_base["Partysize"], party_base["PerHead"])
    tip_base = base[~base["TipEntryError"]]
    tip_bill = stats.spearmanr(tip_base["Amount"], tip_base["TipRatePct"])

    gender = rank_biserial(
        base.loc[base["Gender"].eq("Female"), "TipRatePct"].dropna(),
        base.loc[base["Gender"].eq("Male"), "TipRatePct"].dropna(),
    )
    smoker = rank_biserial(
        base.loc[base["Smoker"].eq("No"), "TipRatePct"].dropna(),
        base.loc[base["Smoker"].eq("Yes"), "TipRatePct"].dropna(),
    )
    service = rank_biserial(
        base.loc[base["Time"].eq("Lunch"), "TipRatePct"].dropna(),
        base.loc[base["Time"].eq("Dinner"), "TipRatePct"].dropna(),
    )

    primary_rows = [
        ["H1", "Bill amount by day within lunch", "All lunch-day distributions are equal", lunch_kw[3], lunch_kw[0], lunch_kw[1], lunch_kw[2], "Epsilon-squared"],
        ["H2", "Bill amount by day within dinner", "All dinner-day distributions are equal", dinner_kw[3], dinner_kw[0], dinner_kw[1], dinner_kw[2], "Epsilon-squared"],
        ["H3", "Weekend vs weekday lunch bill", "Weekend and weekday lunch distributions are equal", weekend_test[3], weekend_test[0], weekend_test[1], weekend_test[2], "Rank-biserial (Weekend-Weekday)"],
        ["H4", "Party size vs per-head spend", "No monotonic association for party sizes 1-6", len(party_base), party_per_head.statistic, party_per_head.pvalue, party_per_head.statistic, "Spearman rho"],
        ["H5", "Bill amount vs tip rate", "No monotonic association after probable tip errors are removed", len(tip_base), tip_bill.statistic, tip_bill.pvalue, tip_bill.statistic, "Spearman rho"],
        ["H6", "Tip rate by waiter gender", "Female- and male-waiter distributions are equal", gender[3], gender[0], gender[1], gender[2], "Rank-biserial (Female-Male)"],
        ["H7", "Tip rate by smoker status", "No-smoker and smoker distributions are equal", smoker[3], smoker[0], smoker[1], smoker[2], "Rank-biserial (No-Yes)"],
        ["H8", "Tip rate by service period", "Lunch and dinner distributions are equal", service[3], service[0], service[1], service[2], "Rank-biserial (Lunch-Dinner)"],
    ]
    primary = adjust_family(primary_rows, "Primary")

    pooled_day_groups = [base.loc[base["Day"].eq(day), "Amount"].dropna() for day in DAY_ORDER]
    pooled_day = kruskal_result(pooled_day_groups)
    pooled_time = rank_biserial(
        base.loc[base["Time"].eq("Dinner"), "Amount"].dropna(),
        base.loc[base["Time"].eq("Lunch"), "Amount"].dropna(),
    )
    amount_tip = stats.spearmanr(base["Amount"], base["Tip"])
    party_amount = stats.spearmanr(party_base["Partysize"], party_base["Amount"])
    tip_day = kruskal_result([
        base.loc[base["Day"].eq(day), "TipRatePct"].dropna() for day in DAY_ORDER
    ])
    two_four = rank_biserial(
        party_base.loc[party_base["Partysize"].eq(2), "PerHead"],
        party_base.loc[party_base["Partysize"].eq(4), "PerHead"],
    )
    lunch_core = lunch[lunch["CorePartySize"] & lunch["Day"].notna()]
    weekend_per_head = lunch_core.loc[lunch_core["Day"].isin(["Sat", "Sun"]), "PerHead"]
    weekday_per_head = lunch_core.loc[lunch_core["Day"].isin(["Thur", "Fri"]), "PerHead"]
    lunch_per_head = rank_biserial(weekend_per_head, weekday_per_head)
    context_rows = [
        ["C1", "Pooled bill amount by day", "All pooled day distributions are equal", pooled_day[3], pooled_day[0], pooled_day[1], pooled_day[2], "Epsilon-squared"],
        ["C2", "Dinner vs lunch bill amount", "Dinner and lunch distributions are equal", pooled_time[3], pooled_time[0], pooled_time[1], pooled_time[2], "Rank-biserial (Dinner-Lunch)"],
        ["C3", "Bill amount vs tip amount", "No monotonic association", len(base), amount_tip.statistic, amount_tip.pvalue, amount_tip.statistic, "Spearman rho"],
        ["C4", "Party size vs bill amount", "No monotonic association for party sizes 1-6", len(party_base), party_amount.statistic, party_amount.pvalue, party_amount.statistic, "Spearman rho"],
        ["C5", "Tip rate by day", "All day tip-rate distributions are equal", tip_day[3], tip_day[0], tip_day[1], tip_day[2], "Epsilon-squared"],
        ["C6", "Per-head spend: party size 2 vs 4", "Two- and four-person per-head distributions are equal", two_four[3], two_four[0], two_four[1], two_four[2], "Rank-biserial (2-person minus 4-person)"],
        ["C7", "Weekend vs weekday lunch per-head spend", "Weekend and weekday lunch per-head distributions are equal", lunch_per_head[3], lunch_per_head[0], lunch_per_head[1], lunch_per_head[2], "Rank-biserial (Weekend-Weekday)"],
    ]
    context = adjust_family(context_rows, "Context")

    pairs = []
    for index, first in enumerate(DAY_ORDER):
        for second in DAY_ORDER[index + 1:]:
            first_values = lunch.loc[lunch["Day"].eq(first), "Amount"].dropna()
            second_values = lunch.loc[lunch["Day"].eq(second), "Amount"].dropna()
            statistic, pvalue, effect, n = rank_biserial(first_values, second_values)
            pairs.append([f"{first} vs {second}", n, len(first_values), len(second_values), statistic, pvalue, effect])
    posthoc = pd.DataFrame(
        pairs,
        columns=["Comparison", "N", "FirstN", "SecondN", "Statistic", "RawP", "RankBiserial"],
    )
    posthoc["AdjustedP"] = stats.false_discovery_control(posthoc["RawP"].to_numpy(), method="bh")
    posthoc["Decision"] = np.where(posthoc["AdjustedP"] < .05, "Different", "Not established")
    return primary, context, posthoc


def sensitivity_results(base):
    scenarios = {
        "Baseline": base,
        "Drop DuplicateBlock": base[~base["DuplicateBlock"]],
        "Drop TipEntryError": base[~base["TipEntryError"]],
        "Drop DuplicateBlock and TipSuspect": base[~base["DuplicateBlock"] & ~base["TipSuspect"]],
    }
    rows = []
    for name, sample in scenarios.items():
        day_groups = [sample.loc[sample["Day"].eq(day), "Amount"].dropna() for day in DAY_ORDER]
        day = kruskal_result(day_groups)
        bill_tip = stats.spearmanr(sample["Amount"], sample["Tip"])
        tip_rate_bill = stats.spearmanr(sample["Amount"], sample["TipRatePct"])
        rows.append([
            name,
            len(sample),
            day[3], day[0], day[1], day[2],
            len(sample), bill_tip.statistic, bill_tip.pvalue,
            len(sample), tip_rate_bill.statistic, tip_rate_bill.pvalue,
        ])
    return pd.DataFrame(rows, columns=[
        "Scenario", "N", "DayN", "DayStatistic", "DayRawP", "DayEffect",
        "BillTipN", "BillTipRho", "BillTipRawP",
        "TipRateBillN", "TipRateBillRho", "TipRateBillRawP",
    ])


def tip_rate_robustness(base):
    scenarios = {
        "Exclude TipEntryError": base[~base["TipEntryError"]],
        "Tip rate at or below 100%": base[base["TipRateSensitivity"]],
    }
    rows = []
    for name, sample in scenarios.items():
        result = stats.spearmanr(sample["Amount"], sample["TipRatePct"])
        rows.append([name, len(sample), result.statistic, result.pvalue])
    return pd.DataFrame(rows, columns=["Scenario", "N", "TipRateBillRho", "RawP"])


def tip_rate_context(base):
    sample = base[~base["TipEntryError"]]
    core = sample[sample["CorePartySize"]]
    per_head = stats.spearmanr(core["TipRatePct"], core["PerHead"])
    party_size = stats.spearmanr(core["TipRatePct"], core["Partysize"])
    multiple_mask = np.isclose(np.mod(sample["Tip"] * 2, 1), 0)
    return pd.DataFrame([
        ("Tip rate vs per-head spend", len(core), per_head.statistic, per_head.pvalue, np.nan, np.nan, "Spearman rho"),
        ("Tip rate vs party size", len(core), party_size.statistic, party_size.pvalue, np.nan, np.nan, "Spearman rho"),
        ("Median tip amount", len(sample), np.nan, np.nan, sample["Tip"].median(), np.nan, "Currency units"),
        ("Tips in 0.50 increments", len(sample), np.nan, np.nan, 100 * multiple_mask.mean(), int(multiple_mask.sum()), "Percent and count"),
    ], columns=["Metric", "N", "Statistic", "RawP", "Value", "Count", "Measure"])
