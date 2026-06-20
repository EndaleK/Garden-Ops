# Onboarding Flow Spec — New User Garden Setup

**Status:** Draft v1 · 2026-06-17
**Owner:** Kaleb / Brainwave Solutions
**Scope:** How a brand-new user goes from sign-up to their first useful daily brief.
**Companion docs:** `docs/ROADMAP.md` (productization path), `CLAUDE.md` (data model), `data/plants.schema.json`.

---

## 1. Goal & design principles

Get a new user from zero to a **trustworthy first brief in under 10 minutes**, without asking
them to know their hardiness zone, frost dates, or how much water a tomato wants. The system
already knows all of that — onboarding's job is to collect the few things only the user can
provide (where they are, what they're growing) and derive everything else.

Principles:

1. **Derive, don't ask.** Anything computable from location (climate profile, frost dates,
   zone) is computed, never typed. The user confirms, they don't author.
2. **Defaults that work, depth that's optional.** A casual user should be able to skip zones
   and plant detail and still get a sane brief. Power users (you) can subdivide.
3. **Every step writes one scoped record.** Each screen maps to one row/object keyed by
   `garden_id`, so onboarding is also the data-seeding path. No orphan state.
4. **Resumable.** A user can stop after any step and come back; the garden is valid (if sparse)
   at every checkpoint.
5. **The photo is the magic.** Plant intake via photo → vision ID → auto care profile is the
   single highest-value moment. Everything before it is setup; protect that wow.

---

## 2. The flow at a glance

```
[1] Account            → user row
[2] Location           → garden row + derived climate_profile   ← the unlock
[3] Zones (optional)   → zone rows (default: one "whole yard" zone)
[4] Plants (photo)     → plant_instance rows from species_catalog, climate-adapted
[5] First brief        → runs the engine, delivers the payoff + sets notifications
```

Each step is detailed below with: **what the user does**, **what the system does**,
**what gets written**, and **defaults / edge cases**.

---

## 3. Step-by-step

### Step 1 — Account

- **User does:** signs up (email / OAuth), picks units (metric/imperial), confirms timezone
  (pre-filled from browser).
- **System does:** creates the user; nothing garden-specific yet.
- **Writes:** `user` { id, email, units, timezone }. Maps to today's `garden.json → units` and
  `location.timezone`, lifted to the account level so a user can later own multiple gardens.
- **Defaults / edges:** units default to metric but inferred from locale; timezone editable.

### Step 2 — Location  *(the step that makes the product portable)*

- **User does:** drops a pin on a map **or** enters a postal/ZIP code. Optionally names the
  garden ("Backyard", "Community plot #14").
- **System does:** geocodes to lat/lon, then builds a **climate profile**:
  - **Hardiness zone** (lookup by lat/lon, or postal-code → zone table).
  - **Average last spring frost / first fall frost** (climate normals source).
  - **Monthly normals** (avg high/low, precip) — the per-garden equivalent of
    `data/edmonton-climate.md`, but computed.
  - Live ET₀ / rainfall already come per-lat/lon from Open-Meteo at brief time — no setup needed.
- **User confirms:** a one-screen summary — *"You're in Zone 5b. Last frost ~May 2, first
  frost ~Oct 4, ~150 frost-free days."* with an edit affordance for microclimate tweaks.
- **Writes:** `garden` { id, user_id, name, lat, lon, timezone } + `climate_profile`
  { garden_id, hardiness_zone, last_spring_frost, first_fall_frost, frost_free_days,
  monthly_normals, source, derived_at }.
- **Defaults / edges:** if normals lookup is uncertain (sparse data / coastal / mountain),
  show a confidence note and let the user nudge frost dates. Re-derivable on demand.

> **Why this is the linchpin:** every downstream rule currently hard-coded to Edmonton —
> watering ET baseline, frost alerts, the "stop nitrogen ~6 weeks before first fall frost"
> rule, overwintering triggers — reads from `climate_profile` instead of constants. Get this
> right and the rest of the system is already multi-garden.

### Step 3 — Zones  *(optional, templated)*

- **User does:** either accepts the default single zone, or adds zones (name, sun exposure,
  soil type, irrigation method). A short "Add another area?" loop.
- **System does:** seeds one default zone so the garden is never zone-less; offers quick
  templates ("Raised bed", "Container cluster", "In-ground row", "Lawn edge") that pre-fill
  soil/irrigation guesses.
- **Writes:** `zone` rows matching today's `zones.json` shape — { zone_id, garden_id, name,
  sun_exposure, soil_type, area_m2, irrigation, **moisture_source: "weather_model"**,
  sensor_id: null }. The sensor-ready field carries over unchanged, so the hardware tier
  drops in later with no migration.
- **Defaults / edges:** default zone = `{ name: "Whole yard", sun: "full_sun",
  soil: "loam", irrigation: "manual_hose" }`. Casual users can skip this entire step.

### Step 4 — Plants  *(photo intake — the core loop)*

- **User does:** for each plant/grouping: snaps or uploads a photo, picks the zone, sets
  quantity + (optional) planted date. Repeats.
- **System does (per `skills/plant-intake`):**
  1. Claude vision identifies species/cultivar; if uncertain, returns top 2–3 candidates with
     distinguishing features to check (never a silent guess).
  2. Pulls care defaults from the **species catalog** (water `weekly_mm`, fertilizer
     `npk_preference`/`interval_days`/`season`, `pests[]`, `frost_tolerance_c`,
     `overwinter.strategy`).
  3. **Adapts to the user's climate profile** — e.g. a fig is `bring_indoors` in Zone 5 but
     `mulch_protect` in Zone 7; overwinter triggers and the N-stop date are computed from the
     user's frost dates, not copied from yours.
- **User confirms:** the proposed care card; can override anything (it's their override, the
  catalog default stays clean).
- **Writes:** `plant_instance` rows — { plant_id, garden_id, zone_id, species_catalog_id,
  common_name, quantity, planted_date, photo, overrides{} }. The *knowledge* lives in
  `species_catalog`; the instance is thin. (This is the split from today's fat per-plant
  records in `plants.json` — same fields, but care defaults are referenced, not copied.)
- **Defaults / edges:** low-confidence ID → save as `TBD` with a "confirm later" flag
  (mirrors your real `*-TBD` records today); no photo → manual search of the catalog by name;
  unknown species → generic care profile + flag for review.

### Step 5 — First brief & notifications

- **User does:** taps "Show me today's brief"; sets delivery prefs (push / email / time).
- **System does:** runs the engine scoped to `garden_id` (weather → per-zone watering → due
  treatments → frost/hail alerts), exactly like `daily_brief.py` today but multi-tenant. The
  brief leads with actions, IPM-first for pests — same tone contract as `CLAUDE.md`.
- **Writes:** `notification_pref` { garden_id, channel, daily_brief_time }. Schedules the
  recurring run (edge function / cron per garden).
- **Defaults / edges:** brand-new garden with no treatment history → brief honestly says
  "no feedings logged yet, here's what's due to start" (we saw this exact empty-log case in
  your own brief). First brief should never look broken because the log is empty.

---

## 4. Data-write summary (onboarding = data seeding)

| Step | Table / record | Keyed by | Today's equivalent |
|---|---|---|---|
| 1 | `user` | id | `garden.json` (units, tz) |
| 2 | `garden` + `climate_profile` | user_id / garden_id | `garden.json` + `edmonton-climate.md` (now computed) |
| 3 | `zone` | garden_id | `zones.json` |
| 4 | `plant_instance` (+ `species_catalog` ref) | garden_id | `plants.json` (split into catalog + instance) |
| 5 | `notification_pref` | garden_id | `garden.json → notifications` |

Append-only logs (`treatments`, `observations`) are created empty and only ever inserted to —
the same contract as today's `.jsonl` files, enforced by insert-only table grants under RLS.

---

## 5. Definition of done (onboarding is "complete")

A garden is **brief-ready** when it has: a confirmed `climate_profile`, ≥1 zone, ≥1 plant
instance, and a notification preference. The UI can show a soft progress meter, but the brief
is generated from whatever exists — a user who adds one plant and stops still gets a real (if
short) brief tomorrow morning.

---

## 6. Open decisions (need a call before build)

1. **Climate normals source.** Hardiness zone + frost dates need a real data source. Options:
   bundled normals dataset (offline, fast, ages), a climate API (live, dependency, cost), or
   Open-Meteo historical + a zone lookup table (free, some assembly). Recommend the last for v1.
2. **Frost-date rule generalization.** The "Aug 1 stop nitrogen" hard rule must become
   "N weeks before first fall frost." Pick N (≈6) and apply it uniformly, or store a
   per-strategy offset.
3. **Species catalog seeding.** Hand-author the top ~100 prairie/temperate edibles + common
   ornamentals first, or seed from an external plant DB and curate? Catalog quality is the
   product — recommend hand-curating the Zone 3–6 core, generic fallback for the long tail.
4. **Zone granularity for casual users.** Confirm the single default zone is enough to ship;
   subdivision stays a power-user feature.
5. **Microclimate overrides.** How much manual frost-date adjustment to expose (urban heat
   island, valley cold sinks) vs. keeping it simple.

---

## 7. Sequencing note

Per the roadmap, **build the climate engine (Step 2's derivation) first**, even against the
current flat-file single-garden setup, and validate it against the Edmonton garden you already
know the answers for. Onboarding Steps 1, 3, 5 are mostly plumbing; Step 2 is the moat and
Step 4 is the magic — both depend on the climate profile existing. Don't migrate to Supabase
until the climate derivation is location-driven, or Edmonton assumptions get baked into the
schema.
