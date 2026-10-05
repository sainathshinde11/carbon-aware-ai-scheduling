"""
Baseline comparison against a prior literature strategy (Priority 4).

Adds a second, non-trivial baseline alongside carbon-agnostic immediate
execution: a "Flexible Start" strategy in the style of Vergallo and
Mainetti [6], which searches only a short, fixed delay window (rather than
the job's full deadline window) before starting the job. This isolates how
much benefit the proposed framework's full-deadline-window optimal search
adds beyond a simple bounded-delay heuristic already established in prior
work, rather than only comparing against doing nothing.

Three strategies are compared on the same 400 trials (4 job configurations
x 100 random real submission times) used in Section 5.1:
    1. Baseline           -- immediate execution (carbon-agnostic)
    2. Flexible Start [6]  -- search only a short fixed window (here, 4 hours)
    3. Proposed (this paper) -- exhaustive search over the FULL deadline window
"""

import numpy as np
import pandas as pd
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils import window_emissions, emissions_saved_pct, added_delay_hours

np.random.seed(42)

CARBON_CSV = "data/uk_neso_multiweek.csv"
N_TRIALS_PER_CONFIG = 100
FLEXIBLE_START_WINDOW_HOURS = 4  # bounded delay window, per Vergallo & Mainetti [6]

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


def best_start_in_window(series, submission_time, search_end, duration_h, power_kw):
    """Exhaustive search for the lowest-emissions start time within
    [submission_time, search_end], at 30-minute granularity."""
    candidates = pd.date_range(submission_time, search_end, freq="30min")
    best_start, best_emissions = None, float("inf")
    for t_s in candidates:
        e = window_emissions(series, t_s, duration_h, power_kw)
        if e is not None and e < best_emissions:
            best_start, best_emissions = t_s, e
    return best_start, best_emissions


def run_trial(series, duration_h, deadline_window_h, power_kw, submission_time):
    deadline = submission_time + pd.Timedelta(hours=deadline_window_h)
    latest_start_full = deadline - pd.Timedelta(hours=duration_h)
    if latest_start_full < submission_time:
        return None

    # 1. Baseline: immediate execution
    baseline_emissions = window_emissions(series, submission_time, duration_h, power_kw)
    if baseline_emissions is None:
        return None

    # 2. Flexible Start [6]: bounded search window (min of 4h or full window if shorter)
    flex_search_end = min(submission_time + pd.Timedelta(hours=FLEXIBLE_START_WINDOW_HOURS), latest_start_full)
    flex_start, flex_emissions = best_start_in_window(series, submission_time, flex_search_end, duration_h, power_kw)
    if flex_start is None:
        return None

    # 3. Proposed: full deadline-window search
    full_start, full_emissions = best_start_in_window(series, submission_time, latest_start_full, duration_h, power_kw)
    if full_start is None:
        return None

    return {
        "baseline_emissions": baseline_emissions,
        "flex_emissions": flex_emissions,
        "full_emissions": full_emissions,
        "flex_saved_pct": emissions_saved_pct(baseline_emissions, flex_emissions),
        "full_saved_pct": emissions_saved_pct(baseline_emissions, full_emissions),
        "flex_delay_hours": added_delay_hours(submission_time, flex_start),
        "full_delay_hours": added_delay_hours(submission_time, full_start),
        # How much MORE the proposed full-window search saves beyond Flexible Start
        "improvement_over_flex_pct": emissions_saved_pct(flex_emissions, full_emissions),
    }


def main():
    series = load_series(CARBON_CSV)
    data_start, data_end = series.index.min(), series.index.max()
    print(f"Loaded {len(series)} real GB carbon intensity readings: {data_start} to {data_end}")
    print(f"Flexible Start [6] bounded window: {FLEXIBLE_START_WINDOW_HOURS} hours\n")

    all_results = []

    for duration_h, deadline_window_h, power_kw, label in JOB_CONFIGS:
        trial_results = []
        latest_possible_submission = data_end - pd.Timedelta(hours=deadline_window_h)
        span_seconds = (latest_possible_submission - data_start).total_seconds()

        for _ in range(N_TRIALS_PER_CONFIG):
            random_offset = np.random.uniform(0, span_seconds)
            submission_time = (data_start + pd.Timedelta(seconds=random_offset)).floor("30min")
            result = run_trial(series, duration_h, deadline_window_h, power_kw, submission_time)
            if result is not None:
                trial_results.append(result)

        if trial_results:
            flex_saved = [r["flex_saved_pct"] for r in trial_results]
            full_saved = [r["full_saved_pct"] for r in trial_results]
            flex_delay = [r["flex_delay_hours"] for r in trial_results]
            full_delay = [r["full_delay_hours"] for r in trial_results]
            improvement = [r["improvement_over_flex_pct"] for r in trial_results]

            summary = {
                "config": label,
                "n_valid_trials": len(trial_results),
                "flex_mean_saved_pct": round(float(np.mean(flex_saved)), 2),
                "flex_mean_delay_h": round(float(np.mean(flex_delay)), 2),
                "full_mean_saved_pct": round(float(np.mean(full_saved)), 2),
                "full_mean_delay_h": round(float(np.mean(full_delay)), 2),
                "mean_improvement_over_flex_pct": round(float(np.mean(improvement)), 2),
            }
            all_results.append(summary)

            print(f"[{label}]")
            print(f"  Flexible Start [6] (4h window):  {summary['flex_mean_saved_pct']}% saved, "
                  f"{summary['flex_mean_delay_h']}h delay")
            print(f"  Proposed (full window):          {summary['full_mean_saved_pct']}% saved, "
                  f"{summary['full_mean_delay_h']}h delay")
            print(f"  -> Proposed improves on Flexible Start by {summary['mean_improvement_over_flex_pct']}% "
                  f"additional emissions reduction\n")

    results_df = pd.DataFrame(all_results)
    results_df.to_csv("results/baseline_comparison_flexible_start.csv", index=False)

    overall_flex = np.average(results_df["flex_mean_saved_pct"], weights=results_df["n_valid_trials"])
    overall_full = np.average(results_df["full_mean_saved_pct"], weights=results_df["n_valid_trials"])
    print("=== Overall (weighted across all configurations) ===")
    print(f"Flexible Start [6]:  {overall_flex:.2f}% mean carbon saved")
    print(f"Proposed (this paper): {overall_full:.2f}% mean carbon saved")
    print(f"Proposed method captures {overall_full - overall_flex:.2f} percentage points more reduction "
          f"than the bounded Flexible Start strategy from prior work.")
    print("\nSaved to results/baseline_comparison_flexible_start.csv")


if __name__ == "__main__":
    main()
