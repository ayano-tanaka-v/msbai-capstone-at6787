"""Part 2 verification: a regression cross-check for the ratio-method
valuation (analysis/VALUATION.md v2). NOT a new headline number -- the
point is to confirm the ratio range isn't way off, using an independent
method with honest out-of-sample testing.

Fits log(annual_fee_usd_real2024) ~ log(capacity) [+ venue_type], on the
full global analysis.naming_rights_analysis_ready comparable set (OBSERVED,
non-null fee + capacity, sub-$10k floor already excluded -- no additional
country or venue-type filtering here, since "keep it simple" argues for
using the whole comparable population rather than a second bespoke filter).

Repeated k-fold cross-validation (not a single train/test split) reports
out-of-sample error; the final prediction for Chiba Lotte is made by
refitting on ALL rows (using every available comparable for the actual
prediction) and computing a classic OLS prediction interval.

Usage:
    python3 scripts/regression_cross_check.py

Requires: google-cloud-bigquery, numpy, pandas, scikit-learn, statsmodels
Env vars: BQ_PROJECT (default msbai-capstone-at6787)
"""
import os

import numpy as np
import pandas as pd
import statsmodels.api as sm
from google.cloud import bigquery
from sklearn.model_selection import KFold

PROJECT = os.environ.get("BQ_PROJECT", "msbai-capstone-at6787")
TARGET_CAPACITY = 33000
TARGET_VENUE_TYPE_GROUP = "Ballpark"
LATEST_FX_JPY_PER_USD = 149.657926890952  # ref.fx_rates, JPY, 2025 actual, carried fwd to 2026
N_SPLITS = 5
N_REPEATS = 10  # 5-fold x 10 repeats = 50 held-out folds total, not one lucky split


def venue_type_group(venue_type):
    """Collapse the raw venue_type strings into a small factor with no
    rare (<3-row) levels, so the categorical model doesn't get a level
    it never saw in a given CV fold."""
    v = venue_type.lower()
    if "ballpark" in v:
        return "Ballpark"
    if "stadium" in v:
        return "Stadium"
    if "arena" in v:
        return "Arena"
    return "Other"


def load_data(client):
    query = f"""
        SELECT record_id, venue_name, country, venue_type, capacity,
               annual_fee_usd_real2024, gdp_usd, population, gdp_per_capita_usd
        FROM `{PROJECT}.analysis.naming_rights_analysis_ready_with_market`
    """
    df = client.query(query).to_dataframe()
    df["venue_type_group"] = df["venue_type"].apply(venue_type_group)
    df["log_capacity"] = np.log(df["capacity"])
    df["log_fee"] = np.log(df["annual_fee_usd_real2024"])
    df["log_gdp"] = np.log(df["gdp_usd"])
    df["log_gdp_per_capita"] = np.log(df["gdp_per_capita_usd"])
    return df


def design_matrix(df, use_venue_type, group_categories, market_term=None):
    """log_capacity (+ venue_type_group dummies, reference = 'Arena', the
    largest group; + an optional market-size term) with a constant.
    group_categories fixes dummy columns across train/test/full so a fold
    missing a rare level still aligns. market_term is None, 'log_gdp', or
    'log_gdp_per_capita' -- country-level market-size test (CLAUDE.md
    section 1's coarse-proxy caveat: every venue in a country gets the
    same national figure)."""
    X = pd.DataFrame({"log_capacity": df["log_capacity"].values}, index=df.index)
    if use_venue_type:
        for cat in group_categories:
            if cat == "Arena":  # reference level, no dummy
                continue
            X[f"vt_{cat}"] = (df["venue_type_group"] == cat).astype(float).values
    if market_term is not None:
        X[market_term] = df[market_term].values
    return sm.add_constant(X, has_constant="add")


def cross_validate(df, use_venue_type, group_categories, market_term=None):
    """Repeated k-fold: every row gets an out-of-sample prediction from a
    model that never saw it. Returns pooled (actual_log, pred_log) for all
    OOS predictions across all repeats/folds."""
    y = df["log_fee"].values
    actual_all, pred_all = [], []
    for repeat in range(N_REPEATS):
        kf = KFold(n_splits=N_SPLITS, shuffle=True, random_state=repeat)
        for train_idx, test_idx in kf.split(df):
            train_df, test_df = df.iloc[train_idx], df.iloc[test_idx]
            X_train = design_matrix(train_df, use_venue_type, group_categories, market_term)
            X_test = design_matrix(test_df, use_venue_type, group_categories, market_term)
            model = sm.OLS(y[train_idx], X_train).fit()
            pred = model.predict(X_test)
            actual_all.extend(y[test_idx])
            pred_all.extend(pred.values)
    return np.array(actual_all), np.array(pred_all)


def oos_metrics(actual_log, pred_log):
    actual_usd = np.exp(actual_log)
    pred_usd = np.exp(pred_log)
    abs_pct_err = np.abs(pred_usd - actual_usd) / actual_usd
    ss_res = np.sum((actual_log - pred_log) ** 2)
    ss_tot = np.sum((actual_log - actual_log.mean()) ** 2)
    r2_log = 1 - ss_res / ss_tot
    return {
        "median_abs_pct_error": np.median(abs_pct_err),
        "p75_abs_pct_error": np.quantile(abs_pct_err, 0.75),
        "r2_log_scale": r2_log,
        "n_oos_predictions": len(actual_log),
    }


def main():
    client = bigquery.Client(project=PROJECT)
    df = load_data(client)
    print(f"Loaded {len(df)} rows from analysis.naming_rights_analysis_ready")
    print("venue_type_group counts:\n", df["venue_type_group"].value_counts(), "\n")

    group_categories = sorted(df["venue_type_group"].unique())

    print("=== Out-of-sample validation: Model A (capacity only) ===")
    a_actual, a_pred = cross_validate(df, use_venue_type=False, group_categories=group_categories)
    a_metrics = oos_metrics(a_actual, a_pred)
    print(a_metrics)

    print("\n=== Out-of-sample validation: Model B (capacity + venue_type) ===")
    b_actual, b_pred = cross_validate(df, use_venue_type=True, group_categories=group_categories)
    b_metrics = oos_metrics(b_actual, b_pred)
    print(b_metrics)

    chosen_use_venue_type = b_metrics["median_abs_pct_error"] < a_metrics["median_abs_pct_error"]
    print(f"\nChosen (pre-market) model: {'B (capacity + venue_type)' if chosen_use_venue_type else 'A (capacity only)'}")

    print("\n=== Market-size test: does adding a market term beat capacity-only OOS? ===")
    print("(baseline = capacity only, since B didn't beat it out-of-sample last time)")
    c1_actual, c1_pred = cross_validate(df, use_venue_type=False, group_categories=group_categories, market_term="log_gdp")
    c1_metrics = oos_metrics(c1_actual, c1_pred)
    print("Model C1 (capacity + log_gdp):", c1_metrics)

    c2_actual, c2_pred = cross_validate(df, use_venue_type=False, group_categories=group_categories, market_term="log_gdp_per_capita")
    c2_metrics = oos_metrics(c2_actual, c2_pred)
    print("Model C2 (capacity + log_gdp_per_capita):", c2_metrics)

    candidates = {
        "A (capacity only)": (a_metrics, False, None),
        "C1 (capacity + log_gdp)": (c1_metrics, False, "log_gdp"),
        "C2 (capacity + log_gdp_per_capita)": (c2_metrics, False, "log_gdp_per_capita"),
    }
    best_name = min(candidates, key=lambda k: candidates[k][0]["median_abs_pct_error"])
    best_metrics, chosen_use_venue_type, chosen_market_term = candidates[best_name]
    market_helps = best_metrics["median_abs_pct_error"] < a_metrics["median_abs_pct_error"]
    print(f"\nBest model by OOS median abs % error: {best_name}")
    print(f"Market term improves on capacity-only OOS error: {market_helps}")
    print(f"  capacity-only median abs % error: {a_metrics['median_abs_pct_error']:.4f}")
    print(f"  best-with-market median abs % error: {best_metrics['median_abs_pct_error']:.4f}")

    final_use_venue_type = chosen_use_venue_type
    final_market_term = chosen_market_term if market_helps else None
    if not market_helps:
        print("\nMarket term does NOT improve out-of-sample error -- keeping capacity-only, plainly.")
        final_use_venue_type = False

    print(f"\n=== Final model, fit on ALL rows, for the actual Chiba Lotte prediction ===")
    print(f"Using: use_venue_type={final_use_venue_type}, market_term={final_market_term}")
    X_full = design_matrix(df, final_use_venue_type, group_categories, final_market_term)
    final_model = sm.OLS(df["log_fee"].values, X_full).fit()
    print(final_model.summary())

    target_row = {
        "log_capacity": [np.log(TARGET_CAPACITY)],
        "venue_type_group": [TARGET_VENUE_TYPE_GROUP],
    }
    if final_market_term is not None:
        japan_market = df.loc[df["country"] == "Japan", final_market_term].iloc[0]
        target_row[final_market_term] = [japan_market]
    target_row = pd.DataFrame(target_row)

    X_target = design_matrix(target_row, final_use_venue_type, group_categories, final_market_term)
    pred = final_model.get_prediction(X_target)
    summary = pred.summary_frame(alpha=0.20)  # 80% prediction interval
    print("\n=== Chiba Lotte prediction (log scale), 80% prediction interval ===")
    print(summary)

    mean_log = summary["mean"].iloc[0]
    lo_log = summary["obs_ci_lower"].iloc[0]
    hi_log = summary["obs_ci_upper"].iloc[0]
    mean_usd, lo_usd, hi_usd = np.exp(mean_log), np.exp(lo_log), np.exp(hi_log)

    print("\n=== Chiba Lotte prediction, dollar/yen terms ===")
    print(f"Point estimate:  USD {mean_usd:,.0f}  /  JPY {mean_usd * LATEST_FX_JPY_PER_USD:,.0f}")
    print(f"80% PI low:      USD {lo_usd:,.0f}  /  JPY {lo_usd * LATEST_FX_JPY_PER_USD:,.0f}")
    print(f"80% PI high:     USD {hi_usd:,.0f}  /  JPY {hi_usd * LATEST_FX_JPY_PER_USD:,.0f}")


if __name__ == "__main__":
    main()
