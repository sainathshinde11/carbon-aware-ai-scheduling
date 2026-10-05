"""
Robust temporal-scheduling evaluation using the real 3-week UK NESO dataset
(data/uk_neso_multiweek.csv). Instead of 7 fixed jobs at 7 fixed times (the
original 48-hour demo), this runs many trials: for each of several job
duration/deadline-window configurations, many random submission times are
sampled across the full 3-week real dataset, giving a genuine mean and
standard deviation of carbon savings rather than a single snapshot result.
"""

import numpy as np
import pandas as pd
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils import window_emissions, emissions_saved_pct, added_delay_hours

np.random.seed(42)

CARBON_CSV = "data/uk_neso_multiweek.csv"
N_TRIALS_PER_CONFIG = 100  # random submission times sampled per configuration

# (duration_hours, deadline_window_hours, power_kw, label)
JOB_CONFIGS = [
    (2, 8, 1.5, "short (2h duration, 8h window)"),
    (4, 16, 1.2, "medium (4h duration, 16h window)"),
    (6, 24, 2.5, "long (6h duration, 24h window)"),
    (10, 36, 3.0, "very long (10h duration, 36h window)"),
]


def load_series(path):
    df = pd.read_csv(path, parse_dates=["datetime"])
    df = df[df["region"] == "GB"].sort_values("datetime")
    return df.set_index("datetime")["carbon_intensity"]


def run_trial(series, duration_h, deadline_window_h, power_kw, submission_time):
    deadline = submission_time + pd.Timedelta(hours=deadline_window_h)

    # Baseline: immediate execution
    baseline_emissions = window_emissions(series, submission_time, duration_h, power_kw)
    if baseline_emissions is None:
        return None

    # Carbon-aware: exhaustive search over feasible start times (hourly steps)
    latest_start = deadline - pd.Timedelta(hours=duration_h)
    if latest_start < submission_time:
        return None
    candidates = pd.date_range(submission_time, latest_start, freq="30min")

    best_start, best_emissions = None, float("inf")
    for t_s in candidates:
        e = window_emissions(series, t_s, duration_h, power_kw)
        if e is not None and e < best_emissions:
            best_start, best_emissions = t_s, e

    if best_start is None:
        return None

    return {
        "baseline_emissions": baseline_emissions,
        "scheduled_emissions": best_emissions,
        "saved_pct": emissions_saved_pct(baseline_emissions, best_emissions),
        "delay_hours": added_delay_hours(submission_time, best_start),
    }


def main():
    series = load_series(CARBON_CSV)
    data_start, data_end = series.index.min(), series.index.max()
    print(f"Loaded {len(series)} real GB carbon intensity readings: {data_start} to {data_end}\n")

    all_results = []

    for duration_h, deadline_window_h, power_kw, label in JOB_CONFIGS:
        trial_results = []
        # Sample random submission times that leave room for the full deadline window
        latest_possible_submission = data_end - pd.Timedelta(hours=deadline_window_h)
        span_seconds = (latest_possible_submission - data_start).total_seconds()

        for _ in range(N_TRIALS_PER_CONFIG):
            random_offset = np.random.uniform(0, span_seconds)
            submission_time = data_start + pd.Timedelta(seconds=random_offset)
            submission_time = submission_time.floor("30min")

            result = run_trial(series, duration_h, deadline_window_h, power_kw, submission_time)
            if result is not None:
                trial_results.append(result)

        if trial_results:
            saved = [r["saved_pct"] for r in trial_results]
            delays = [r["delay_hours"] for r in trial_results]
            summary = {
                "config": label,
                "duration_hours": duration_h,
                "deadline_window_hours": deadline_window_h,
                "n_valid_trials": len(trial_results),
                "mean_saved_pct": round(float(np.mean(saved)), 2),
                "std_saved_pct": round(float(np.std(saved)), 2),
                "min_saved_pct": round(float(np.min(saved)), 2),
                "max_saved_pct": round(float(np.max(saved)), 2),
                "mean_delay_hours": round(float(np.mean(delays)), 2),
                "std_delay_hours": round(float(np.std(delays)), 2),
            }
            all_results.append(summary)
            print(f"[{label}]")
            print(f"  Valid trials: {summary['n_valid_trials']} / {N_TRIALS_PER_CONFIG}")
            print(f"  Carbon saved: {summary['mean_saved_pct']}% (std {summary['std_saved_pct']}, "
                  f"range {summary['min_saved_pct']}-{summary['max_saved_pct']}%)")
            print(f"  Added delay:  {summary['mean_delay_hours']}h (std {summary['std_delay_hours']})\n")

    results_df = pd.DataFrame(all_results)
    results_df.to_csv("results/uk_neso_multitrial_summary.csv", index=False)

    overall_mean_saved = np.average(results_df["mean_saved_pct"], weights=results_df["n_valid_trials"])
    overall_mean_delay = np.average(results_df["mean_delay_hours"], weights=results_df["n_valid_trials"])
    print("=== Overall (across all configurations) ===")
    print(f"Weighted mean carbon saved: {overall_mean_saved:.2f}%")
    print(f"Weighted mean added delay:  {overall_mean_delay:.2f} hours")
    print(f"Total trials run: {results_df['n_valid_trials'].sum()} across {len(JOB_CONFIGS)} job configurations")
    print(f"Real data window: {data_start.date()} to {data_end.date()} ({(data_end-data_start).days} days)")

    print("\nSaved to results/uk_neso_multitrial_summary.csv")


if __name__ == "__main__":
    main()
