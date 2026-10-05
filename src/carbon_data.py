"""
Carbon Intensity Data Module (Section 3.1 / 3.3 of the paper).

Responsible for supplying forecasted (and historical/actual) grid carbon
intensity data, C(t, r), for one or more candidate regions. Supports three
sources, in order of preference:
    1. Electricity Maps API (real-time + forecast + historical; needs API key)
    2. UK National Energy System Operator (NESO) API (GB only; free, no key)
    3. A local CSV file (offline / reproducible fallback, e.g. for grading)
"""

import requests
import pandas as pd


class CarbonDataModule:
    def __init__(self, config: dict):
        self.config = config
        self.em_key = config.get("electricity_maps", {}).get("api_key", "")
        self.em_base = config.get("electricity_maps", {}).get("base_url", "")
        self.neso_base = config.get("uk_neso", {}).get("base_url", "")

    # ------------------------------------------------------------------
    # Electricity Maps
    # ------------------------------------------------------------------
    def fetch_electricity_maps(self, zone: str, kind: str = "forecast") -> pd.Series:
        """
        Fetch carbon intensity data for a single zone from Electricity Maps.
        `kind` is either "forecast" or "history".
        Returns a pandas Series indexed by timestamp, values in gCO2eq/kWh.
        """
        if not self.em_key:
            raise ValueError("No Electricity Maps API key configured in config.yaml")

        endpoint = f"{self.em_base}/carbon-intensity/{kind}"
        headers = {"auth-token": self.em_key}
        resp = requests.get(endpoint, params={"zone": zone}, headers=headers, timeout=15)
        resp.raise_for_status()
        payload = resp.json()

        records = payload.get(kind, payload.get("history", []))
        df = pd.DataFrame(records)
        df["datetime"] = pd.to_datetime(df["datetime"])
        series = df.set_index("datetime")["carbonIntensity"].sort_index()
        series.name = zone
        return series

    # ------------------------------------------------------------------
    # UK NESO (free, no key, GB only)
    # ------------------------------------------------------------------
    def fetch_uk_neso(self, date: str = None) -> pd.Series:
        """
        Fetch half-hourly carbon intensity for Great Britain from the UK
        NESO Carbon Intensity API. If `date` is None, fetches the current
        48-hour forecast window; otherwise fetches that specific date
        (format: YYYY-MM-DD).
        """
        if date:
            url = f"{self.neso_base}/intensity/date/{date}"
        else:
            url = f"{self.neso_base}/intensity"

        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        records = resp.json()["data"]

        rows = []
        for r in records:
            rows.append({
                "datetime": r["from"],
                "carbonIntensity": r["intensity"]["forecast"] or r["intensity"]["actual"],
            })
        df = pd.DataFrame(rows)
        df["datetime"] = pd.to_datetime(df["datetime"])
        series = df.set_index("datetime")["carbonIntensity"].sort_index()
        series.name = "GB"
        return series

    # ------------------------------------------------------------------
    # Local CSV fallback (recommended for reproducible experiments)
    # ------------------------------------------------------------------
    @staticmethod
    def load_from_csv(path: str) -> dict:
        """
        Load multi-region carbon intensity data from a CSV with columns:
            datetime, region, carbon_intensity
        Returns a dict of {region: pandas Series indexed by datetime}.
        """
        df = pd.read_csv(path, parse_dates=["datetime"])
        series_by_region = {}
        for region, group in df.groupby("region"):
            s = group.set_index("datetime")["carbon_intensity"].sort_index()
            s.name = region
            series_by_region[region] = s
        return series_by_region

    # ------------------------------------------------------------------
    def get_all_regions(self, regions: list, source: str = "csv", csv_path: str = None) -> dict:
        """
        Convenience method: fetch carbon intensity series for a list of
        regions from the specified source ("electricity_maps", "uk_neso",
        or "csv"). Returns {region: pandas Series}.
        """
        if source == "csv":
            return self.load_from_csv(csv_path)

        result = {}
        for r in regions:
            if source == "electricity_maps":
                result[r] = self.fetch_electricity_maps(r, kind="forecast")
            elif source == "uk_neso":
                result[r] = self.fetch_uk_neso()
            else:
                raise ValueError(f"Unknown source: {source}")
        return result
