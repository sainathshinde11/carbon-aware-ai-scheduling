"""
Pulls approximately 2 weeks of historical carbon intensity data, plus the
current forecast, for all configured regions from the Electricity Maps API,
and saves it in the format expected by the carbon-aware scheduler project.

Usage:
    python pull_two_weeks_data.py

Requires: pip install requests pandas
Set your API key below or via the ELECTRICITYMAPS_API_KEY environment variable.
"""

import os
import time
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone

API_KEY = os.environ.get("ELECTRICITYMAPS_API_KEY", "YOUR_API_KEY_HERE")
BASE_URL = "https://api.electricitymap.org/v3"
HEADERS = {"auth-token": API_KEY}

ZONES = ["IN-WE", "IN-SO", "IN-NO", "IN-EA", "GB", "DE", "FR", "US-CAL-CISO"]
DAYS_BACK = 14  # how many days of history to pull


def fetch_history_range(zone: str, start_iso: str, end_iso: str):
    """
    Uses the confirmed /v3/carbon-intensity/past-range endpoint, which
    accepts a start and end datetime and returns hourly carbon intensity
    for that span. Per Electricity Maps' documentation, this endpoint is
    limited to a 10-day (240-hour) range per call at hourly granularity,
    so pulling 14 days requires two calls per zone.
    """
    resp = requests.get(
        f"{BASE_URL}/carbon-intensity/past-range",
        params={"zone": zone, "start": start_iso, "end": end_iso},
        headers=HEADERS,
        timeout=20,
    )
    if resp.status_code != 200:
        print(f"  [warn] {zone} {start_iso} to {end_iso}: HTTP {resp.status_code} — {resp.text[:150]}")
        return []
    return resp.json().get("data", [])


def fetch_forecast(zone: str):
    resp = requests.get(
        f"{BASE_URL}/carbon-intensity/forecast",
        params={"zone": zone},
        headers=HEADERS,
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json().get("forecast", [])


def main():
    if API_KEY == "YOUR_API_KEY_HERE":
        raise SystemExit("Set your API key in this script or via ELECTRICITYMAPS_API_KEY env var.")

    all_rows = []
    now = datetime.now(timezone.utc)

    for zone in ZONES:
        print(f"Fetching {zone} ...")

        # Historical: the past-range endpoint caps at 10 days (240h) per call
        # at hourly granularity, so split 14 days into two ~7-day calls.
        chunk_days = 7
        for chunk_start_days_ago in range(DAYS_BACK, 0, -chunk_days):
            chunk_end_days_ago = max(chunk_start_days_ago - chunk_days, 0)
            start_iso = (now - timedelta(days=chunk_start_days_ago)).replace(minute=0, second=0, microsecond=0).isoformat()
            end_iso = (now - timedelta(days=chunk_end_days_ago)).replace(minute=0, second=0, microsecond=0).isoformat()

            records = fetch_history_range(zone, start_iso, end_iso)
            for r in records:
                all_rows.append({
                    "region": zone,
                    "datetime": r.get("datetime"),
                    "carbon_intensity": r.get("carbonIntensity"),
                })
            time.sleep(0.3)  # be gentle on rate limits

        # Forecast: current forward-looking window
        forecast_records = fetch_forecast(zone)
        for r in forecast_records:
            all_rows.append({
                "region": zone,
                "datetime": r.get("datetime"),
                "carbon_intensity": r.get("carbonIntensity"),
            })

    df = pd.DataFrame(all_rows)
    df["datetime"] = pd.to_datetime(df["datetime"], utc=True).dt.tz_localize(None)
    df = df.dropna(subset=["carbon_intensity"]).drop_duplicates(subset=["region", "datetime"])
    df = df.sort_values(["region", "datetime"])

    out_path = "data/real_carbon_intensity_2weeks.csv"
    os.makedirs("data", exist_ok=True)
    df.to_csv(out_path, index=False)

    print(f"\nSaved {len(df)} rows across {df['region'].nunique()} regions to {out_path}")
    print(df.groupby("region")["datetime"].agg(["min", "max", "count"]))


if __name__ == "__main__":
    main()
