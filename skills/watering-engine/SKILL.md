---
name: watering-engine
description: Explains and tunes the water-balance model. Use when Kaleb asks why a watering recommendation was made, wants to adjust water needs, asks about a specific zone's watering, or when integrating sensor moisture data into watering decisions.
---

# Watering Engine

## The model (scripts/watering.py)
Per zone, in mm of rain-equivalent water:

```
demand   = max(weekly_mm of plants in zone) × ET_scale
ET_scale = past-7d ET0 ÷ 28mm baseline, clamped 0.5–1.8
deficit  = demand × soil_factor − rain_past_7d − rain_next_48h
```
- soil_factor: sand 1.25 (drains fast), loam 1.0, clay 0.8 (holds water)
- deficit > 15mm → WATER NOW · 5–15mm → WATER LIGHT · ≤5mm → SKIP
- Forecast rain in the next 48h counts as credit — never water ahead of rain.

## Converting mm to real-world amounts
- 10mm over 1 m² = 10 L. A zone of 6 m² needing 20mm ≈ 120 L ≈ 12 watering cans
  or ~15–20 min of slow hose soak.
- Tell Kaleb amounts in minutes-of-hose or cans, not mm.

## Sensor override (Phase 2)
If `zones.json` has `moisture_source: "sensor:<id>"` and
`hardware/sensor_cache.json` contains a recent reading, measured VWC wins:
< 20% water now · 20–30% soon · > 30% skip. If the sensor is stale (no reading
in 6h), fall back to the weather model and flag the sensor as offline.

## Tuning
- A plant consistently wilting on SKIP days → raise its `weekly_mm`.
- Mushrooms/fungus gnats/yellowing on clay → lower zone demand or check drainage.
- New transplants (first 3 weeks) need water regardless of model — note in brief.
