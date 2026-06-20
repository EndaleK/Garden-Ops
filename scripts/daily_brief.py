#!/usr/bin/env python3
"""
daily_brief.py - orchestrator. Produces the morning garden brief (markdown to stdout).

Sections: weather summary | watering actions | frost & wind alerts |
fertilizer due | pest watch (by calendar window) | overwintering reminders (Aug 15+).

Wire to launchd + Hermes/Telegram for 7:00 delivery, e.g.:
  python3 daily_brief.py | <your telegram send script>
"""
import json
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent

def run(script, *args):
    out = subprocess.run([sys.executable, str(ROOT / "scripts" / script), *args],
                         capture_output=True, text=True, check=True)
    return json.loads(out.stdout)

def load(p):
    return json.loads((ROOT / p).read_text())

def last_treatment(treatments, plant_id, ttype):
    dates = [t["date"] for t in treatments
             if t.get("type") == ttype and plant_id in t.get("plant_ids", [])]
    return max(dates) if dates else None

def main():
    today = date.today()
    wx = run("weather.py", "--compact")
    water = run("watering.py")
    plants = load("data/plants.json")["plants"]
    treatments = [json.loads(l) for l in (ROOT / "data/treatments.jsonl").read_text().splitlines()
                  if l.strip() and not l.startswith('{"_comment')]

    lines = [f"# Garden Brief — {today.strftime('%A, %B %d')}", ""]

    # Weather
    nx = wx["next_7d"]["days"][0]
    lines += [f"**Today:** {nx['tmin_c']:.0f}–{nx['tmax_c']:.0f}°C, "
              f"{nx['precip_mm'] or 0}mm rain expected. "
              f"Past week: {wx['past_7d']['rain_total_mm']}mm rain.", ""]

    # Frost alerts
    frost = water.get("frost_risk_nights", [])
    if frost:
        lines.append("## ⚠️ FROST RISK")
        for f in frost:
            tender = [p["common_name"] for p in plants
                      if p.get("frost_tolerance_c") is not None
                      and f["tmin_c"] <= p["frost_tolerance_c"] + 2]
            lines.append(f"- {f['date']}: low {f['tmin_c']}°C — cover/bring in: "
                         + (", ".join(sorted(set(tender))) or "check tender plants"))
        lines.append("")

    # Wind/hail proxy
    gusty = [d for d in wx["next_7d"]["days"][:2] if (d.get("wind_gust_kmh") or 0) >= 70]
    if gusty:
        lines += ["## ⚠️ Severe weather watch",
                  "High wind gusts forecast — move potted plants under cover; "
                  "check ECCC alerts for hail.", ""]

    # Watering
    lines.append("## Watering")
    for r in water["recommendations"]:
        emoji = {"WATER NOW": "🔴", "WATER LIGHT": "🟡", "WATER SOON": "🟡", "SKIP": "🟢"}[r["action"]]
        lines.append(f"- {emoji} **{r['zone']} {r['name']}**: {r['action']} — {r['reason']}")
    lines.append("")

    # Fertilizer due
    due = []
    for p in plants:
        f = p.get("fertilizer") or {}
        if not f.get("interval_days"):
            continue
        if today.month >= 8 and p["type"] in ("perennial", "shrub", "tree"):
            continue  # Aug 1 nitrogen stop
        last = last_treatment(treatments, p["plant_id"], "fertilizer")
        if last is None:
            due.append((p["common_name"], "no record — log first application"))
        else:
            days = (today - datetime.strptime(last, "%Y-%m-%d").date()).days
            if days >= f["interval_days"]:
                due.append((p["common_name"], f"{days}d since last ({f['npk_preference']})"))
    if due:
        lines.append("## Fertilizer due")
        lines += [f"- **{n}**: {msg}" for n, msg in due]
        lines.append("")

    # Pest watch by month
    month = today.strftime("%b")
    watch = []
    for p in plants:
        for pest in p.get("pests", []):
            if month[:3] in pest.get("watch_window", "") or _month_in_window(today.month, pest.get("watch_window", "")):
                watch.append(f"- **{p['common_name']}** — {pest['pest']}: inspect; first response: {pest['ipm_first']}")
    if watch:
        lines += ["## Pest watch (in season now)"] + sorted(set(watch)) + [""]

    # Overwintering season
    if (today.month == 8 and today.day >= 15) or today.month in (9, 10):
        lines += ["## Overwintering season",
                  "Fall transition window is open — run the overwintering skill for the "
                  "dig-up / bring-in / cover checklist per plant.", ""]

    print("\n".join(lines))

MONTHS = {m: i+1 for i, m in enumerate(
    ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"])}

def _month_in_window(month_num, window):
    # window like "Jun-Aug" or "May-June"
    try:
        a, b = [w.strip()[:3] for w in window.split("-")]
        return MONTHS[a] <= month_num <= MONTHS[b]
    except Exception:
        return False

if __name__ == "__main__":
    main()
