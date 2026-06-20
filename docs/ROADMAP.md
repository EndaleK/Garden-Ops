# Roadmap — Garden Ops → Brainwave Product

## Phase 0 — Populate & run manually (now)
- [ ] Define real zones in `data/zones.json` (one per area watered as a unit)
- [ ] Photo-intake every plant (skills/plant-intake) — delete EXAMPLE records
- [ ] Run `daily_brief.py` manually for a week; tune `weekly_mm` values
- [ ] Backfill any treatments already done this season

## Phase 1 — Automate (this summer)
- [ ] LaunchAgent at 07:00 → daily_brief.py → Hermes Telegram (MAMS pattern)
- [ ] Add ECCC alert check (severe thunderstorm/hail watch) to the brief
- [ ] Weekly photo check-in: compare new photos to records, log observations

## Phase 2 — Hardware (order sensors)
- [ ] 1× ESP32 + 2 capacitive sensors, Mosquitto broker, ESPHome
- [ ] MQTT→cache bridge daemon (with 6h staleness check)
- [ ] Validate sensor vs model recommendations for 2–3 weeks before trusting

## Phase 3 — Actuation
- [ ] Solenoid valves + drip per zone; engine output → valve commands
- [ ] Manual-override + rain-skip safety logic

## Productization path (Brainwave)
The moat is the same one as Synaptic's: **localized intelligence**. Generic garden apps
assume temperate climates; "gardening for zone 3–4 prairie Canada" is underserved
(Edmonton, Calgary, Saskatoon, Winnipeg = ~3M people who all lose plants to the same
frost dates and hail).

Port plan when ready:
- Data model → Supabase tables (it's already relational: gardens → zones → plants → treatments)
- Scripts → edge functions; daily brief → push notifications
- Plant intake → the killer feature: photo → Claude vision ID → auto care profile
  tuned to the user's postal-code climate normals
- Hardware → optional premium tier (ship calibrated sensor kits)
- Validate with your own garden for one full season first — the overwintering cycle
  (Sept–May) is the hardest part to get right and the part competitors skip.
