"""
Scheduling Decision Engine (Section 3.2 / 3.4 of the paper).

Implements the exhaustive-search scheduling algorithm:

    Algorithm: Carbon-Aware Job Scheduling
    Input: job duration d, submission time t0, deadline t_deadline,
           forecasted carbon intensity C(t, r) for candidate region(s) R
    Output: selected start time t_s*, selected region r*

    1. Determine the set of feasible start times S:
       S = { t_s : t0 <= t_s and t_s + d <= t_deadline }
    2. For each candidate region r in R:
           For each feasible start time t_s in S:
               Compute window_emissions(t_s, r) =
                   sum of C(t, r) over the window [t_s, t_s + d]
    3. Select (t_s*, r*) = argmin over all (t_s, r) of window_emissions(t_s, r)
    4. If no region relocation is permitted, restrict R to the job's
       default/submission region before step 2.
    5. Hold the job until time t_s*, then dispatch it to region r*.
"""

from src.job_profiler import Job
from src.utils import hourly_range, window_emissions


class SchedulingDecisionEngine:
    def __init__(self, carbon_series_by_region: dict, allow_spatial_relocation: bool = False,
                 time_step_hours: float = 1.0):
        """
        carbon_series_by_region: {region: pandas Series indexed by datetime}
        allow_spatial_relocation: if False, only the job's default_region is considered
        time_step_hours: granularity of candidate start times (Step 1 of the algorithm)
        """
        self.carbon_series_by_region = carbon_series_by_region
        self.allow_spatial_relocation = allow_spatial_relocation
        self.time_step_hours = time_step_hours

    def _candidate_regions(self, job: Job) -> list:
        # Step 4 of the algorithm: restrict to default region unless relocation is allowed
        if self.allow_spatial_relocation:
            return list(self.carbon_series_by_region.keys())
        return [job.default_region]

    def _feasible_start_times(self, job: Job) -> list:
        # Step 1: S = { t_s : t0 <= t_s and t_s + d <= t_deadline }
        latest_start = job.deadline - (job.deadline - job.submission_time) * 0  # placeholder, replaced below
        from datetime import timedelta
        latest_start = job.deadline - timedelta(hours=job.duration_hours)
        if latest_start < job.submission_time:
            return []  # infeasible: job cannot fit before its deadline at all
        return hourly_range(job.submission_time, latest_start + timedelta(hours=self.time_step_hours))

    def schedule_job(self, job: Job) -> dict:
        """
        Runs Steps 1-3 of the algorithm for a single job.
        Returns a dict with the chosen start time, region, and expected emissions,
        or None values if no feasible/valid schedule could be found.
        """
        if not job.is_feasible():
            return {"job_id": job.job_id, "start_time": None, "region": None,
                    "emissions_g": None, "status": "infeasible: duration exceeds deadline window"}

        candidate_starts = self._feasible_start_times(job)
        candidate_regions = self._candidate_regions(job)

        if not candidate_starts:
            return {"job_id": job.job_id, "start_time": None, "region": None,
                    "emissions_g": None, "status": "infeasible: no valid start time"}

        best = {"start_time": None, "region": None, "emissions_g": float("inf")}

        # Steps 2-3: exhaustive search over (start_time, region)
        for region in candidate_regions:
            series = self.carbon_series_by_region.get(region)
            if series is None:
                continue
            for t_s in candidate_starts:
                emissions = window_emissions(series, t_s, job.duration_hours, job.power_kw)
                if emissions is None:
                    continue  # not enough forecast data to cover this window
                if emissions < best["emissions_g"]:
                    best = {"start_time": t_s, "region": region, "emissions_g": emissions}

        if best["start_time"] is None:
            return {"job_id": job.job_id, "start_time": None, "region": None,
                    "emissions_g": None, "status": "no carbon data available for feasible window"}

        return {
            "job_id": job.job_id,
            "start_time": best["start_time"],
            "region": best["region"],
            "emissions_g": best["emissions_g"],
            "status": "scheduled",
        }
