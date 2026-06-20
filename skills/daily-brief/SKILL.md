---
name: daily-brief
description: Produce the morning garden brief. Use whenever Kaleb asks "what does the garden need", "garden brief", "do I need to water", "anything due in the garden", or any general what-should-I-do-today gardening question. Also the entry point for the scheduled launchd/Hermes run.
---

# Daily Brief

## How to run
```bash
cd garden-ops && python3 scripts/daily_brief.py
```
Requires internet (Open-Meteo). If the API fails, fall back to reasoning from
`data/edmonton-climate.md` monthly norms and say the data is estimated.

## Your job after running the script
The script produces the mechanical brief. Add judgment on top:
- If frost risk + tender plants: spell out the *specific* protection action per plant
  (frost cloth vs bring pot in vs harvest).
- If WATER NOW on clay-soil zones: remind deep-and-infrequent beats daily sprinkles.
- Cross-reference `data/observations.jsonl` — if a pest was logged recently, escalate
  the inspection reminder.
- Keep the final output short. Actions first. No data dumps.

## Scheduling (launchd)
Same pattern as MAMS: a LaunchAgent running daily at 07:00 that pipes
`daily_brief.py` output to the Hermes Telegram send. Plist template in
`docs/ROADMAP.md` notes.
