"""
Baseline Comparator (Section 3.5 of the paper).

Implements the carbon-agnostic baseline scheduling policy: the job is
dispatched for immediate execution at its submission time t0, regardless of
the carbon intensity prevailing at that moment. This is not part of the
operational scheduling path (see Figure 1) — it is invoked only during
evaluation, to measure how much the carbon-aware schedule improves on the
default behavior of a typical production scheduler.
"""

from src.job_profiler import Job
from src.utils import window_emissions


class BaselineComparator:
    def __init__(self, carbon_series_by_region: dict):
        self.carbon_series_by_region = carbon_series_by_region

    def run_baseline(self, job: Job) -> dict:
        """
        Computes emissions for immediate execution of the job in its
        default region, starting at its submission time t0.
        """
        series = self.carbon_series_by_region.get(job.default_region)
        if series is None:
            return {"job_id": job.job_id, "start_time": job.submission_time,
                     "region": job.default_region, "emissions_g": None,
                     "status": "no carbon data available for default region"}

        emissions = window_emissions(series, job.submission_time, job.duration_hours, job.power_kw)
        return {
            "job_id": job.job_id,
            "start_time": job.submission_time,
            "region": job.default_region,
            "emissions_g": emissions,
            "status": "baseline (immediate execution)" if emissions is not None else "no data for window",
        }
