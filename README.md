# Garden Ops

Edmonton garden management system — Cowork project scaffold.

## Quick start
1. Open this folder as a Cowork project (CLAUDE.md is the master context).
2. Edit `data/zones.json` with your real garden zones.
3. Upload plant photos and say "add these to the garden" → plant-intake skill runs.
4. Ask "what does the garden need today?" or run:
   ```bash
   python3 scripts/daily_brief.py
   ```
   (Uses Open-Meteo, no API key. Internet required; offline test:
   `GARDEN_WX_FILE=<raw open-meteo json> python3 scripts/daily_brief.py`)

## Layout
- `CLAUDE.md` — project context & rules
- `data/` — garden config, zones, plant registry (+ schema), append-only logs
- `skills/` — plant-intake, daily-brief, watering-engine, treatment-tracker, overwintering
- `scripts/` — weather.py, watering.py, daily_brief.py
- `hardware/` — sensor spec (ESP32 + MQTT), integration contract
- `docs/ROADMAP.md` — Phase 0–3 + productization path
