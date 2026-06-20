# Hardware Spec — Phase 2 Soil Sensors

## Goal
Replace per-zone *estimated* soil moisture with *measured* moisture, changing nothing
else in the system. The integration contract is one JSON file: `hardware/sensor_cache.json`.

## Bill of materials (per zone, ~$20–25 CAD)
| Part | Notes |
|---|---|
| ESP32 dev board (e.g. ESP32-WROOM) | WiFi built in; one board can serve 3–4 sensors |
| Capacitive soil moisture sensor v2.0 | NOT resistive (those corrode in a season). Conformal-coat the electronics end |
| Waterproof enclosure + cable gland | Sensor electronics must stay dry |
| USB power or 18650 + solar | Deep sleep gives weeks on battery |

Start with **one ESP32 + 2 sensors** in your two most-watered zones. Validate, then scale.

## Firmware behavior (ESPHome recommended — config, not code)
- Wake every 30 min → read ADC → publish → deep sleep
- Calibrate per sensor: record ADC raw in air (0% VWC) and submerged (100%), map linearly
- Publish MQTT to a Mosquitto broker on the Mac mini / always-on machine:

```
topic:   garden/<zone_id>/moisture
payload: {"sensor_id":"S1","vwc_percent":24.5,"raw":2210,"battery_v":3.9,"ts":"2026-06-12T07:30:00-06:00"}
```

## Bridge (the only new software needed)
A small daemon (launchd, like MAMS) subscribes to `garden/+/moisture` and writes the
latest reading per sensor to `hardware/sensor_cache.json`:
```json
{ "S1": {"vwc_percent": 24.5, "ts": "2026-06-12T07:30:00-06:00"}, "S2": {...} }
```
`scripts/watering.py` already reads this file. Flip the zone's `moisture_source` to
`"sensor:S1"` in `data/zones.json` and the watering engine prefers measured data.
Staleness rule: readings older than 6h are ignored (sensor flagged offline, weather
model takes over) — implement the timestamp check when the bridge is built.

## Calibration & placement
- Place sensor at root depth (10–15cm for veg, deeper for shrubs), mid-bed, away from
  drip emitters.
- VWC thresholds in the engine (20% / 30%) assume loam; recalibrate against finger-test
  for clay zones (clay reads "wet" at lower plant-available water).

## Phase 3 preview (don't build yet)
Same ESP32s drive relay boards → 12V solenoid valves → drip lines per zone. The watering
engine's output becomes a command (`garden/<zone_id>/valve/open`, duration computed from
deficit_mm × area). Blow out lines before freeze-up (see overwintering skill).
