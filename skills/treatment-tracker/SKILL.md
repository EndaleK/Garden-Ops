---
name: treatment-tracker
description: Log and schedule fertilizer and pest/disease treatments. Use whenever Kaleb says he fertilized, sprayed, or treated anything ("I fed the tomatoes", "sprayed the roses"), asks what's due for feeding, asks what to spray for a pest, or reports seeing a pest or disease.
---

# Treatment Tracker

## Logging (always do this when Kaleb reports an action)
Append one line to `data/treatments.jsonl`:
```json
{"date":"YYYY-MM-DD","type":"fertilizer|insecticide|fungicide|watering|other","zone_id":"Z2","plant_ids":["..."],"product":"...","rate":"...","method":"...","notes":"..."}
```
Pest *sightings* (no treatment yet) go to `data/observations.jsonl` instead.

## Fertilizer rules (Edmonton)
- Respect each plant's `interval_days` and `season`.
- **HARD RULE: no nitrogen on perennials, shrubs, or trees after Aug 1** — soft late
  growth winter-kills in zone 4a. The brief script enforces this; you enforce it in
  conversation too.
- Edmonton soil is alkaline — for iron-chlorosis symptoms (yellow leaves, green veins)
  recommend chelated iron, not just more fertilizer.
- Always give rate per the product label; when in doubt, half-strength.

## Pest/disease response protocol (IPM ladder — always start at step 1)
1. **Identify first.** Photo if possible. Wrong ID = wasted spray.
2. **Physical/cultural:** hand-pick, water blast, row cover, prune out, sanitation.
3. **Least-toxic:** insecticidal soap, horticultural oil, BTK (caterpillars),
   diatomaceous earth (slugs/crawlers).
4. **Chemical:** only if 1–3 fail and damage is significant. Name the active
   ingredient, the pre-harvest interval for edibles, and pollinator precautions
   (never spray open blooms; spray at dusk).
5. Log whatever was done; set a follow-up check in 5–7 days.

## Common product notes
- Insecticidal soap & BTK: safe near harvest, reapply after rain.
- Black knot on cherries/maydays: pruning in winter is the treatment — no spray works.
