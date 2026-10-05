# Carbon-Aware AI Model Scheduling

Implementation accompanying the paper "Carbon-Aware AI Model Scheduling."
Schedules AI training/inference jobs against real grid carbon intensity data
to minimize emissions, subject to job deadlines, and compares the result
against a carbon-agnostic (immediate-execution) baseline.

## Project Structure

```
carbon-aware-scheduler/
├── README.md
├── requirements.txt
├── config.yaml                          # Region list, API keys, experiment settings
├── src/
│   ├── __init__.py
│   ├── carbon_data.py                   # Carbon Intensity Data Module (Section 3.1)
│   ├── job_profiler.py                  # Job Profiler: Job dataclass + loading jobs
│   ├── scheduler.py                     # Scheduling Decision Engine (Section 3.4 algorithm)
│   ├── baseline.py                      # Baseline Comparator (carbon-agnostic policy)
│   ├── dispatcher.py                    # Dispatcher (simulated execution handoff)
│   └── utils.py                         # Shared helpers (time parsing, emissions math)
├── data/
│   ├── uk_neso_multiweek.csv            # REAL: 21 days, 1009 readings, GB (temporal experiment)
│   ├── real_carbon_intensity.csv        # REAL: 48h, 8 regions, Electricity Maps (spatial experiment)
│   ├── real_jobs.csv                    # 7 representative jobs used in the spatial experiment
│   ├── sample_carbon_intensity.csv      # Synthetic fallback data (for testing without API access)
│   └── sample_jobs.csv                  # Synthetic fallback jobs
├── experiments/
│   └── run_experiment.py                # Spatial experiment: temporal-only vs. temporal+spatial
├── run_uk_neso_multitrial.py            # Temporal experiment: 400 trials across 4 job configs
├── measure_real_job.py                  # Real energy measurement of an actual training job via CodeCarbon
├── pull_uk_neso_weeks.py                # Fetches more real UK NESO data (no API key needed)
├── pull_full_dataset.py                 # Fetches Electricity Maps data (needs academic API key)
└── results/                             # Output CSVs from all experiments (already populated)
```

## How the Modules Map to the Paper

| Paper Section | Module / Script |
|---|---|
| 3.1 System Overview | `carbon_data.py`, `job_profiler.py`, `scheduler.py`, `dispatcher.py` |
| 3.2 Problem Formulation | `scheduler.py` (implements the argmin over feasible start times/regions) |
| 3.3 Data Sources | `carbon_data.py`, `data/uk_neso_multiweek.csv`, `data/real_carbon_intensity.csv` |
| 3.4 Scheduling Algorithm | `scheduler.py::schedule_job()` |
| 3.5 Baseline for Comparison | `baseline.py` |
| 4.2 Temporal Scheduling Experiment (400 trials) | `run_uk_neso_multitrial.py` |
| 4.3 Spatial Scheduling Experiment (8 regions) | `experiments/run_experiment.py` |
| Section 6 Discussion — measured power draw | `measure_real_job.py` (CodeCarbon) |

## Setup

```bash
pip install -r requirements.txt
```

## Reproducing the Paper's Results

**Temporal experiment (Section 5.1 — 400 trials, real 21-day UK data):**
```bash
python run_uk_neso_multitrial.py
```
Outputs `results/uk_neso_multitrial_summary.csv` with mean/std/min/max
carbon savings and delay per job flexibility configuration.

**Spatial experiment (Section 5.2 — 8-region real Electricity Maps data):**
```bash
python experiments/run_experiment.py --jobs data/real_jobs.csv --carbon data/real_carbon_intensity.csv
python experiments/run_experiment.py --jobs data/real_jobs.csv --carbon data/real_carbon_intensity.csv --allow-relocation True
```
Run once without and once with `--allow-relocation True` to reproduce the
temporal-only vs. temporal-and-spatial comparison in Table 3.

**Real energy measurement (Section 6 — CodeCarbon):**
```bash
python measure_real_job.py
```
Trains a real small neural network and measures its actual energy
consumption. Note: in CPU-only environments without RAPL hardware access,
CodeCarbon falls back to fixed per-component wattage estimates rather than
a true dynamic reading -- see Section 6 (Discussion) for the honest caveat
this introduces. For a measurement at the same power scale as the jobs used
in the spatial experiment, re-run this on a machine with a real NVIDIA GPU.

**Pulling fresh data:**
- `pull_uk_neso_weeks.py` -- no API key needed, fully free, extends the UK dataset
- `pull_full_dataset.py` -- needs an Electricity Maps academic API key; note that
  `past-range` (extended historical) and `power-breakdown` endpoints returned
  401 Unauthorized under the academic tier tested during this project; only
  `/forecast` and `/latest` were accessible.

## Notes on Data Provenance

- All datasets in `data/` are real API pulls, not synthetic, except
  `sample_*.csv` which are explicitly synthetic fallbacks for offline testing.
- The two real datasets differ in scope: 21 days/1 region (UK NESO) for
  robust temporal statistics, and 48 hours/8 regions (Electricity Maps) for
  spatial comparison. This asymmetry is disclosed and discussed as a
  limitation in Section 6 of the paper.
