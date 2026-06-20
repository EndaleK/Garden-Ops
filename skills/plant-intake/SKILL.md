---
name: plant-intake
description: Add plants to the garden registry from photos. Use this whenever Kaleb uploads a photo of a plant, says "add this to the garden", "what plant is this", "new plant", or describes plants he's bought or planted. Also use when correcting or enriching an existing plant record.
---

# Plant Intake

Turn a plant photo (or description) into a complete registry record.

## Workflow

1. **Identify.** From the photo: species, cultivar if distinguishable. If uncertain,
   give top 2–3 candidates and the distinguishing feature to check (leaf shape, flower,
   bark). Ask Kaleb to confirm before writing the record. Never silently guess.
2. **Check Edmonton viability.** Is it hardy to zone 4a? If not, the record MUST have a
   non-trivial `overwinter.strategy` (dig_and_store / bring_indoors / cover_on_frost /
   annual_dies). Consult `data/edmonton-climate.md`.
3. **Research the care profile** (use web search if needed for the specific cultivar):
   - `water.weekly_mm` — baseline weekly water need in mm
   - `fertilizer` — N-P-K preference, interval, season (respect the Aug 1 nitrogen stop
     for perennials/shrubs/trees)
   - `pests` — Alberta-relevant pests only, with watch window + IPM-first response
   - `frost_tolerance_c` — temp at which protection is needed (null if fully hardy)
   - `overwinter` — strategy, trigger, instructions
4. **Assign a zone.** Ask which zone if not obvious. Plant must reference a valid
   `zone_id` in `data/zones.json`; create the zone first if needed.
5. **Write the record** to `data/plants.json`, validating against
   `data/plants.schema.json`. plant_id format: `<slug>-<zone>-<nn>` (e.g. `peony-z2-01`).
6. **Save the photo** to `photos/` named `<plant_id>.jpg` and reference it in the record.
7. **Confirm back** with a one-paragraph care summary so Kaleb can sanity-check.

## Edge cases
- Multiple plants in one photo: create one record each, confirm the list first.
- Houseplants that summer outdoors: type `tropical_potted`, overwinter `bring_indoors`,
  trigger "night temps < 10°C" (typically early September in Edmonton).
- Unknown quantity: ask. Quantity matters for fertilizer rates.
