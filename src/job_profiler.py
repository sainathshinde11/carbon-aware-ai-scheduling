"""
Job Profiler (Section 3.1 of the paper).

Defines the Job representation and extracts scheduling-relevant attributes
from job submissions: duration, deadline, power draw, and default region.
"""

from dataclasses import dataclass
import pandas as pd


@dataclass
class Job:
    job_id: str
    submission_time: pd.Timestamp   # t0
    duration_hours: float           # d
    deadline: pd.Timestamp          # t_deadline
    power_kw: float                 # P — measured average power draw
    default_region: str             # region job would run in if not relocated
    interruptible: bool = False     # whether the job supports pause/resume

    def feasible_window_hours(self) -> float:
        """Total span, in hours, between submission and deadline. Used to
        sanity-check that the job's duration actually fits before its
        deadline."""
        return (self.deadline - self.submission_time).total_seconds() / 3600.0

    def is_feasible(self) -> bool:
        return self.feasible_window_hours() >= self.duration_hours


def load_jobs_from_csv(path: str) -> list:
    """
    Load job definitions from a CSV with columns:
        job_id, submission_time, duration_hours, deadline, power_kw, default_region
    Optional column: interruptible (True/False)

    Returns a list of Job objects.
    """
    df = pd.read_csv(path, parse_dates=["submission_time", "deadline"])
    jobs = []
    for _, row in df.iterrows():
        jobs.append(Job(
            job_id=str(row["job_id"]),
            submission_time=row["submission_time"],
            duration_hours=float(row["duration_hours"]),
            deadline=row["deadline"],
            power_kw=float(row["power_kw"]),
            default_region=str(row["default_region"]),
            interruptible=bool(row.get("interruptible", False)),
        ))
    return jobs
