# Garden Ops — Edmonton Garden Management System

## What this project is

A Cowork-managed garden operations system for Kaleb's garden in Edmonton, Alberta.
It tracks every plant, computes watering needs from Edmonton weather (and later from
soil sensors), schedules fertilizer and pest treatments, and manages seasonal
transitions (frost protection, overwintering, bringing plants indoors).

**Scaling intent:** personal tool now → Brainwave Solutions product later. All data is
structured (JSON/JSONL), all logic is deterministic where possible, and every design
decision should survive a port to a multi-user web app (Supabase + Vercel). Do not
hard-code anything that would only work for one garden — garden-level config lives in
`data/garden.json`.

## Location & climate constants

- **Location:** Edmonton, AB — lat 53.5461, lon -113.4938
- **Hardiness zone:** 4a (Canadian zone 3b–4a depending on microclimate)
- **Average last spring frost:** ~May 7 (safe planting for tender annuals: long weekend, ~May 18)
- **Average first fall frost:** ~Sept 22
- **Frost-free season:** ~135–140 days
- **Risks to watch:** late May frosts, July hail, August heat spikes, early September frost,
  chinook freeze-thaw damage on perennials in winter
- Full climate reference: `data/edmonton-climate.md`

## Data model (single source of truth)

| File | What it holds |
|---|---|
| `data/garden.json` | Garden-level config (location, units, notification prefs) |
| `data/zones.json` | Physical garden zones. **Sensor-ready**: each zone has a `moisture_source` field (`weather_model` now, `sensor:<id>` later) |
| `data/plants.json` | Plant registry — one record per plant/grouping, conforms to `data/plants.schema.json` |
| `data/treatments.jsonl` | Append-only log of every watering, fertilizer, and pest treatment |
| `data/observations.jsonl` | Append-only log of observations (pest sightings, disease, growth notes, photos) |

**Rules:**
1. Never edit `treatments.jsonl` or `observations.jsonl` retroactively — append only.
2. Every plant must reference a valid `zone_id`.
3. All dates are ISO 8601 (`YYYY-MM-DD`), all times local (America/Edmonton).
4. When adding plants from photos, follow `skills/plant-intake/SKILL.md`.

## Skills (workflows)

| Skill | When to use |
|---|---|
| `skills/plant-intake/` | Kaleb uploads plant photos → identify, research, add to registry |
| `skills/daily-brief/` | "What does the garden need today?" — runs weather + watering + alerts |
| `skills/watering-engine/` | Water-balance logic and how to interpret `scripts/watering.py` output |
| `skills/treatment-tracker/` | Logging/scheduling fertilizer and insecticide applications |
| `skills/overwintering/` | Fall transition: what to dig up, cover, mulch, or bring indoors |

## Scripts

- `scripts/weather.py` — pulls Edmonton forecast + recent rainfall + ET₀ from Open-Meteo
  (no API key). Outputs JSON to stdout.
- `scripts/watering.py` — runs the water-balance model per zone using weather data +
  plant registry. Outputs per-zone watering recommendations.
- `scripts/daily_brief.py` — orchestrator: weather → watering → due treatments →
  frost/hail alerts → markdown brief.

Run with: `python3 scripts/daily_brief.py` (requires `requests`: `pip install requests`)

## Hardware (Phase 2 — designed in, not yet installed)

Sensor architecture is specified in `hardware/SENSOR-SPEC.md` (ESP32 + capacitive soil
moisture, MQTT). The integration contract: a sensor publishing to
`garden/<zone_id>/moisture` overrides the weather-model soil-moisture estimate for that
zone. Nothing else in the system changes. When sensors arrive, flip the zone's
`moisture_source` and the watering engine prefers measured data automatically.

## Conventions

- Tone of briefs: practical and short. Lead with actions, not data.
- Insecticide guidance: **IPM-first** — recommend identification and least-toxic option
  first (hand-pick, water spray, insecticidal soap, BTK) before chemical controls.
  Always note pollinator safety and pre-harvest intervals for edibles.
- Fertilizer guidance: state N-P-K, rate, and method. Edmonton soils are typically
  alkaline (pH 7.5–8); flag plants that need acidity (no blueberries without serious
  amendment).
- When uncertain about a plant ID from a photo, say so and list the top 2–3 candidates
  with distinguishing features to check.

## Roadmap

See `docs/ROADMAP.md` for the personal → product path (Phase 0–3).
