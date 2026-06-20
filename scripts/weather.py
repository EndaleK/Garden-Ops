#!/usr/bin/env python3
"""
weather.py - Edmonton weather for Garden Ops.

Pulls from Open-Meteo (free, no API key):
  - Past 7 days: rainfall, ET0 evapotranspiration
  - Next 7 days: rain forecast, min/max temps, ET0, frost risk
Outputs a single JSON object to stdout. Other scripts consume this.

Usage:  python3 weather.py            # pretty JSON
        python3 weather.py --compact  # one-line JSON
"""
import json
import sys
import urllib.request
from pathlib import Path

GARDEN = json.loads((Path(__file__).parent.parent / "data" / "garden.json").read_text())
LAT = GARDEN["location"]["lat"]
LON = GARDEN["location"]["lon"]
TZ = GARDEN["location"]["timezone"]

URL = (
    "https://api.open-meteo.com/v1/forecast"
    f"?latitude={LAT}&longitude={LON}"
    "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,"
    "et0_fao_evapotranspiration,wind_gusts_10m_max"
    "&past_days=7&forecast_days=7"
    f"&timezone={TZ.replace('/', '%2F')}"
)

def fetch():
    # Offline/test override: set GARDEN_WX_FILE to a raw Open-Meteo JSON dump
    import os
    cache = os.environ.get("GARDEN_WX_FILE")
    if cache:
        return json.loads(Path(cache).read_text())
    with urllib.request.urlopen(URL, timeout=15) as r:
        return json.loads(r.read().decode())

def summarize(raw):
    d = raw["daily"]
    days = []
    for i, date in enumerate(d["time"]):
        days.append({
            "date": date,
            "tmax_c": d["temperature_2m_max"][i],
            "tmin_c": d["temperature_2m_min"][i],
            "precip_mm": d["precipitation_sum"][i],
            "et0_mm": d["et0_fao_evapotranspiration"][i],
            "wind_gust_kmh": d["wind_gusts_10m_max"][i],
        })
    past, future = days[:7], days[7:]
    frost_nights = [x for x in future if x["tmin_c"] is not None and x["tmin_c"] <= 2.0]
    return {
        "location": "Edmonton, AB",
        "past_7d": {
            "rain_total_mm": round(sum(x["precip_mm"] or 0 for x in past), 1),
            "et0_total_mm": round(sum(x["et0_mm"] or 0 for x in past), 1),
            "days": past,
        },
        "next_7d": {
            "rain_total_mm": round(sum(x["precip_mm"] or 0 for x in future), 1),
            "et0_total_mm": round(sum(x["et0_mm"] or 0 for x in future), 1),
            "frost_risk_nights": [{"date": x["date"], "tmin_c": x["tmin_c"]} for x in frost_nights],
            "days": future,
        },
    }

if __name__ == "__main__":
    out = summarize(fetch())
    indent = None if "--compact" in sys.argv else 2
    print(json.dumps(out, indent=indent))
