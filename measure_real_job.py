"""
Real AI training job with measured energy consumption (Priority 1 fix).

Trains an actual neural network (MLPClassifier) on the digits dataset
(a genuine, if small, AI training workload) and measures its real power
draw and energy consumption using CodeCarbon, an established open-source
emissions-tracking library used in several papers reviewed in Section 2
(e.g., CarbonEdge [15]).

This replaces the placeholder power_kw values used in data/real_jobs.csv
with an actual measured value from real training, closing the gap flagged
in Section 6 (Discussion / Limitations) of the paper.
"""

import time
import json
from codecarbon import EmissionsTracker
from sklearn.datasets import load_digits
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split


def run_measured_training():
    print("Loading dataset...")
    X, y = load_digits(return_X_y=True)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("Starting measured training run...")
    tracker = EmissionsTracker(
        project_name="carbon_aware_scheduler_demo_job",
        output_dir="results",
        output_file="codecarbon_emissions.csv",
        log_level="error",
        save_to_file=True,
    )

    tracker.start()
    start_time = time.time()

    # A real, if small, neural network training job -- multiple epochs
    # over multiple hidden-layer configurations to give a non-trivial,
    # measurable amount of real compute.
    model = MLPClassifier(
        hidden_layer_sizes=(256, 128, 64),
        max_iter=2000,
        random_state=42,
    )
    model.fit(X_train, y_train)
    accuracy = model.score(X_test, y_test)

    elapsed_seconds = time.time() - start_time
    emissions_kg = tracker.stop()

    # Pull the detailed energy figures CodeCarbon recorded for this run
    energy_kwh = None
    try:
        import pandas as pd
        df = pd.read_csv("results/codecarbon_emissions.csv")
        last_row = df.iloc[-1]
        energy_kwh = float(last_row["energy_consumed"])
        duration_s = float(last_row["duration"])
    except Exception as e:
        print(f"Could not read detailed CodeCarbon output: {e}")
        duration_s = elapsed_seconds

    avg_power_kw = (energy_kwh / (duration_s / 3600.0)) if energy_kwh and duration_s > 0 else None

    result = {
        "model": "MLPClassifier (256,128,64), digits dataset",
        "test_accuracy": round(accuracy, 4),
        "duration_seconds": round(duration_s, 2),
        "energy_consumed_kwh": round(energy_kwh, 8) if energy_kwh else None,
        "emissions_kg_co2eq_local_grid": round(float(emissions_kg), 8) if emissions_kg else None,
        "average_power_kw": round(avg_power_kw, 6) if avg_power_kw else None,
    }

    print("\n=== Measured Training Job Results ===")
    for k, v in result.items():
        print(f"  {k}: {v}")

    with open("results/measured_job_result.json", "w") as f:
        json.dump(result, f, indent=2)

    print("\nSaved to results/measured_job_result.json")
    return result


if __name__ == "__main__":
    run_measured_training()
