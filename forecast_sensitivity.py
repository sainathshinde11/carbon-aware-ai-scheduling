"""
Forecast uncertainty sensitivity analysis (Priority 3 / Objective 4).

Uses the forecast_intensity and actual_intensity columns in
data/uk_neso_multiweek.csv (each UK NESO settlement period reports both) to:

    1. Quantify raw forecast error: how far forecast_intensity deviates
       from actual_intensity across the real 21-day dataset.
    2. Run the SAME 400-trial scheduling experiment as Section 5.1, but
       compare two versions of the scheduler:
         (a) "Forecast-based" scheduler: makes its scheduling decision
             using only forecast_intensity (what a real deployment would
             have available at decision time), then its TRUE emissions
             are computed using actual_intensity for the chosen window.
         (b) "Perfect-foresight" scheduler: makes its decision using
             actual_intensity directly (an upper bound / oracle baseline
             that could never be achieved in practice).
    The gap between (a) and (b) is the real cost of forecast uncertainty.

Requires data/uk_neso_multiweek.csv to have been generated with the
UPDATED pull_uk_neso_weeks.py (the one that saves both forecast_intensity
and actual_intensity columns, not just a single merged column).
"""

import numpy as np
import pandas as pd
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils import window_emissions, emissions_saved_pct

np.random.seed(42)

CARBON_CSV = "data/uk_neso_multiweek.csv"
N_TRIALS_PER_CONFIG = 100

JOB_CONFIGS = [
    (2, 8, 1.5, "short (2h duration, 8h window)"),
    (4, 16, 1.2, "medium (4h duration, 16h window)"),
    (6, 24, 2.5, "long (6h duration, 24h window)"),
    (10, 36, 3.0, "very long (10h duration, 36h window)"),
]


def load_paired_series(path):
    df = pd.read_csv(path, parse_dates=["datetime"])
    if "forecast_intensity" not in df.columns or "actual_intensity" not in df.columns:
        raise SystemExit(
            "data/uk_neso_multiweek.csv does not contain forecast_intensity and "
            "actual_intensity columns. Re-run the UPDATED pull_uk_neso_weeks.py "
            "to regenerate this file with both fields before running this script."
        )
    df = df[df["region"] == "GB"].sort_values("datetime")
    df = df.dropna(subset=["actual_intensity"])  # only real paired points, not the live forecast tail
    forecast_series = df.set_index("datetime")["forecast_intensity"]
    actual_series = df.set_index("datetime")["actual_intensity"]
    return forecast_series, actual_series, df


def report_raw_forecast_error(df):
    error = df["forecast_intensity"] - df["actual_intensity"]
    mae = error.abs().mean()
    rmse = np.sqrt((error ** 2).mean())
    mean_pct_error = (error.abs() / df["actual_intensity"]).mean() * 100
    corr = df["forecast_intensity"].corr(df["actual_intensity"])

    print("=== Raw Forecast Error (across all paired settlement periods) ===")
    print(f"  N paired readings: {len(df)}")
    print(f"  Mean Absolute Error (MAE): {mae:.2f} gCO2/kWh")
    print(f"  Root Mean Squared Error (RMSE): {rmse:.2f} gCO2/kWh")
    print(f"  Mean Absolute Percentage Error: {mean_pct_error:.2f}%")
    print(f"  Correlation (forecast vs actual): {corr:.4f}\n")
    return {"mae": mae, "rmse": rmse, "mape": mean_pct_error, "correlation": corr}


def best_start(series, submission_time, latest_start, duration_h, power_kw):
    candidates = pd.date_range(submission_time, latest_start, freq="30min")
    best_t, best_e = None, float("inf")
    for t_s in candidates:
        e = window_emissions(series, t_s, duration_h, power_kw)
        if e is not None and e < best_e:
            best_t, best_e = t_s, e
    return best_t, best_e


def run_trial(forecast_series, actual_series, duration_h, deadline_window_h, power_kw, submission_time):
    deadline = submission_time + pd.Timedelta(hours=deadline_window_h)
    latest_start = deadline - pd.Timedelta(hours=duration_h)
    if latest_start < submission_time:
        return None

    # (a) Forecast-based decision: choose start time using FORECAST data
    forecast_choice_start, _ = best_start(forecast_series, submission_time, latest_start, duration_h, power_kw)
    if forecast_choice_start is None:
        return None
    # ...but the TRUE emissions incurred use ACTUAL data at that chosen time
    true_emissions_of_forecast_choice = window_emissions(actual_series, forecast_choice_start, duration_h, power_kw)

    # (b) Perfect-foresight: choose start time using ACTUAL data directly (oracle upper bound)
    oracle_start, oracle_emissions = best_start(actual_series, submission_time, latest_start, duration_h, power_kw)
    if oracle_start is None or true_emissions_of_forecast_choice is None:
        return None

    # Baseline: immediate execution, true emissions
    baseline_emissions = window_emissions(actual_series, submission_time, duration_h, power_kw)
    if baseline_emissions is None:
        return None

    return {
        "baseline_emissions": baseline_emissions,
        "forecast_based_true_emissions": true_emissions_of_forecast_choice,
        "oracle_emissions": oracle_emissions,
        "forecast_based_saved_pct": emissions_saved_pct(baseline_emissions, true_emissions_of_forecast_choice),
        "oracle_saved_pct": emissions_saved_pct(baseline_emissions, oracle_emissions),
        # The gap: how much worse forecast-based scheduling is vs. perfect foresight
        "forecast_uncertainty_cost_pct": emissions_saved_pct(oracle_emissions, true_emissions_of_forecast_choice) * -1
                                          if true_emissions_of_forecast_choice >= oracle_emissions else 0.0,
    }


def main():
    forecast_series, actual_series, df = load_paired_series(CARBON_CSV)
    print(f"Loaded {len(df)} paired forecast/actual readings: {df['datetime'].min()} to {df['datetime'].max()}\n")

    report_raw_forecast_error(df)

    print("=== Scheduling Impact of Forecast Uncertainty (400 trials) ===\n")
    all_results = []

    for duration_h, deadline_window_h, power_kw, label in JOB_CONFIGS:
        trial_results = []
        data_start, data_end = df["datetime"].min(), df["datetime"].max()
        latest_possible_submission = data_end - pd.Timedelta(hours=deadline_window_h)
        span_seconds = (latest_possible_submission - data_start).total_seconds()

        for _ in range(N_TRIALS_PER_CONFIG):
            offset = np.random.uniform(0, span_seconds)
            submission_time = (data_start + pd.Timedelta(seconds=offset)).floor("30min")
            result = run_trial(forecast_series, actual_series, duration_h, deadline_window_h, power_kw, submission_time)
            if result is not None:
                trial_results.append(result)

        if trial_results:
            fc_saved = [r["forecast_based_saved_pct"] for r in trial_results]
            oracle_saved = [r["oracle_saved_pct"] for r in trial_results]
            cost = [r["forecast_uncertainty_cost_pct"] for r in trial_results]

            summary = {
                "config": label,
                "n_trials": len(trial_results),
                "forecast_based_mean_saved_pct": round(float(np.mean(fc_saved)), 2),
                "oracle_mean_saved_pct": round(float(np.mean(oracle_saved)), 2),
                "mean_forecast_uncertainty_cost_pct": round(float(np.mean(cost)), 2),
            }
            all_results.append(summary)
            print(f"[{label}]")
            print(f"  Forecast-based scheduling: {summary['forecast_based_mean_saved_pct']}% saved (real achievable)")
            print(f"  Perfect-foresight oracle:  {summary['oracle_mean_saved_pct']}% saved (theoretical upper bound)")
            print(f"  Cost of forecast uncertainty: {summary['mean_forecast_uncertainty_cost_pct']} percentage points\n")

    results_df = pd.DataFrame(all_results)
    results_df.to_csv("results/forecast_uncertainty_sensitivity.csv", index=False)

    overall_fc = np.average(results_df["forecast_based_mean_saved_pct"], weights=results_df["n_trials"])
    overall_oracle = np.average(results_df["oracle_mean_saved_pct"], weights=results_df["n_trials"])
    print("=== Overall ===")
    print(f"Forecast-based (realistic):    {overall_fc:.2f}% mean carbon saved")
    print(f"Perfect-foresight (oracle):    {overall_oracle:.2f}% mean carbon saved")
    print(f"Forecast uncertainty costs approximately {overall_oracle - overall_fc:.2f} percentage points "
          f"of achievable carbon reduction.")
    print("\nSaved to results/forecast_uncertainty_sensitivity.csv")


if __name__ == "__main__":
    main()
