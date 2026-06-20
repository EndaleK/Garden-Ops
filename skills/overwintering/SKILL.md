---
name: overwintering
description: Fall transition and frost protection planning. Use from mid-August onward, whenever frost appears in the forecast, or when Kaleb asks what to bring inside, dig up, cover, mulch, or how to prep the garden for winter. Also use in spring for the reverse (when to bring plants back out).
---

# Overwintering (Edmonton zone 4a)

## The fall sequence
Generate the checklist by grouping `data/plants.json` on `overwinter.strategy`:

| Strategy | Timing trigger | Action |
|---|---|---|
| `bring_indoors` | night temps < 10°C (early Sept) | Acclimate over a week; inspect/treat for hitchhiking pests BEFORE bringing in (soap spray, soil drench) |
| `cover_on_frost` | any forecast night ≤ 2°C | Frost cloth/old sheets at dusk, remove mid-morning. One covered night in early Sept often buys 2–3 more growing weeks |
| `dig_and_store` | after first light frost blackens foliage | Dahlias/glads/begonias: lift, cure 1–2 weeks, store in peat/vermiculite at 4–10°C |
| `mulch_protect` | AFTER ground freezes (~early Nov) | 10–15cm mulch/leaves. Goal: keep ground frozen through chinooks, not warm |
| `annual_dies` | before first hard frost | Final harvest; pull and compost (not diseased material) |
| `hardy_leave` | late Oct | Deep watering before freeze-up, especially evergreens |

## Frost-night drill (any night ≤ 2°C forecast)
1. List every plant where `tmin ≤ frost_tolerance_c + 2`.
2. Pots → garage/indoors. Beds → cover at dusk. Harvest anything ripe on tender edibles.
3. Log the event in observations.

## Other fall tasks to surface in October
Drain/disconnect hoses, blow out irrigation lines (Phase 3 hardware!), final mow,
burlap screens for exposed evergreens, rodent guards on young tree trunks.

## Spring reverse (May)
Bring `bring_indoors` plants out gradually after May 7, hardening off over 7–10 days;
tender annuals out after May 18 unless forecast is clean.
