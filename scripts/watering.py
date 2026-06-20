#!/usr/bin/env python3
"""
watering.py - per-zone water-balance model.

Model (simple bucket, mm of water):
  deficit = (plant_demand_7d scaled by ET0 vs seasonal norm)
          - rain_past_7d
          - rain_forecast_2d        (don't water ahead of rain)
  Adjusted by soil_type water-holding factor.

If a zone's moisture_source is 'sensor:<id>', measured volumetric moisture
(via MQTT cache file hardware/sensor_cache.json) overrides the estimate:
  < 20% VWC -> water now; 20-30% -> water soon; > 30% -> skip.

Usage: python3 watering.py            (fetches weather itself)
       python3 watering.py weather.json  (use cached weather output)
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
SOIL_FACTOR = {"sand": 1.25, "loam": 1.0, "clay": 0.8}  # clay holds water -> needs less frequent
ET0_NORM_7D = 28.0  # mm, rough Edmonton summer weekly ET0 baseline

def load(p):
    return json.loads((ROOT / p).read_text())

def get_weather():
    if len(sys.argv) > 1:
        return json.loads(Path(sys.argv[1]).read_text())
    out = subprocess.run([sys.executable, str(ROOT / "scripts" / "weather.py"), "--compact"],
                         capture_output=True, text=True, check=True)
    return json.loads(out.stdout)

def sensor_reading(sensor_id):
    cache = ROOT / "hardware" / "sensor_cache.json"
    if not cache.exists():
        return None
    data = json.loads(cache.read_text())
    return data.get(sensor_id, {}).get("vwc_percent")

def main():
    zones = load("data/zones.json")["zones"]
    plants = load("data/plants.json")["plants"]
    wx = get_weather()

    rain_past = wx["past_7d"]["rain_total_mm"]
    et0_past = wx["past_7d"]["et0_total_mm"]
    rain_next2 = round(sum((d["precip_mm"] or 0) for d in wx["next_7d"]["days"][:2]), 1)
    et_scale = max(0.5, min(1.8, et0_past / ET0_NORM_7D)) if et0_past else 1.0

    results = []
    for z in zones:
        zid = z["zone_id"]
        zone_plants = [p for p in plants if p["zone_id"] == zid]
        if not zone_plants:
            continue

        # Sensor path
        if str(z.get("moisture_source", "")).startswith("sensor:"):
            vwc = sensor_reading(z["moisture_source"].split(":", 1)[1])
            if vwc is not None:
                if vwc < 20:
                    action, reason = "WATER NOW", f"sensor {vwc:.0f}% VWC (dry)"
                elif vwc < 30:
                    action, reason = "WATER SOON", f"sensor {vwc:.0f}% VWC"
                else:
                    action, reason = "SKIP", f"sensor {vwc:.0f}% VWC (moist)"
                results.append({"zone": zid, "name": z["name"], "action": action,
                                "reason": reason, "source": "sensor"})
                continue  # sensor present and reporting -> done

        # Weather-model path
        demand = max(p["water"]["weekly_mm"] for p in zone_plants) * et_scale
        soil = SOIL_FACTOR.get(z.get("soil_type", "loam"), 1.0)
        deficit = round((demand * soil) - rain_past - rain_next2, 1)

        if deficit > 15:
            action = "WATER NOW"
        elif deficit > 5:
            action = "WATER LIGHT"
        else:
            action = "SKIP"
        reason = (f"need ~{demand:.0f}mm/wk (ET adj x{et_scale:.2f}), "
                  f"rain past7d {rain_past}mm, next 48h {rain_next2}mm -> deficit {deficit}mm")
        results.append({"zone": zid, "name": z["name"], "action": action,
                        "deficit_mm": deficit, "reason": reason, "source": "weather_model"})

    print(json.dumps({"recommendations": results,
                      "frost_risk_nights": wx["next_7d"]["frost_risk_nights"]}, indent=2))

if __name__ == "__main__":
    main()
