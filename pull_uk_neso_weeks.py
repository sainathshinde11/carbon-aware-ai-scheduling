"""
Pulls several weeks of REAL historical carbon intensity data for Great
Britain from the UK National Energy System Operator (NESO) API, plus the
current forecast. No API key required -- this is a fully free, public API.

This fixes the "only 48 hours of data" limitation: the NESO API's
/intensity/date/{date} endpoint returns half-hourly actual + forecast
carbon intensity for any given day, going back through its full history,
so looping over N days gives a genuinely long, real evaluation window.

Usage:
    python pull_uk_neso_weeks.py --days 21

Requires: pip install requests pandas
"""

import argparse
import time
import requests
import pandas as pd
from datetime import date, timedelta

BASE_URL = "https://api.carbonintensity.org.uk"


def fetch_day(day: date):
    """Fetch all half-hourly settlement periods for a single date.
    Each record includes BOTH the forecasted and actual carbon intensity
    for that same settlement period, which is what enables the forecast
    error analysis in this script's companion (forecast_sensitivity.py)."""
    url = f"{BASE_URL}/intensity/date/{day.isoformat()}"
    resp = requests.get(url, timeout=15)
    if resp.status_code != 200:
        print(f"  [warn] {day}: HTTP {resp.status_code}")
        return []
    return resp.json().get("data", [])


def fetch_current_forecast():
    """Fetch the current 48-hour-ahead forecast (separate from historical)."""
    resp = requests.get(f"{BASE_URL}/intensity", timeout=15)
    resp.raise_for_status()
    return resp.json().get("data", [])


def main(days_back: int):
    print(f"Pulling {days_back} days of REAL UK (GB) carbon intensity history...")
    all_rows = []
    today = date.today()

    for i in range(days_back, 0, -1):
        day = today - timedelta(days=i)
        records = fetch_day(day)
        for r in records:
            all_rows.append({
                "region": "GB",
                "datetime": r["from"],
                "forecast_intensity": r["intensity"]["forecast"],
                "actual_intensity": r["intensity"]["actual"],
                "carbon_intensity": r["intensity"]["actual"] if r["intensity"]["actual"] is not None
                                     else r["intensity"]["forecast"],
            })
        print(f"  {day}: {len(records)} half-hourly records")
        time.sleep(0.2)  # be polite to the free public API

    # Also grab the live forecast for the near future, useful for testing
    # the scheduler's forward-looking behavior beyond the historical window
    forecast_records = fetch_current_forecast()
    for r in forecast_records:
        all_rows.append({
            "region": "GB",
            "datetime": r["from"],
            "forecast_intensity": r["intensity"]["forecast"],
            "actual_intensity": None,
            "carbon_intensity": r["intensity"]["forecast"],
        })
    print(f"  current forecast: {len(forecast_records)} records")

    df = pd.DataFrame(all_rows)
    df["datetime"] = pd.to_datetime(df["datetime"], utc=True).dt.tz_localize(None)
    df = df.dropna(subset=["carbon_intensity"]).drop_duplicates(subset=["datetime"]).sort_values("datetime")

    out_path = "data/uk_neso_multiweek.csv"
    df[["region", "datetime", "carbon_intensity", "forecast_intensity", "actual_intensity"]].to_csv(out_path, index=False)

    print(f"\nSaved {len(df)} rows spanning {df['datetime'].min()} to {df['datetime'].max()}")
    print(f"-> {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=21, help="Number of past days to fetch")
    args = parser.parse_args()
    main(args.days)
