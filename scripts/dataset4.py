"""
Complete Electricity Maps data pull for the Carbon-Aware AI Model Scheduling
project. Pulls everything the paper's Methodology (Section 3.3) promises:
    - Carbon Intensity: historical (14 days) + forecast
    - Renewable Energy % and Carbon-Free Energy %: historical (14 days) + forecast
      (these come from the power-breakdown endpoints, fields
       renewablePercentage and fossilFreePercentage)

Design goals for a one-shot trial run:
    1. Test authentication on ONE zone/signal first before spending calls on
       all 8 zones — if this fails, nothing else runs.
    2. Save each zone's data to disk immediately after fetching it (not just
       at the very end), so a network error or trial cutoff partway through
       does not lose data already retrieved.
    3. Print clear progress and error messages for every call.
    4. Combine everything into one final Excel file at the end, built from
       the incrementally saved per-zone CSVs (so the final combine step can
       be re-run safely even if fetching was interrupted and resumed).

Usage:
    export ELECTRICITYMAPS_API_KEY="your_key_here"
    python pull_full_dataset.py
"""

import os
import sys
import time
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone

API_KEY = os.environ.get("ELECTRICITYMAPS_API_KEY", "")
BASE_URL = "https://api.electricitymap.org/v3"
HEADERS = {"auth-token": API_KEY}

ZONES = ["IN-WE", "IN-SO", "IN-NO", "IN-EA", "GB", "DE", "FR", "US-CAL-CISO"]
DAYS_BACK = 14
RAW_DIR = "data/raw_pull"


def get(endpoint: str, params: dict):
    """Single GET with basic error surfacing. Returns (ok, json_or_None)."""
    try:
        resp = requests.get(f"{BASE_URL}{endpoint}", params=params, headers=HEADERS, timeout=25)
    except requests.RequestException as e:
        print(f"    [network error] {e}")
        return False, None

    if resp.status_code != 200:
        print(f"    [HTTP {resp.status_code}] {endpoint} params={params} -> {resp.text[:200]}")
        return False, None

    return True, resp.json()


def test_authentication():
    print("Step 1/3: Testing API key on a single zone/signal before doing anything else...")
    ok, data = get("/carbon-intensity/latest", {"zone": "GB"})
    if not ok:
        print("\nAuthentication or connectivity test FAILED. Stopping before using any more")
        print("of your trial quota. Fix the API key / connection issue and re-run this script.")
        sys.exit(1)
    print(f"    OK — sample response: {data}\n")


def fetch_past_range_chunks(endpoint: str, zone: str, days_back: int):
    """Fetch `days_back` days of history via past-range, chunked into <=7-day
    calls (endpoint caps at 10 days/240h per call at hourly granularity)."""
    now = datetime.now(timezone.utc)
    all_records = []
    chunk_size = 7
    starts = list(range(days_back, 0, -chunk_size))
    for chunk_start_days_ago in starts:
        chunk_end_days_ago = max(chunk_start_days_ago - chunk_size, 0)
        start_iso = (now - timedelta(days=chunk_start_days_ago)).replace(minute=0, second=0, microsecond=0).isoformat()
        end_iso = (now - timedelta(days=chunk_end_days_ago)).replace(minute=0, second=0, microsecond=0).isoformat()

        ok, data = get(endpoint, {"zone": zone, "start": start_iso, "end": end_iso})
        if ok and data:
            records = data.get("data", [])
            all_records.extend(records)
            print(f"    {zone} {endpoint} [{start_iso[:10]} to {end_iso[:10]}]: {len(records)} records")
        time.sleep(0.3)
    return all_records


def fetch_forecast(endpoint: str, zone: str):
    ok, data = get(endpoint, {"zone": zone})
    if not ok or not data:
        return []
    records = data.get("forecast", [])
    print(f"    {zone} {endpoint} forecast: {len(records)} records")
    return records


def main():
    if not API_KEY:
        raise SystemExit("Set ELECTRICITYMAPS_API_KEY environment variable before running.")

    os.makedirs(RAW_DIR, exist_ok=True)
    test_authentication()

    print("Step 2/3: Fetching all signals for all zones (saving incrementally)...\n")

    for zone in ZONES:
        print(f"--- {zone} ---")

        # Carbon intensity
        ci_hist = fetch_past_range_chunks("/carbon-intensity/past-range", zone, DAYS_BACK)
        pd.DataFrame(ci_hist).assign(zone=zone).to_csv(f"{RAW_DIR}/{zone}_carbon_intensity_hist.csv", index=False)

        ci_fcst = fetch_forecast("/carbon-intensity/forecast", zone)
        pd.DataFrame(ci_fcst).assign(zone=zone).to_csv(f"{RAW_DIR}/{zone}_carbon_intensity_forecast.csv", index=False)

        # Power breakdown (contains renewablePercentage, fossilFreePercentage)
        pb_hist = fetch_past_range_chunks("/power-breakdown/past-range", zone, DAYS_BACK)
        pd.DataFrame(pb_hist).assign(zone=zone).to_csv(f"{RAW_DIR}/{zone}_power_breakdown_hist.csv", index=False)

        pb_fcst = fetch_forecast("/power-breakdown/forecast", zone)
        pd.DataFrame(pb_fcst).assign(zone=zone).to_csv(f"{RAW_DIR}/{zone}_power_breakdown_forecast.csv", index=False)

        print()

    print("Step 3/3: Combining all per-zone CSVs into one Excel workbook...")
    combine_into_excel()
    print("\nDone. See data/electricitymaps_full_dataset.xlsx")


def combine_into_excel():
    """Reads whatever per-zone CSVs exist in RAW_DIR (even if the fetch loop
    was interrupted partway) and combines them into one workbook. Safe to
    re-run independently of fetching."""
    def combine(pattern_suffix):
        frames = []
        for zone in ZONES:
            path = f"{RAW_DIR}/{zone}_{pattern_suffix}.csv"
            if os.path.exists(path):
                df = pd.read_csv(path)
                if not df.empty:
                    frames.append(df)
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    ci_hist = combine("carbon_intensity_hist")
    ci_fcst = combine("carbon_intensity_forecast")
    pb_hist = combine("power_breakdown_hist")
    pb_fcst = combine("power_breakdown_forecast")

    out_path = "data/electricitymaps_full_dataset.xlsx"
    with pd.ExcelWriter(out_path) as writer:
        ci_hist.to_excel(writer, sheet_name="CarbonIntensity_Historical", index=False)
        ci_fcst.to_excel(writer, sheet_name="CarbonIntensity_Forecast", index=False)
        pb_hist.to_excel(writer, sheet_name="PowerBreakdown_Historical", index=False)
        pb_fcst.to_excel(writer, sheet_name="PowerBreakdown_Forecast", index=False)

    print(f"    CarbonIntensity_Historical: {ci_hist.shape}")
    print(f"    CarbonIntensity_Forecast:   {ci_fcst.shape}")
    print(f"    PowerBreakdown_Historical:  {pb_hist.shape}")
    print(f"    PowerBreakdown_Forecast:    {pb_fcst.shape}")


if __name__ == "__main__":
    main()