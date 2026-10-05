"""
Experiment runner for the Carbon-Aware AI Model Scheduling framework.

Loads carbon intensity data and job definitions, runs the carbon-aware
scheduler and the carbon-agnostic baseline for each job, and reports the
resulting emissions savings and added latency (Section 4/5 of the paper).

Usage:
    python experiments/run_experiment.py \
        --jobs data/sample_jobs.csv \
        --carbon data/sample_carbon_intensity.csv \
        --allow-relocation False
"""

import argparse
import os
import sys
import yaml
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.carbon_data import CarbonDataModule
from src.job_profiler import load_jobs_from_csv
from src.scheduler import SchedulingDecisionEngine
from src.baseline import BaselineComparator
from src.dispatcher import Dispatcher
from src.utils import emissions_saved_pct, added_delay_hours


def load_config(path="config.yaml") -> dict:
    if os.path.exists(path):
        with open(path) as f:
            return yaml.safe_load(f)
    return {}


def run(jobs_path: str, carbon_path: str, allow_relocation: bool, output_path: str):
    config = load_config()

    # 1. Load carbon intensity data for all regions (Section 3.1 / 3.3)
    carbon_module = CarbonDataModule(config)
    carbon_series_by_region = carbon_module.load_from_csv(carbon_path)
    print(f"Loaded carbon intensity data for regions: {list(carbon_series_by_region.keys())}")

    # 2. Load job definitions (Job Profiler, Section 3.1)
    jobs = load_jobs_from_csv(jobs_path)
    print(f"Loaded {len(jobs)} jobs from {jobs_path}")

    # 3. Set up the Scheduling Decision Engine and Baseline Comparator
    engine = SchedulingDecisionEngine(
        carbon_series_by_region,
        allow_spatial_relocation=allow_relocation,
        time_step_hours=config.get("scheduling", {}).get("time_step_minutes", 60) / 60.0,
    )
    baseline = BaselineComparator(carbon_series_by_region)
    dispatcher = Dispatcher()

    results = []
    for job in jobs:
        scheduled = engine.schedule_job(job)
        base = baseline.run_baseline(job)
        dispatcher.dispatch(scheduled)

        row = {
            "job_id": job.job_id,
            "submission_time": job.submission_time,
            "deadline": job.deadline,
            "duration_hours": job.duration_hours,
            "default_region": job.default_region,
            "baseline_start": base["start_time"],
            "baseline_region": base["region"],
            "baseline_emissions_g": base["emissions_g"],
            "scheduled_start": scheduled["start_time"],
            "scheduled_region": scheduled["region"],
            "scheduled_emissions_g": scheduled["emissions_g"],
            "status": scheduled["status"],
        }

        if base["emissions_g"] is not None and scheduled["emissions_g"] is not None:
            row["emissions_saved_pct"] = round(
                emissions_saved_pct(base["emissions_g"], scheduled["emissions_g"]), 2
            )
            row["added_delay_hours"] = round(
                added_delay_hours(base["start_time"], scheduled["start_time"]), 2
            )
        else:
            row["emissions_saved_pct"] = None
            row["added_delay_hours"] = None

        results.append(row)

    results_df = pd.DataFrame(results)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    results_df.to_csv(output_path, index=False)

    print("\n=== Per-Job Results ===")
    print(results_df[["job_id", "baseline_emissions_g", "scheduled_emissions_g",
                       "emissions_saved_pct", "added_delay_hours", "status"]].to_string(index=False))

    valid = results_df.dropna(subset=["emissions_saved_pct"])
    if not valid.empty:
        print("\n=== Summary ===")
        print(f"Jobs successfully scheduled: {len(valid)} / {len(results_df)}")
        print(f"Average carbon emissions saved: {valid['emissions_saved_pct'].mean():.2f}%")
        print(f"Average added scheduling delay: {valid['added_delay_hours'].mean():.2f} hours")
        print(f"Total baseline emissions:  {valid['baseline_emissions_g'].sum():.1f} gCO2eq")
        print(f"Total scheduled emissions: {valid['scheduled_emissions_g'].sum():.1f} gCO2eq")

    print(f"\nFull results written to: {output_path}")
    return results_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a carbon-aware scheduling experiment.")
    parser.add_argument("--jobs", default="data/sample_jobs.csv", help="Path to jobs CSV")
    parser.add_argument("--carbon", default="data/sample_carbon_intensity.csv", help="Path to carbon intensity CSV")
    parser.add_argument("--allow-relocation", default="False", help="Allow spatial (cross-region) scheduling")
    parser.add_argument("--output", default="results/experiment_results.csv", help="Where to save results")
    args = parser.parse_args()

    run(
        jobs_path=args.jobs,
        carbon_path=args.carbon,
        allow_relocation=args.allow_relocation.lower() == "true",
        output_path=args.output,
    )
