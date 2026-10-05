"""
Shared helper functions used across the carbon-aware scheduling framework.
"""

from datetime import datetime, timedelta
import pandas as pd


def parse_time(value):
    """Parse a timestamp string (ISO 8601 or 'YYYY-MM-DD HH:MM') into a
    timezone-naive pandas Timestamp for consistent internal comparisons."""
    return pd.to_datetime(value)


def hourly_range(start, end):
    """Return a list of hourly timestamps from start (inclusive) to end
    (exclusive), used to enumerate candidate windows."""
    start = parse_time(start)
    end = parse_time(end)
    hours = []
    current = start
    while current < end:
        hours.append(current)
        current += timedelta(hours=1)
    return hours


def window_emissions(carbon_series: pd.Series, start, duration_hours: float, power_kw: float) -> float:
    """
    Compute total emissions (in grams CO2-equivalent) for a job of the given
    duration and power draw, starting at `start`, using an hourly carbon
    intensity series indexed by timestamp.

    This implements the discretized version of the integral in Section 3.2:
        emissions = P * sum( C(t, r) for t in [start, start + duration) )
    where each hourly C(t, r) value is treated as constant over that hour.
    """
    end = parse_time(start) + timedelta(hours=duration_hours)
    window = carbon_series[(carbon_series.index >= parse_time(start)) & (carbon_series.index < end)]

    if window.empty:
        return None  # no data available for this window; caller should skip it

    # Fractional last hour handling: weight the final partial hour proportionally
    full_hours = int(duration_hours)
    remainder = duration_hours - full_hours

    total = window.iloc[:full_hours].sum() if full_hours > 0 else 0.0
    if remainder > 0 and len(window) > full_hours:
        total += window.iloc[full_hours] * remainder

    return power_kw * total


def emissions_saved_pct(baseline_emissions: float, scheduled_emissions: float) -> float:
    """Percentage reduction in emissions achieved by the scheduled job
    relative to the carbon-agnostic baseline."""
    if baseline_emissions in (None, 0):
        return None
    return 100.0 * (baseline_emissions - scheduled_emissions) / baseline_emissions


def added_delay_hours(baseline_start, scheduled_start) -> float:
    """Difference, in hours, between the carbon-aware start time and the
    baseline (immediate) start time."""
    return (parse_time(scheduled_start) - parse_time(baseline_start)).total_seconds() / 3600.0
