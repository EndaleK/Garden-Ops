#!/usr/bin/env python3
"""
build_dashboard.py — bake data/ into a single self-contained dashboard.html.

Reads:  data/garden.json, data/zones.json, data/plants.json,
        data/season-calendar.json, data/treatments.jsonl, data/observations.jsonl
Writes: dashboard.html  (open in any browser)

Design: "Field Almanac" — editorial botanical. Fraunces display serif +
Schibsted Grotesk UI (both with system fallbacks, so it still looks good
OFFLINE), a warm paper "Day" theme and a "Night Garden" dark theme with a
toggle, a season-progress ring, and an SVG sprout favicon.

The dashboard is offline-capable except for one live call to Open-Meteo
(same free, no-key endpoint as scripts/weather.py) which it uses to fetch
the current Edmonton forecast and run the watering math client-side. All
other sections render from baked data + the browser's current date — so the
file stays correct over the season without rebuilding.

Re-run this script any time you change a data/ file.

The client-side watering engine MIRRORS scripts/watering.py. If you change
the constants there, change WATERING_CONSTANTS below to match.

Usage:  python3 scripts/build_dashboard.py
"""
import base64
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent

# Keep in sync with scripts/watering.py
WATERING_CONSTANTS = {
    "SOIL_FACTOR": {"sand": 1.25, "loam": 1.0, "clay": 0.8},
    "ET0_NORM_7D": 28.0,
    "FROST_TMIN_C": 2.0,
    "WIND_GUST_SEVERE_KMH": 70,
}

# Botanical "sprout + sun" mark, used as the favicon and the masthead glyph.
FAVICON_SVG = (
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'>"
    "<rect width='32' height='32' rx='8' fill='#1f4d33'/>"
    "<circle cx='22.5' cy='9.5' r='3.1' fill='#e7b84f'/>"
    "<path d='M16 27 C16 19 16 16 16 13' stroke='#a7e2b3' stroke-width='2.1' "
    "stroke-linecap='round' fill='none'/>"
    "<path d='M16 18 C11.5 18 8.5 14.8 8.5 10.2 C13.4 10.2 16 13 16 18 Z' fill='#5fbf72'/>"
    "<path d='M16 21 C20.5 21 23.5 18 23.5 14 C18.6 14 16 16.6 16 21 Z' fill='#3f8f55'/>"
    "</svg>"
)


def favicon_data_uri():
    b64 = base64.b64encode(FAVICON_SVG.encode("utf-8")).decode("ascii")
    return "data:image/svg+xml;base64," + b64


def load_json(rel):
    return json.loads((ROOT / rel).read_text())


def load_jsonl(rel):
    out = []
    for line in (ROOT / rel).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('{"_comment'):
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return out


def main():
    data = {
        "garden": load_json("data/garden.json"),
        "zones": load_json("data/zones.json")["zones"],
        "plants": load_json("data/plants.json")["plants"],
        "season": load_json("data/season-calendar.json"),
        "treatments": load_jsonl("data/treatments.jsonl"),
        "observations": load_jsonl("data/observations.jsonl"),
        "watering": WATERING_CONSTANTS,
        "built": datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M %Z"),
    }
    payload = json.dumps(data, ensure_ascii=False)
    html = TEMPLATE.replace("/*__DATA__*/null", payload)
    html = html.replace("__FAVICON__", favicon_data_uri())
    out = ROOT / "dashboard.html"
    out.write_text(html, encoding="utf-8")
    print(f"Wrote {out}  ({out.stat().st_size//1024} KB)")
    print(f"  plants: {len(data['plants'])}  zones: {len(data['zones'])}  "
          f"calendar: {len(data['season']['calendar'])}  built: {data['built']}")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en" data-theme="day">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#1f4d33">
<title>Garden Ops — Edmonton</title>
<link rel="icon" href="__FAVICON__">
<link rel="apple-touch-icon" href="__FAVICON__">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<style>
  /* Fonts load from Google when online; fall back to good system faces offline. */
  @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Schibsted+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

  :root{
    --font-display:'Fraunces','Iowan Old Style','Palatino Linotype',Georgia,serif;
    --font-ui:'Schibsted Grotesk',system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;
    --font-mono:'JetBrains Mono',ui-monospace,'SF Mono',Menlo,monospace;
    --r:16px; --r-sm:11px;
    --ease:cubic-bezier(.33,1,.68,1); --spring:cubic-bezier(.34,1.4,.64,1);
  }

  /* ---------- DAY: botanical paper ---------- */
  html[data-theme="day"]{
    --paper:#f3eee2; --paper2:#ece4d3;
    --surface:#fffdf7; --surface2:#f6f0e3; --inset:#efe7d6;
    --line:#e3dac6; --line2:#d3c7ac;
    --ink:#1d2a21; --ink-soft:#54624f; --ink-dim:#8a907c;
    --forest:#2c6a44; --forest2:#388552; --leaf:#4e9e64;
    --amber:#a86f15; --amber-bri:#caa13b; --sky:#2f6f9e; --sky-bri:#5a9ec8;
    --clay:#b14a26; --plum:#7a5aa6;
    --skytop:#dfe7d8; --skybot:#f3eee2;
    --shadow:0 1px 1px rgba(40,50,35,.04), 0 10px 26px -14px rgba(40,55,35,.32);
    --shadow-lg:0 2px 2px rgba(40,50,35,.05), 0 26px 50px -20px rgba(35,55,35,.40);
    --ring-track:#e2dac6; --noise:.05;
    color-scheme:light;
  }
  /* ---------- NIGHT: night garden ---------- */
  html[data-theme="night"]{
    --paper:#0d1410; --paper2:#0a110c;
    --surface:#15201a; --surface2:#1b271f; --inset:#111b15;
    --line:#293a2f; --line2:#34493b;
    --ink:#e9f1e6; --ink-soft:#a9bdad; --ink-dim:#728777;
    --forest:#5fbf72; --forest2:#7fcf9a; --leaf:#5fbf72;
    --amber:#e7b84f; --amber-bri:#f3d182; --sky:#6cb6df; --sky-bri:#95cdec;
    --clay:#e2674f; --plum:#b39ae0;
    --skytop:#13211a; --skybot:#0d1410;
    --shadow:0 1px 0 rgba(255,255,255,.02), 0 12px 30px -16px rgba(0,0,0,.6);
    --shadow-lg:0 1px 0 rgba(255,255,255,.03), 0 30px 60px -22px rgba(0,0,0,.7);
    --ring-track:#26342b; --noise:.04;
    color-scheme:dark;
  }

  *{box-sizing:border-box}
  html,body{margin:0}
  body{
    font-family:var(--font-ui); color:var(--ink); background:var(--paper);
    -webkit-font-smoothing:antialiased; text-rendering:optimizeLegibility;
    padding-bottom:60px; overflow-x:hidden;
  }
  /* paper / texture overlay */
  body::before{
    content:""; position:fixed; inset:0; pointer-events:none; z-index:0; opacity:var(--noise);
    background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  }
  .wrap{width:min(94%,1200px); margin-inline:auto}
  a{color:var(--forest2); text-decoration:none} a:hover{text-decoration:underline}

  /* ---------- masthead ---------- */
  .masthead{position:relative; z-index:1; overflow:hidden;
    background:linear-gradient(180deg,var(--skytop),var(--skybot));
    border-bottom:1px solid var(--line);
  }
  .masthead .hills{position:absolute; left:0; right:0; bottom:-1px; height:120px; opacity:.5; pointer-events:none}
  .mast-inner{display:flex; align-items:center; gap:22px; padding:26px 0 22px; position:relative; z-index:2; flex-wrap:wrap}
  .brand{display:flex; align-items:center; gap:15px; min-width:0}
  .mark{width:54px; height:54px; flex:0 0 auto; border-radius:15px; box-shadow:var(--shadow);}
  .mark svg{display:block; width:100%; height:100%; border-radius:15px}
  .brand-txt h1{font-family:var(--font-display); font-optical-sizing:auto; font-weight:600;
    font-size:clamp(1.9rem,1.2rem+2.4vw,2.9rem); line-height:.96; margin:0; letter-spacing:-.018em;}
  .brand-txt h1 .amp{color:var(--forest2); font-style:italic; font-weight:500}
  .brand-txt p{margin:6px 0 0; color:var(--ink-soft); font-size:13.5px; letter-spacing:.01em}
  .brand-txt .chip{display:inline-flex; align-items:center; gap:6px; padding:2px 9px; border-radius:999px;
    background:color-mix(in srgb,var(--forest2) 14%,transparent); color:var(--forest2);
    border:1px solid color-mix(in srgb,var(--forest2) 30%,transparent); font-weight:600; font-size:11.5px;}

  .mast-right{margin-left:auto; display:flex; align-items:center; gap:20px}
  .today-read{text-align:right; min-width:120px}
  .today-read .big{font-family:var(--font-display); font-weight:600; font-size:30px; line-height:1; letter-spacing:-.02em}
  .today-read .big small{font-size:15px; color:var(--ink-soft)}
  .today-read .lab{font-size:11px; text-transform:uppercase; letter-spacing:.14em; color:var(--ink-dim); margin-bottom:4px}
  .today-read .sub{font-size:12px; color:var(--ink-soft); margin-top:4px}
  .today-read.skel .big{color:var(--ink-dim)}

  .ring{width:104px; height:104px; flex:0 0 auto; position:relative}
  .ring svg{display:block}
  .ring .ringnum{position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center}
  .ring .ringnum b{font-family:var(--font-display); font-weight:600; font-size:26px; line-height:.9}
  .ring .ringnum span{font-size:9.5px; text-transform:uppercase; letter-spacing:.1em; color:var(--ink-dim); margin-top:3px; max-width:80px}

  .theme-btn{width:42px; height:42px; border-radius:12px; border:1px solid var(--line2); cursor:pointer;
    background:var(--surface); color:var(--ink); display:grid; place-items:center; transition:.2s var(--ease); box-shadow:var(--shadow)}
  .theme-btn:hover{transform:translateY(-2px) rotate(-8deg); color:var(--amber)}
  .theme-btn svg{width:20px; height:20px}

  /* ---------- tab bar ---------- */
  .tabbar{position:sticky; top:0; z-index:30;
    background:color-mix(in srgb,var(--paper) 86%,transparent); backdrop-filter:blur(10px) saturate(1.1);
    border-bottom:1px solid var(--line);}
  .tabrow{display:flex; gap:4px; overflow-x:auto; padding:9px 0; scrollbar-width:none}
  .tabrow::-webkit-scrollbar{display:none}
  .tab{display:inline-flex; align-items:center; gap:8px; white-space:nowrap; cursor:pointer;
    font-family:var(--font-ui); font-size:13.5px; font-weight:550; color:var(--ink-soft);
    background:transparent; border:1px solid transparent; border-radius:999px; padding:8px 15px; transition:.18s var(--ease)}
  .tab svg{width:16px; height:16px; opacity:.85}
  .tab:hover{color:var(--ink); background:var(--surface2)}
  .tab.on{color:var(--forest2); background:var(--surface); border-color:color-mix(in srgb,var(--forest2) 34%,transparent);
    box-shadow:var(--shadow); font-weight:650}
  html[data-theme="night"] .tab.on{color:#0c1610; background:var(--forest2); border-color:var(--forest2)}
  html[data-theme="night"] .tab.on svg{opacity:1}

  /* ---------- layout ---------- */
  main{position:relative; z-index:1}
  .pane{animation:rise .5s var(--ease) both}
  @keyframes rise{from{opacity:0; transform:translateY(14px)} to{opacity:1; transform:none}}
  section{margin:30px 0}
  h2.sec{font-family:var(--font-display); font-optical-sizing:auto; font-weight:600; font-size:20px;
    letter-spacing:-.01em; margin:0 0 14px; display:flex; align-items:center; gap:11px; color:var(--ink)}
  h2.sec::after{content:""; height:1px; background:linear-gradient(90deg,var(--line2),transparent); flex:1}
  /* Inline-icon sizing — these icons are raw <svg> with no width/height attrs,
     so without an explicit size they expand to fill their box. Constrain per context. */
  h2.sec > svg{width:21px; height:21px; flex:0 0 auto; color:var(--forest2)}
  .pill > svg{width:13px; height:13px; flex:0 0 auto; vertical-align:-2px; opacity:.85}
  .stat .ic > svg, .alert .ai > svg{width:100%; height:100%; display:block}
  .lead{color:var(--ink-soft); font-size:13.5px; margin:-6px 0 16px}

  .grid{display:grid; gap:15px}
  .cols-2{grid-template-columns:repeat(2,1fr)}
  .cols-3{grid-template-columns:repeat(3,1fr)}
  .cols-4{grid-template-columns:repeat(4,1fr)}
  @media(max-width:920px){.cols-3,.cols-4{grid-template-columns:repeat(2,1fr)}}
  @media(max-width:600px){.cols-2,.cols-3,.cols-4{grid-template-columns:1fr}}

  .card{position:relative; background:var(--surface); border:1px solid var(--line);
    border-radius:var(--r); padding:16px 17px; box-shadow:var(--shadow); transition:transform .22s var(--ease),box-shadow .22s var(--ease),border-color .22s}
  .card.lift:hover{transform:translateY(-4px); box-shadow:var(--shadow-lg); border-color:var(--line2)}
  .card h3{margin:0 0 8px; font-size:15.5px; font-weight:650; letter-spacing:-.005em}
  .card .sub{color:var(--ink-soft); font-size:13px}
  /* category spine */
  .card.spine{padding-left:19px}
  .card.spine::before{content:""; position:absolute; left:0; top:12px; bottom:12px; width:4px; border-radius:4px; background:var(--spineC,var(--leaf))}

  .stat .k{color:var(--ink-dim); font-size:10.5px; text-transform:uppercase; letter-spacing:.13em; margin-bottom:7px}
  .stat .v{font-family:var(--font-display); font-weight:600; font-size:30px; line-height:1; letter-spacing:-.02em}
  .stat .v small{font-size:14px; color:var(--ink-soft); font-weight:500; font-family:var(--font-ui)}
  .stat .sub{margin-top:8px}
  .stat .ic{position:absolute; top:14px; right:14px; width:20px; height:20px; color:var(--ink-dim); opacity:.7}

  .tag{display:inline-flex; align-items:center; gap:5px; padding:3px 9px; border-radius:8px; font-size:11.5px;
    font-weight:650; letter-spacing:.01em; font-family:var(--font-ui)}
  .tag .pip{width:7px;height:7px;border-radius:50%}
  .t-now{background:color-mix(in srgb,var(--clay) 16%,transparent); color:var(--clay); border:1px solid color-mix(in srgb,var(--clay) 36%,transparent)}
  .t-light{background:color-mix(in srgb,var(--amber-bri) 18%,transparent); color:var(--amber); border:1px solid color-mix(in srgb,var(--amber-bri) 40%,transparent)}
  .t-skip{background:color-mix(in srgb,var(--leaf) 16%,transparent); color:var(--forest2); border:1px solid color-mix(in srgb,var(--leaf) 34%,transparent)}
  .t-soon{background:color-mix(in srgb,var(--sky-bri) 16%,transparent); color:var(--sky); border:1px solid color-mix(in srgb,var(--sky-bri) 36%,transparent)}
  .t-muted{background:var(--inset); color:var(--ink-soft); border:1px solid var(--line)}

  .alert{position:relative; border-radius:var(--r); padding:15px 17px 15px 18px; border:1px solid; margin-bottom:12px; display:flex; gap:13px; align-items:flex-start}
  .alert .ai{width:24px; height:24px; flex:0 0 auto; margin-top:1px}
  .alert.frost{background:color-mix(in srgb,var(--sky-bri) 11%,var(--surface)); border-color:color-mix(in srgb,var(--sky) 42%,transparent); color:var(--ink)}
  .alert.frost .ai{color:var(--sky)}
  .alert.severe{background:color-mix(in srgb,var(--clay) 11%,var(--surface)); border-color:color-mix(in srgb,var(--clay) 46%,transparent)}
  .alert.severe .ai{color:var(--clay)}
  .alert.ok{background:color-mix(in srgb,var(--leaf) 9%,var(--surface)); border-color:color-mix(in srgb,var(--leaf) 30%,transparent)}
  .alert.ok .ai{color:var(--forest2)}
  .alert h3{margin:0 0 3px; font-size:15px}
  .alert .who{color:var(--ink-soft); font-size:13.5px; margin-top:5px}
  .alert .who b{color:var(--ink)}

  table{width:100%; border-collapse:collapse; font-size:13.5px}
  th,td{text-align:left; padding:9px 11px; border-bottom:1px solid var(--line); vertical-align:top}
  th{color:var(--ink-dim); font-size:10.5px; text-transform:uppercase; letter-spacing:.09em; font-weight:650}
  tr:last-child td{border-bottom:0}
  td .mono,.mono{font-family:var(--font-mono); font-size:12.5px}

  /* beds */
  .zhead{display:flex; align-items:center; gap:10px; margin-bottom:4px}
  .zid{font-family:var(--font-display); font-weight:600; color:var(--forest2); font-size:22px; line-height:1}
  .zname{font-weight:650; font-size:15px}
  .zmeta{color:var(--ink-soft); font-size:12px; margin:9px 0 8px; display:flex; gap:6px; flex-wrap:wrap}
  .pill{display:inline-flex;align-items:center;gap:5px;padding:3px 9px;border-radius:999px;background:var(--inset);
    border:1px solid var(--line);font-size:11.5px;color:var(--ink-soft)}
  .pill.sensor{color:var(--sky); border-color:color-mix(in srgb,var(--sky) 34%,transparent); background:color-mix(in srgb,var(--sky-bri) 12%,transparent)}
  .plant{display:flex; gap:10px; padding:9px 0; border-top:1px solid var(--line)}
  .plant:first-of-type{border-top:0}
  .dot{width:9px;height:9px;border-radius:50%;margin-top:6px;flex:0 0 auto;background:var(--leaf); box-shadow:0 0 0 3px color-mix(in srgb,var(--leaf) 18%,transparent)}
  .dot.warn{background:var(--amber-bri); box-shadow:0 0 0 3px color-mix(in srgb,var(--amber-bri) 20%,transparent)}
  .dot.bad{background:var(--clay); box-shadow:0 0 0 3px color-mix(in srgb,var(--clay) 20%,transparent)}
  .dot.tbd{background:var(--ink-dim); box-shadow:none}
  .plant .pn{font-weight:600}
  .plant .pm{color:var(--ink-soft); font-size:12.5px; font-family:var(--font-mono)}
  .flag{color:var(--amber); font-size:12px; margin-top:3px}

  .row{display:flex; gap:10px; align-items:center}
  .between{justify-content:space-between}
  .muted{color:var(--ink-soft)} .dim{color:var(--ink-dim)} .small{font-size:12.5px}
  .hsig{color:var(--ink-soft); font-size:12.5px; margin-top:6px; line-height:1.5}
  .hsig b{color:var(--ink)}

  /* timeline */
  .legend{display:flex; gap:15px; flex-wrap:wrap; font-size:12px; color:var(--ink-soft); margin-bottom:12px}
  .legend span{display:inline-flex; align-items:center; gap:6px}
  .swatch{width:10px;height:10px;border-radius:3px;flex:0 0 auto}
  .timeline{display:flex; flex-direction:column}
  .mrow{display:grid; grid-template-columns:58px 1fr; gap:14px; padding:11px 0; border-top:1px solid var(--line)}
  .mrow:first-child{border-top:0}
  .mlabel{font-family:var(--font-display); font-weight:600; font-size:15px; color:var(--ink-dim); padding-top:2px}
  .mlabel.cur{color:var(--forest2)}
  .events{display:flex; flex-direction:column; gap:9px}
  .event{display:flex; gap:10px; align-items:flex-start}
  .event .cat{width:9px;height:9px;border-radius:3px;margin-top:5px;flex:0 0 auto}
  .event .et{font-weight:600; font-size:14px}
  .event .ed{color:var(--ink-soft); font-size:12.5px; line-height:1.5}
  .badge-now{background:var(--forest2); color:#fff; font-weight:700; font-size:10px; padding:1px 7px; border-radius:6px; margin-left:7px; letter-spacing:.03em}
  html[data-theme="night"] .badge-now{color:#0c1610}

  .cat.c-spring_prep,.swatch.c-spring_prep{background:var(--leaf)}
  .cat.c-fertilize,.swatch.c-fertilize{background:var(--plum)}
  .cat.c-harvest,.swatch.c-harvest{background:var(--amber-bri)}
  .cat.c-winter_prep,.swatch.c-winter_prep{background:var(--sky)}
  .cat.c-pest,.swatch.c-pest{background:var(--clay)}
  .cat.c-planting,.swatch.c-planting{background:#7fcf9a}
  .cat.c-maintenance,.swatch.c-maintenance{background:var(--ink-dim)}

  .chartwrap{overflow-x:auto; scrollbar-width:thin}
  svg.fc{display:block; width:100%; min-width:580px; height:230px}
  .skel{position:relative; overflow:hidden; background:var(--inset); border-radius:8px}
  .skel::after{content:"";position:absolute;inset:0;transform:translateX(-100%);
    background:linear-gradient(90deg,transparent,color-mix(in srgb,var(--ink) 7%,transparent),transparent);animation:sh 1.3s infinite}
  @keyframes sh{100%{transform:translateX(100%)}}

  footer{margin-top:34px; padding:18px 0 0; border-top:1px solid var(--line); color:var(--ink-dim); font-size:12.5px; line-height:1.7}
  code{font-family:var(--font-mono); background:var(--inset); padding:1px 6px; border-radius:6px; font-size:12px; color:var(--ink-soft)}
  .err{color:var(--clay)}
  ul.clean{margin:6px 0 0; padding-left:18px} ul.clean li{margin:3px 0}

  :focus-visible{outline:2px solid var(--forest2); outline-offset:2px; border-radius:6px}
  @media (prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.01ms!important;transition-duration:.01ms!important}}
</style>
</head>
<body>
<header class="masthead">
  <svg class="hills" viewBox="0 0 1200 120" preserveAspectRatio="none" aria-hidden="true">
    <path d="M0 90 Q150 50 320 78 T640 70 T960 80 T1200 64 V120 H0 Z" fill="var(--forest2)" opacity=".22"/>
    <path d="M0 104 Q200 72 430 96 T860 92 T1200 96 V120 H0 Z" fill="var(--forest)" opacity=".30"/>
  </svg>
  <div class="wrap mast-inner">
    <div class="brand">
      <span class="mark" id="mark"></span>
      <div class="brand-txt">
        <h1>Garden <span class="amp">&amp;</span> Ops</h1>
        <p><span class="chip" id="gchip">Zone 4a</span> &nbsp;<span id="gsub">Edmonton, AB</span></p>
      </div>
    </div>
    <div class="mast-right">
      <div class="today-read skel" id="mastToday">
        <div class="lab">Today</div><div class="big">—</div><div class="sub">fetching forecast…</div>
      </div>
      <div class="ring" id="seasonRing"></div>
      <button class="theme-btn" id="themeBtn" title="Toggle day / night" aria-label="Toggle day or night theme"></button>
    </div>
  </div>
  <div class="tabbar"><nav class="wrap tabrow" id="tabs" aria-label="Sections"></nav></div>
</header>

<main class="wrap" id="app"><p class="muted" style="padding:30px 0">Loading garden…</p></main>

<script>
const DATA = /*__DATA__*/null;

/* ---------- icons ---------- */
const I = {
  overview:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M19 5l-2 2M7 17l-2 2"/></svg>',
  beds:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="7" rx="1.5"/><rect x="3" y="13" width="18" height="7" rx="1.5"/><path d="M7 4v7M12 4v7M17 13v7"/></svg>',
  water:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11Z"/></svg>',
  harvest:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 13h18l-1.6 6.2a1 1 0 0 1-1 .8H5.6a1 1 0 0 1-1-.8Z"/><path d="M8 13c0-4 1.8-7 4-9M16 13c0-3-1.2-5.5-3-7"/></svg>',
  fert:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M10 3h4M9 7h6l-1 3.5a5 5 0 0 1 2 4V18a3 3 0 0 1-3 3h-2a3 3 0 0 1-3-3v-3.5a5 5 0 0 1 2-4Z"/><path d="M8.5 14h7"/></svg>',
  spring:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21v-8"/><path d="M12 13c-3 0-5-2-5-5 3 0 5 2 5 5Z"/><path d="M12 15c3 0 5-2.2 5-5.5-3.3 0-5 2.2-5 5.5Z"/></svg>',
  winter:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20M4 6l16 12M20 6L4 18"/><path d="M12 5l2 2-2 2-2-2 2-2ZM12 15l2 2-2 2-2-2 2-2Z"/></svg>',
  cal:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4.5" width="18" height="16" rx="2"/><path d="M3 9h18M8 3v4M16 3v4"/></svg>',
  sun:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4.2"/><path d="M12 2v2.4M12 19.6V22M2 12h2.4M19.6 12H22M4.6 4.6l1.7 1.7M17.7 17.7l1.7 1.7M19.4 4.6l-1.7 1.7M6.3 17.7l-1.7 1.7"/></svg>',
  moon:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M20 14.5A8 8 0 1 1 9.5 4a6.3 6.3 0 0 0 10.5 10.5Z"/></svg>',
  drop:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M12 4s5 5.5 5 9.3A5 5 0 0 1 7 13.3C7 9.5 12 4 12 4Z"/></svg>',
  rain:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><path d="M7 16a4 4 0 0 1-.5-7.97A5.5 5.5 0 0 1 17 8.5a3.5 3.5 0 0 1 .5 7"/><path d="M8 19l-1 2M12 19l-1 2M16 19l-1 2"/></svg>',
  flake:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><path d="M12 2v20M3.5 7l17 10M20.5 7l-17 10"/></svg>',
  frost:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20M4 7l16 10M20 7L4 17"/></svg>',
  wind:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9h11a3 3 0 1 0-3-3M3 14h15a3 3 0 1 1-3 3"/></svg>',
  check:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M8.5 12.5l2.5 2.5 4.5-5"/></svg>',
};

/* ---------- helpers ---------- */
const $ = (h)=>{const t=document.createElement('template');t.innerHTML=h.trim();return t.content.firstChild;};
const esc = (s)=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const MONTHS=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const today=new Date();
const todayMMDD=String(today.getMonth()+1).padStart(2,'0')+'-'+String(today.getDate()).padStart(2,'0');
const curMonth=today.getMonth()+1;
const cssvar=(n)=>getComputedStyle(document.documentElement).getPropertyValue(n).trim();
function mmddToOrd(s){if(!s)return null;const[a,b]=s.split('-').map(Number);return a*100+b;}
function inWindow(start,end){if(!start||!end)return false;const t=mmddToOrd(todayMMDD),s=mmddToOrd(start),e=mmddToOrd(end);
  return s<=e?(t>=s&&t<=e):(t>=s||t<=e);}
function daysUntil(mmdd){if(!mmdd)return 9999;const[m,d]=mmdd.split('-').map(Number);const y=today.getFullYear();
  const base=new Date(y,today.getMonth(),today.getDate());let dt=new Date(y,m-1,d);if(dt<base)dt=new Date(y+1,m-1,d);
  return Math.round((dt-base)/86400000);}
function fmtMMDD(s){if(!s)return '';const[m,d]=s.split('-').map(Number);return MONTHS[m-1]+' '+d;}
function fmtDate(iso){return new Date(iso+'T12:00:00').toLocaleDateString(undefined,{weekday:'short',month:'short',day:'numeric'});}

const zoneById=Object.fromEntries(DATA.zones.map(z=>[z.zone_id,z]));
const plantsByZone={}; DATA.zones.forEach(z=>plantsByZone[z.zone_id]=[]);
DATA.plants.forEach(p=>{(plantsByZone[p.zone_id]=plantsByZone[p.zone_id]||[]).push(p);});

/* ---------- live weather (mirrors scripts/weather.py) ---------- */
let WX=null,WXERR=null;
async function fetchWeather(){
  const L=DATA.garden.location;
  const url="https://api.open-meteo.com/v1/forecast?latitude="+L.lat+"&longitude="+L.lon
    +"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,et0_fao_evapotranspiration,wind_gusts_10m_max"
    +"&past_days=7&forecast_days=7&timezone="+encodeURIComponent(L.timezone);
  try{const r=await fetch(url);if(!r.ok)throw new Error("HTTP "+r.status);WX=summarize(await r.json());}
  catch(e){WXERR=e.message||String(e);}
}
function summarize(raw){
  const d=raw.daily,days=[];
  for(let i=0;i<d.time.length;i++)days.push({date:d.time[i],tmax_c:d.temperature_2m_max[i],tmin_c:d.temperature_2m_min[i],
    precip_mm:d.precipitation_sum[i],et0_mm:d.et0_fao_evapotranspiration[i],wind_gust_kmh:d.wind_gusts_10m_max[i]});
  const past=days.slice(0,7),future=days.slice(7),sum=(a,k)=>Math.round(a.reduce((s,x)=>s+(x[k]||0),0)*10)/10,FT=DATA.watering.FROST_TMIN_C;
  return{past_7d:{rain_total_mm:sum(past,'precip_mm'),et0_total_mm:sum(past,'et0_mm'),days:past},
    next_7d:{rain_total_mm:sum(future,'precip_mm'),et0_total_mm:sum(future,'et0_mm'),
      frost_risk_nights:future.filter(x=>x.tmin_c!=null&&x.tmin_c<=FT).map(x=>({date:x.date,tmin_c:x.tmin_c})),days:future}};
}

/* ---------- watering engine (mirrors scripts/watering.py) ---------- */
function computeWatering(){
  if(!WX)return [];
  const C=DATA.watering,rain_past=WX.past_7d.rain_total_mm,et0_past=WX.past_7d.et0_total_mm;
  const rain_next2=Math.round(WX.next_7d.days.slice(0,2).reduce((s,x)=>s+(x.precip_mm||0),0)*10)/10;
  const et_scale=et0_past?Math.max(0.5,Math.min(1.8,et0_past/C.ET0_NORM_7D)):1.0;
  const out=[];
  for(const z of DATA.zones){
    const zp=plantsByZone[z.zone_id]||[];if(!zp.length)continue;
    if(String(z.moisture_source||'').startsWith('sensor:')&&DATA.sensors){
      const vwc=(DATA.sensors[z.moisture_source.split(':')[1]]||{}).vwc_percent;
      if(vwc!=null){let a,r;if(vwc<20){a='WATER NOW';r='sensor '+vwc.toFixed(0)+'% VWC (dry)';}
        else if(vwc<30){a='WATER SOON';r='sensor '+vwc.toFixed(0)+'% VWC';}else{a='SKIP';r='sensor '+vwc.toFixed(0)+'% VWC (moist)';}
        out.push({zone:z.zone_id,name:z.name,action:a,reason:r,source:'sensor'});continue;}
    }
    const demand=Math.max(...zp.map(p=>p.water.weekly_mm))*et_scale;
    const soil=C.SOIL_FACTOR[z.soil_type]??1.0;
    const deficit=Math.round((demand*soil-rain_past-rain_next2)*10)/10;
    const action=deficit>15?'WATER NOW':(deficit>5?'WATER LIGHT':'SKIP');
    out.push({zone:z.zone_id,name:z.name,action,deficit_mm:deficit,source:'weather_model',
      reason:'need ~'+demand.toFixed(0)+'mm/wk (ET ×'+et_scale.toFixed(2)+'), rain past7d '+rain_past+'mm, next48h '+rain_next2+'mm → deficit '+deficit+'mm'});
  }
  return out;
}
const ACT_TAG={'WATER NOW':'t-now','WATER LIGHT':'t-light','WATER SOON':'t-soon','SKIP':'t-skip'};
const ACT_PIP={'WATER NOW':'var(--clay)','WATER LIGHT':'var(--amber-bri)','WATER SOON':'var(--sky)','SKIP':'var(--leaf)'};

/* ---------- fertilizer due (mirrors scripts/daily_brief.py) ---------- */
function lastTreatment(id,type){const ds=DATA.treatments.filter(t=>t.type===type&&(t.plant_ids||[]).includes(id)).map(t=>t.date);return ds.length?ds.sort().slice(-1)[0]:null;}
function fertilizerDue(){
  const due=[];
  for(const p of DATA.plants){
    const f=p.fertilizer||{};if(!f.interval_days||f.interval_days>=999)continue;
    if(curMonth>=8&&['perennial','shrub','tree'].includes(p.type))continue;
    const last=lastTreatment(p.plant_id,'fertilizer');
    if(!last)due.push({name:p.common_name,zone:p.zone_id,msg:'no record — log first feed',npk:f.npk_preference});
    else{const d=Math.round((today-new Date(last))/86400000);if(d>=f.interval_days)due.push({name:p.common_name,zone:p.zone_id,msg:d+'d since last feed',npk:f.npk_preference});}
  }
  return due;
}

/* ---------- masthead bits ---------- */
function renderMast(){
  document.getElementById('mark').innerHTML=document.querySelector('link[rel=icon]')?'<img alt="" src="'+document.querySelector('link[rel=icon]').href+'" width="54" height="54" style="display:block;border-radius:15px">':'';
  const g=DATA.garden;
  document.getElementById('gsub').textContent=g.location.city+', '+g.location.province;
  document.getElementById('gchip').textContent='Zone '+g.hardiness_zone;
  drawSeasonRing();
}
function describeArc(cx,cy,r,a0,a1){
  const pol=(a)=>{const rad=(a-90)*Math.PI/180;return[cx+r*Math.cos(rad),cy+r*Math.sin(rad)];};
  const[x0,y0]=pol(a0),[x1,y1]=pol(a1);const large=(a1-a0)>180?1:0;
  return 'M '+x0+' '+y0+' A '+r+' '+r+' 0 '+large+' 1 '+x1+' '+y1;
}
function drawSeasonRing(){
  const a=DATA.season.climate_anchors||{};
  const y=today.getFullYear();
  const mk=(s)=>{const[m,d]=s.split('-').map(Number);return new Date(y,m-1,d);};
  const start=mk(a.last_spring_frost_avg||'05-07'),end=mk(a.first_fall_frost_avg||'09-22');
  const total=Math.round((end-start)/86400000);
  let frac,big,lab;
  if(today<start){frac=0;big=daysUntil(a.last_spring_frost_avg);lab='days to last frost';}
  else if(today>end){frac=1;big='❄';lab='season closed';}
  else{const day=Math.round((today-start)/86400000)+1;frac=Math.max(0,Math.min(1,day/total));big=day;lab='of ~'+total+' frost-free days';}
  const A0=-122,A1=122,cx=52,cy=52,r=42;
  const prog=A0+(A1-A0)*frac;
  const track=describeArc(cx,cy,r,A0,A1);
  const fill=frac>0?describeArc(cx,cy,r,A0,prog):'';
  const[mx,my]=(a=>{const rad=(prog-90)*Math.PI/180;return[cx+r*Math.cos(rad),cy+r*Math.sin(rad)];})();
  const ring=document.getElementById('seasonRing');
  ring.innerHTML=
    '<svg width="104" height="104" viewBox="0 0 104 104">'+
      '<path d="'+track+'" fill="none" stroke="var(--ring-track)" stroke-width="7" stroke-linecap="round"/>'+
      (fill?'<path d="'+fill+'" fill="none" stroke="var(--forest2)" stroke-width="7" stroke-linecap="round"/>':'')+
      (frac>0&&frac<1?'<circle cx="'+mx+'" cy="'+my+'" r="5" fill="var(--amber-bri)" stroke="var(--surface)" stroke-width="2"/>':'')+
    '</svg>'+
    '<div class="ringnum"><b>'+big+'</b><span>'+lab+'</span></div>';
}
function paintMastToday(){
  const box=document.getElementById('mastToday');
  if(WXERR){box.classList.remove('skel');box.innerHTML='<div class="lab">Today</div><div class="big">—</div><div class="sub err">weather offline</div>';return;}
  if(!WX)return;
  const t=WX.next_7d.days[0];
  box.classList.remove('skel');
  box.innerHTML='<div class="lab">Today · Edmonton</div>'+
    '<div class="big">'+Math.round(t.tmin_c)+'<small>–</small>'+Math.round(t.tmax_c)+'<small>°C</small></div>'+
    '<div class="sub">'+(t.precip_mm||0)+' mm rain · '+WX.next_7d.frost_risk_nights.length+' frost night'+(WX.next_7d.frost_risk_nights.length===1?'':'s')+'/7d</div>';
}

/* ---------- OVERVIEW ---------- */
function paneOverview(){
  const el=document.createElement('div');el.className='pane';
  el.appendChild($('<section><h2 class="sec">'+I.sun+' Today &amp; this week</h2><div class="grid cols-4" id="wxstrip"></div></section>'));
  el.appendChild($('<section><h2 class="sec">'+I.frost+' Alerts</h2><div id="alerts"></div></section>'));
  el.appendChild($('<section><h2 class="sec">'+I.sun+' 7-day forecast</h2><div class="card chartwrap"><div id="fcchart" class="skel" style="height:230px"></div></div></section>'));
  el.appendChild($('<section><h2 class="sec">'+I.water+' Watering — by bed</h2><div class="grid cols-3" id="watergrid"></div></section>'));
  el.appendChild(nowPanel());
  return el;
}
function statTile(ic,k,v,sub){return '<div class="card lift stat">'+(ic?'<span class="ic">'+ic+'</span>':'')+'<div class="k">'+k+'</div><div class="v">'+v+'</div>'+(sub?'<div class="sub small">'+sub+'</div>':'')+'</div>';}
function paintWeather(){
  const strip=document.getElementById('wxstrip');
  if(strip){
    if(WXERR)strip.innerHTML='<div class="card" style="grid-column:1/-1"><div class="err">Live weather unavailable ('+esc(WXERR)+').</div><div class="sub small">Everything else still works — it runs off the calendar + today’s date, not the network. Reconnect and reload for watering &amp; the forecast.</div></div>';
    else if(WX){const t=WX.next_7d.days[0];strip.innerHTML=[
      statTile(I.sun,'Today',Math.round(t.tmin_c)+'–'+Math.round(t.tmax_c)+'<small>°C</small>',(t.precip_mm||0)+' mm rain expected'),
      statTile(I.rain,'Rain · past 7d',WX.past_7d.rain_total_mm+'<small> mm</small>','ET₀ '+WX.past_7d.et0_total_mm+' mm'),
      statTile(I.drop,'Rain · next 7d',WX.next_7d.rain_total_mm+'<small> mm</small>','next 48h drives watering'),
      statTile(I.flake,'Frost nights · 7d',String(WX.next_7d.frost_risk_nights.length),WX.next_7d.frost_risk_nights.length?'see alerts':'none forecast')
    ].join('');}
  }
  paintMastToday();paintAlerts();paintChart();paintWatering();
}
function paintAlerts(){
  const box=document.getElementById('alerts');if(!box)return;
  if(!WX&&!WXERR){box.innerHTML='<div class="alert ok"><span class="ai">'+I.check+'</span><div><h3>Waiting on live forecast…</h3></div></div>';return;}
  if(WXERR){box.innerHTML='<div class="alert severe"><span class="ai">'+I.wind+'</span><div><h3>Forecast offline</h3><div class="who">Frost &amp; severe-weather checks need the live feed. Reconnect and reload.</div></div></div>';return;}
  let html='';
  for(const f of WX.next_7d.frost_risk_nights){
    const tender=[...new Set(DATA.plants.filter(p=>p.frost_tolerance_c!=null&&f.tmin_c<=p.frost_tolerance_c+2).map(p=>p.common_name))];
    html+='<div class="alert frost"><span class="ai">'+I.frost+'</span><div><h3>Frost risk '+fmtDate(f.date)+' · low '+f.tmin_c+'°C</h3>'+
      '<div class="who"><b>Cover or bring in:</b> '+(tender.join(', ')||'check tender plants')+'</div></div></div>';
  }
  const gusty=WX.next_7d.days.slice(0,2).filter(d=>(d.wind_gust_kmh||0)>=DATA.watering.WIND_GUST_SEVERE_KMH);
  if(gusty.length)html+='<div class="alert severe"><span class="ai">'+I.wind+'</span><div><h3>Severe-weather watch</h3><div class="who">Gusts to '+
    Math.max(...gusty.map(d=>Math.round(d.wind_gust_kmh)))+' km/h forecast — move potted plants (P1) under cover and check ECCC for hail (June–Aug hail alley).</div></div></div>';
  if(!html)html='<div class="alert ok"><span class="ai">'+I.check+'</span><div><h3>No frost or severe-weather flags in the next 7 days</h3><div class="who">Keep up watering and pest scouting.</div></div></div>';
  box.innerHTML=html;
}
function smoothPath(pts){ // catmull-rom -> bezier
  if(pts.length<2)return '';
  let d='M '+pts[0][0]+' '+pts[0][1];
  for(let i=0;i<pts.length-1;i++){
    const p0=pts[i-1]||pts[i],p1=pts[i],p2=pts[i+1],p3=pts[i+2]||p2;
    const c1x=p1[0]+(p2[0]-p0[0])/6,c1y=p1[1]+(p2[1]-p0[1])/6;
    const c2x=p2[0]-(p3[0]-p1[0])/6,c2y=p2[1]-(p3[1]-p1[1])/6;
    d+=' C '+c1x+' '+c1y+' '+c2x+' '+c2y+' '+p2[0]+' '+p2[1];
  }return d;
}
function paintChart(){
  const box=document.getElementById('fcchart');if(!box)return;
  if(WXERR){box.classList.remove('skel');box.innerHTML='<div class="err" style="padding:20px">Forecast unavailable.</div>';return;}
  if(!WX)return;
  box.classList.remove('skel');
  const days=WX.next_7d.days,W=680,H=230,padL=34,padR=16,padT=22,padB=46,n=days.length,xw=(W-padL-padR)/n;
  const temps=days.flatMap(d=>[d.tmax_c,d.tmin_c]).filter(v=>v!=null);
  let tmin=Math.min(...temps,0),tmax=Math.max(...temps,6);const tr=(tmax-tmin)||1;
  const ty=v=>padT+(H-padT-padB)*(1-(v-tmin)/tr),xc=i=>padL+i*xw+xw/2;
  const maxP=Math.max(2,...days.map(d=>d.precip_mm||0));
  const cAmber=cssvar('--amber-bri'),cSky=cssvar('--sky'),cInkDim=cssvar('--ink-dim'),cClay=cssvar('--clay'),cForest=cssvar('--forest2'),cLine=cssvar('--line');
  const hi=days.map((d,i)=>[xc(i),ty(d.tmax_c)]),lo=days.map((d,i)=>[xc(i),ty(d.tmin_c)]);
  let s='<svg class="fc" viewBox="0 0 '+W+' '+H+'"><defs>'+
    '<linearGradient id="hg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="'+cAmber+'" stop-opacity=".34"/><stop offset="1" stop-color="'+cAmber+'" stop-opacity="0"/></linearGradient></defs>';
  // frost line
  const fy=ty(2);s+='<line x1="'+padL+'" y1="'+fy+'" x2="'+(W-padR)+'" y2="'+fy+'" stroke="'+cSky+'" stroke-dasharray="2 5" opacity=".55"/>'+
    '<text x="'+(W-padR)+'" y="'+(fy-5)+'" fill="'+cSky+'" font-size="9.5" text-anchor="end" opacity=".85">2°C frost line</text>';
  // precip bars
  days.forEach((d,i)=>{const x=padL+i*xw,ph=(H-padT-padB)*((d.precip_mm||0)/maxP);
    s+='<rect x="'+(x+xw*0.30)+'" y="'+(H-padB-ph)+'" width="'+(xw*0.40)+'" height="'+ph+'" rx="2.5" fill="'+cSky+'" opacity=".26"/>';});
  // high area + lines
  const areaD=smoothPath(hi)+' L '+hi[hi.length-1][0]+' '+(H-padB)+' L '+hi[0][0]+' '+(H-padB)+' Z';
  s+='<path d="'+areaD+'" fill="url(#hg)"/>';
  s+='<path d="'+smoothPath(hi)+'" fill="none" stroke="'+cAmber+'" stroke-width="2.4" stroke-linecap="round"/>';
  s+='<path d="'+smoothPath(lo)+'" fill="none" stroke="'+cSky+'" stroke-width="2.4" stroke-linecap="round"/>';
  days.forEach((d,i)=>{const frost=d.tmin_c!=null&&d.tmin_c<=2;
    s+='<circle cx="'+xc(i)+'" cy="'+ty(d.tmax_c)+'" r="2.7" fill="'+cAmber+'"/>';
    s+='<circle cx="'+xc(i)+'" cy="'+ty(d.tmin_c)+'" r="3.1" fill="'+(frost?cClay:cSky)+'"/>';
    s+='<text x="'+xc(i)+'" y="'+(ty(d.tmax_c)-8)+'" fill="'+cAmber+'" font-size="10" font-weight="600" text-anchor="middle">'+Math.round(d.tmax_c)+'</text>';
    s+='<text x="'+xc(i)+'" y="'+(ty(d.tmin_c)+15)+'" fill="'+(frost?cClay:cSky)+'" font-size="10" font-weight="600" text-anchor="middle">'+Math.round(d.tmin_c)+'</text>';
    const dd=new Date(d.date+'T12:00:00');
    s+='<text x="'+xc(i)+'" y="'+(H-25)+'" fill="'+(frost?cClay:cInkDim)+'" font-size="10.5" font-weight="600" text-anchor="middle">'+['Sun','Mon','Tue','Wed','Thu','Fri','Sat'][dd.getDay()]+'</text>';
    s+='<text x="'+xc(i)+'" y="'+(H-12)+'" fill="'+cInkDim+'" font-size="9.5" text-anchor="middle">'+(dd.getMonth()+1)+'/'+dd.getDate()+'</text>';});
  s+='</svg>';
  box.innerHTML='<div class="legend" style="padding:2px 4px 10px"><span><span class="swatch" style="background:'+cAmber+'"></span>High °C</span><span><span class="swatch" style="background:'+cSky+'"></span>Low °C</span><span><span class="swatch" style="background:'+cSky+';opacity:.4"></span>Rain (mm)</span></div>'+s;
}
function paintWatering(){
  const box=document.getElementById('watergrid');if(!box)return;
  if(WXERR){box.innerHTML='<div class="card" style="grid-column:1/-1"><div class="err">Watering needs the live forecast.</div><div class="sub small">Bed soil &amp; plant water-needs are in the Watering tab.</div></div>';return;}
  if(!WX){box.innerHTML='<div class="card skel" style="height:120px"></div>'.repeat(3);return;}
  box.innerHTML=computeWatering().map(r=>waterCard(r)).join('');
}
function waterCard(r){const z=zoneById[r.zone];
  return '<div class="card lift spine" style="--spineC:'+ACT_PIP[r.action]+'">'+
    '<div class="row between"><h3><span class="mono" style="color:var(--forest2)">'+esc(r.zone)+'</span> &nbsp;<span class="muted small" style="font-weight:500">'+esc(z.name)+'</span></h3>'+
    '<span class="tag '+ACT_TAG[r.action]+'"><span class="pip" style="background:'+ACT_PIP[r.action]+'"></span>'+r.action+'</span></div>'+
    '<div class="sub small" style="margin-top:7px">'+esc(r.reason)+'</div>'+
    '<div class="dim small mono" style="margin-top:7px">'+esc(z.soil_type)+' · '+esc(z.irrigation)+' · '+esc(r.source)+'</div></div>';
}

/* ---------- shared "now" panel ---------- */
function nowPanel(){
  const sec=document.createElement('section');sec.innerHTML='<h2 class="sec">'+I.check+' What needs doing now</h2>';
  const items=DATA.season.calendar.map(e=>({...e,_d:daysUntil(e.start),_a:inWindow(e.start,e.end)}))
    .filter(e=>e._a||(e._d>=0&&e._d<=18)).sort((a,b)=>(b._a-a._a)||(a._d-b._d));
  const card=document.createElement('div');card.className='card';
  if(!items.length)card.innerHTML='<div class="muted">Nothing time-critical this week. Keep up watering + pest scouting.</div>';
  else card.innerHTML='<div class="legend">'+legendHtml()+'</div>'+items.map(e=>
    '<div class="event" style="padding:10px 0;border-top:1px solid var(--line)"><span class="cat c-'+e.category+'"></span>'+
    '<div style="flex:1"><div class="et">'+esc(e.title)+(e._a?'<span class="badge-now">ACTIVE</span>':'<span class="muted small"> · in '+e._d+'d</span>')+'</div>'+
    '<div class="ed">'+esc(e.detail)+'</div><div class="dim small mono" style="margin-top:3px">'+fmtMMDD(e.start)+'–'+fmtMMDD(e.end)+(e.zones&&e.zones.length?' · '+e.zones.join(', '):'')+'</div></div></div>').join('');
  sec.appendChild(card);return sec;
}
function legendHtml(){return [['spring_prep','Spring'],['fertilize','Fertilize'],['harvest','Harvest'],['winter_prep','Winter'],['pest','Pest'],['maintenance','Upkeep']]
  .map(([c,l])=>'<span><span class="swatch c-'+c+'"></span>'+l+'</span>').join('');}

/* ---------- BEDS ---------- */
function paneBeds(){
  const el=document.createElement('div');el.className='pane';
  const total=DATA.plants.reduce((s,p)=>s+(p.quantity||1),0);
  el.appendChild($('<section><h2 class="sec">'+I.beds+' Beds &amp; what’s planted where</h2><p class="lead">'+DATA.zones.length+' zones · '+DATA.plants.length+' plant groups · '+total+' plants total. Health dots come from your latest observations.</p><div class="grid cols-2" id="beds"></div></section>'));
  const wrap=el.querySelector('#beds');
  for(const z of DATA.zones){
    const zp=plantsByZone[z.zone_id]||[];const card=document.createElement('div');card.className='card lift';
    const sensor=String(z.moisture_source).startsWith('sensor:');
    let h='<div class="zhead"><span class="zid">'+esc(z.zone_id)+'</span><span class="zname">'+esc(z.name)+'</span></div>'+
      '<div class="zmeta"><span class="pill">☀ '+esc(z.sun_exposure)+'</span><span class="pill">🪨 '+esc(z.soil_type)+'</span><span class="pill">'+I.drop+' '+esc(z.irrigation)+'</span><span class="pill'+(sensor?' sensor':'')+'">'+(sensor?'📡 '+esc(z.moisture_source):'🛰 weather model')+'</span></div>';
    if(z.notes)h+='<div class="dim small" style="margin:-2px 0 8px">'+esc(z.notes)+'</div>';
    if(!zp.length)h+='<div class="muted small">No plants recorded.</div>';
    for(const p of zp){h+='<div class="plant"><span class="dot '+healthDot(p)+'"></span><div style="flex:1">'+
      '<div class="pn">'+esc(p.common_name)+(p.quantity>1?' <span class="muted small mono">×'+p.quantity+'</span>':'')+'</div>'+
      '<div class="pm">'+esc(p.type)+' · '+esc(p.hardiness||'')+' · '+p.water.weekly_mm+'mm/wk</div>'+
      (p.notes?'<div class="flag">⚑ '+esc(firstSentence(p.notes))+'</div>':'')+'</div></div>';}
    card.innerHTML=h;wrap.appendChild(card);
  }
  return el;
}
function healthDot(p){const n=((p.notes||'')+' '+(p.cultivar||'')+' '+p.common_name).toLowerCase();
  if(/tbd|unidentified|id needed|id pending|weed flush/.test(n))return 'tbd';
  if(/damaged|loss|snapped|collapse|dried|dieback|chloros|yellow/.test(n))return 'bad';
  if(/watch|stress|re-stake|recover/.test(n))return 'warn';return '';}
function firstSentence(s){const m=String(s).split(/(?<=[.!])\s/);return m[0].length>120?m[0].slice(0,117)+'…':m[0];}

/* ---------- WATERING tab ---------- */
function paneWater(){
  const el=document.createElement('div');el.className='pane';
  el.appendChild($('<section><h2 class="sec">'+I.water+' Watering schedule</h2><p class="lead">Live water-balance per bed, mirroring <code>scripts/watering.py</code>. Deficit = weekly need (ET-adjusted, soil-weighted) − rain past 7d − rain next 48h. <b>Phase&nbsp;2:</b> a soil sensor on a bed overrides this with measured moisture.</p><div class="grid cols-3" id="wg2"></div></section>'));
  const t=$('<section><h2 class="sec">'+I.drop+' Per-plant water needs</h2><div class="card" style="padding:6px 8px"><table id="wtab"><thead><tr><th>Bed</th><th>Plant</th><th>mm/wk</th><th>Drought</th><th>Notes</th></tr></thead><tbody></tbody></table></div></section>');
  el.appendChild(t);
  const g=el.querySelector('#wg2');
  if(WXERR)g.innerHTML='<div class="card err">Live forecast unavailable — reconnect and reload.</div>';
  else if(!WX)g.innerHTML='<div class="card skel" style="height:120px"></div>'.repeat(3);
  else g.innerHTML=computeWatering().map(r=>waterCard(r)).join('');
  t.querySelector('tbody').innerHTML=DATA.plants.slice().sort((a,b)=>a.zone_id.localeCompare(b.zone_id)).map(p=>
    '<tr><td class="mono"><b>'+esc(p.zone_id)+'</b></td><td>'+esc(p.common_name)+'</td><td class="mono">'+p.water.weekly_mm+'</td><td>'+(p.water.drought_tolerant?'ok':'—')+'</td><td class="muted small">'+esc(p.water.notes||'')+'</td></tr>').join('');
  return el;
}

/* ---------- HARVEST ---------- */
function paneHarvest(){
  const el=document.createElement('div');el.className='pane';
  const rows=DATA.plants.map(p=>{const h=(DATA.season.plant_schedules[p.plant_id]||{}).harvest||{};
    return{p,h,active:inWindow(h.start,h.end),du:daysUntil(h.start),has:!!h.start};});
  const active=rows.filter(r=>r.active).sort((a,b)=>mmddToOrd(a.h.end)-mmddToOrd(b.h.end));
  const up=rows.filter(r=>!r.active&&r.has&&r.du<=120).sort((a,b)=>a.du-b.du);
  const later=rows.filter(r=>!r.active&&r.has&&r.du>120).sort((a,b)=>mmddToOrd(a.h.start)-mmddToOrd(b.h.start));
  const tbd=rows.filter(r=>!r.has);
  el.appendChild(harvestBlock('Ready / in season now',active));
  el.appendChild(harvestBlock('Coming up · next ~4 months',up));
  if(later.length)el.appendChild(harvestBlock('Later this season',later));
  if(tbd.length)el.appendChild(harvestBlock('Needs ID / no harvest expected',tbd));
  return el;
}
function harvestBlock(title,rows){
  const s=document.createElement('section');s.innerHTML='<h2 class="sec">'+I.harvest+' '+esc(title)+'</h2>';
  if(!rows.length){s.appendChild($('<div class="card muted small">Nothing here right now.</div>'));return s;}
  const grid=document.createElement('div');grid.className='grid cols-2';
  rows.forEach(({p,h,active,du})=>grid.appendChild($('<div class="card lift spine" style="--spineC:var(--amber-bri)">'+
    '<div class="row between"><h3>'+esc(p.common_name)+'</h3>'+
    (active?'<span class="tag t-light"><span class="pip" style="background:var(--amber-bri)"></span>IN SEASON</span>':(h.year1?'<span class="tag t-muted">est. year</span>':(du<9999?'<span class="tag t-soon"><span class="pip" style="background:var(--sky)"></span>in '+du+'d</span>':'')))+'</div>'+
    '<div class="dim small mono">'+esc(p.zone_id)+' · '+esc(zoneById[p.zone_id]?.name||'')+'</div>'+
    '<div class="sub" style="margin-top:8px;font-weight:600">'+esc(h.window||'TBD')+'</div>'+
    (h.signal?'<div class="hsig">🔎 '+esc(h.signal)+'</div>':'')+
    (h.pre_harvest?'<div class="hsig">› '+esc(h.pre_harvest)+'</div>':'')+
    (h.post_harvest?'<div class="hsig">📦 '+esc(h.post_harvest)+'</div>':'')+'</div>')));
  s.appendChild(grid);return s;
}

/* ---------- FERTILIZE ---------- */
function paneFert(){
  const el=document.createElement('div');el.className='pane';
  const due=fertilizerDue();
  const s1=document.createElement('section');s1.innerHTML='<h2 class="sec">'+I.fert+' Feeding due now</h2>';
  const c=document.createElement('div');c.className='card';let inner='';
  if(curMonth>=8)inner+='<div class="alert ok" style="margin:0 0 12px"><span class="ai">'+I.check+'</span><div><h3>Aug 1 nitrogen stop is in effect</h3><div class="who">Perennials, shrubs and trees are excluded now (soft late growth winter-kills). Vegetables may still feed.</div></div></div>';
  if(!due.length)inner+='<div class="muted">No feedings overdue per the treatment log. Log applications to <code>data/treatments.jsonl</code> to keep this accurate.</div>';
  else inner+='<table><thead><tr><th>Bed</th><th>Plant</th><th>Status</th><th>Use</th></tr></thead><tbody>'+due.map(d=>'<tr><td class="mono"><b>'+esc(d.zone)+'</b></td><td>'+esc(d.name)+'</td><td class="muted">'+esc(d.msg)+'</td><td class="small">'+esc(d.npk||'')+'</td></tr>').join('')+'</tbody></table>';
  c.innerHTML=inner;s1.appendChild(c);el.appendChild(s1);
  const fcal=DATA.season.calendar.filter(e=>e.category==='fertilize').sort((a,b)=>mmddToOrd(a.start)-mmddToOrd(b.start));
  const s2=document.createElement('section');s2.innerHTML='<h2 class="sec">'+I.cal+' Fertilization calendar</h2>';
  const g=document.createElement('div');g.className='grid cols-2';fcal.forEach(e=>g.appendChild(calCard(e)));s2.appendChild(g);el.appendChild(s2);
  const s3=$('<section><h2 class="sec">'+I.fert+' Per-plant feeding reference</h2><div class="card" style="padding:6px 8px"><table><thead><tr><th>Bed</th><th>Plant</th><th>Product</th><th>Every</th><th>Season</th></tr></thead><tbody>'+
    DATA.plants.slice().sort((a,b)=>a.zone_id.localeCompare(b.zone_id)).map(p=>{const f=p.fertilizer||{};
      return '<tr><td class="mono"><b>'+esc(p.zone_id)+'</b></td><td>'+esc(p.common_name)+'</td><td class="small">'+esc(f.npk_preference||'—')+'</td><td class="mono">'+(f.interval_days&&f.interval_days<999?f.interval_days+'d':'—')+'</td><td class="small muted">'+esc(f.season||'')+'</td></tr>';}).join('')+'</tbody></table></div></section>');
  el.appendChild(s3);return el;
}

/* ---------- PREP (winter / spring) ---------- */
function panePrep(kind){return function(){
  const el=document.createElement('div');el.className='pane';const isW=kind==='winter_prep';
  const cal=DATA.season.calendar.filter(e=>e.category===kind).sort((a,b)=>mmddToOrd(a.start)-mmddToOrd(b.start));
  const s1=document.createElement('section');s1.innerHTML='<h2 class="sec">'+(isW?I.winter:I.spring)+' '+(isW?'Fall &amp; winter prep — garden tasks':'Spring prep — garden tasks')+'</h2>';
  const g=document.createElement('div');g.className='grid cols-2';cal.forEach(e=>g.appendChild(calCard(e)));s1.appendChild(g);el.appendChild(s1);
  const s2=document.createElement('section');s2.innerHTML='<h2 class="sec">'+(isW?I.flake:I.spring)+' '+(isW?'Per-plant overwintering':'Per-plant spring wake-up')+'</h2>';
  const grid=document.createElement('div');grid.className='grid cols-2';
  const STRAT={hardy_leave:'Hardy — leave',mulch_protect:'Mulch / protect',cover_on_frost:'Cover on frost',dig_and_store:'Dig &amp; store',bring_indoors:'Bring indoors',annual_dies:'Annual — replant'};
  for(const p of DATA.plants){
    const sc=DATA.season.plant_schedules[p.plant_id]||{};const tasks=isW?(sc.fall_winter_prep||[]):(sc.spring_prep||[]);const ow=p.overwinter||{};
    if(isW){if(ow.strategy==='annual_dies'&&!tasks.length)continue;
      grid.appendChild($('<div class="card lift spine" style="--spineC:var(--sky)"><div class="row between"><h3>'+esc(p.common_name)+'</h3><span class="tag t-muted">'+(STRAT[ow.strategy]||ow.strategy)+'</span></div>'+
        '<div class="dim small mono">'+esc(p.zone_id)+'</div>'+
        (ow.trigger?'<div class="hsig">⏱ <b>'+esc(ow.trigger)+'</b></div>':'')+
        (ow.instructions?'<div class="hsig">'+esc(ow.instructions)+'</div>':'')+
        tasks.map(t=>'<div class="hsig">📅 '+esc(t.window)+': '+esc(t.task)+'</div>').join('')+'</div>'));
    }else{if(!tasks.length)continue;
      grid.appendChild($('<div class="card lift spine" style="--spineC:var(--leaf)"><div class="row between"><h3>'+esc(p.common_name)+'</h3><span class="dim small mono">'+esc(p.zone_id)+'</span></div>'+
        tasks.map(t=>'<div class="hsig">🌱 <b>'+esc(t.window)+':</b> '+esc(t.task)+'</div>').join('')+'</div>'));}
  }
  s2.appendChild(grid);el.appendChild(s2);return el;
};}

/* ---------- CALENDAR ---------- */
function paneCalendar(){
  const el=document.createElement('div');el.className='pane';
  const s=document.createElement('section');s.innerHTML='<h2 class="sec">'+I.cal+' Season timeline</h2><div class="legend">'+legendHtml()+'</div>';
  const card=document.createElement('div');card.className='card';const tl=document.createElement('div');tl.className='timeline';
  for(let m=1;m<=12;m++){
    const evs=DATA.season.calendar.filter(e=>{const a=mmddToOrd(e.start),b=mmddToOrd(e.end);return Math.floor(a/100)<=m&&Math.floor(b/100)>=m;}).sort((a,b)=>mmddToOrd(a.start)-mmddToOrd(b.start));
    if(!evs.length&&(m<4||m>11))continue;
    const row=document.createElement('div');row.className='mrow';
    row.innerHTML='<div class="mlabel'+(m===curMonth?' cur':'')+'">'+MONTHS[m-1]+'</div><div class="events">'+(evs.length?evs.map(e=>{
      const a=inWindow(e.start,e.end);
      return '<div class="event"><span class="cat c-'+e.category+'"></span><div><div class="et">'+esc(e.title)+(a?'<span class="badge-now">NOW</span>':'')+' <span class="dim small mono">'+fmtMMDD(e.start)+'–'+fmtMMDD(e.end)+'</span></div><div class="ed">'+esc(e.detail)+'</div></div></div>';
    }).join(''):'<div class="muted small">—</div>')+'</div>';
    tl.appendChild(row);
  }
  card.appendChild(tl);s.appendChild(card);el.appendChild(s);
  const o=document.createElement('section');o.innerHTML='<h2 class="sec">'+I.beds+' Recent observations</h2>';
  const oc=document.createElement('div');oc.className='card';
  const obs=DATA.observations.slice().sort((a,b)=>(b.date||'').localeCompare(a.date)).slice(0,12);
  oc.innerHTML=obs.length?'<table><tbody>'+obs.map(o=>'<tr><td class="dim small mono" style="white-space:nowrap">'+esc(o.date)+'</td><td><b class="mono">'+esc(o.zone_id||'')+'</b> <span class="tag t-muted">'+esc(o.type)+'</span></td><td class="small">'+esc(o.observation)+'</td></tr>').join('')+'</tbody></table>':'<div class="muted">No observations logged.</div>';
  o.appendChild(oc);el.appendChild(o);return el;
}
function calCard(e){const a=inWindow(e.start,e.end),du=daysUntil(e.start);
  return $('<div class="card lift spine" style="--spineC:var(--c'+e.category+',var(--leaf))"><div class="row between"><h3><span class="cat c-'+e.category+'" style="display:inline-block;margin-right:8px;vertical-align:middle"></span>'+esc(e.title)+'</h3>'+
    (a?'<span class="badge-now">NOW</span>':(du<9999&&du>0?'<span class="tag t-soon"><span class="pip" style="background:var(--sky)"></span>in '+du+'d</span>':''))+'</div>'+
    '<div class="dim small mono">'+fmtMMDD(e.start)+'–'+fmtMMDD(e.end)+(e.zones&&e.zones.length?' · '+e.zones.join(', '):'')+'</div>'+
    '<div class="sub small" style="margin-top:8px">'+esc(e.detail)+'</div></div>');
}

/* ---------- tabs / theme / boot ---------- */
const PANES=[
  ['Overview',I.overview,paneOverview],
  ['Beds & Plants',I.beds,paneBeds],
  ['Watering',I.water,paneWater],
  ['Harvest',I.harvest,paneHarvest],
  ['Fertilize',I.fert,paneFert],
  ['Spring Prep',I.spring,panePrep('spring_prep')],
  ['Winter Prep',I.winter,panePrep('winter_prep')],
  ['Calendar',I.cal,paneCalendar],
];
let CUR=0;
function mountTabs(){
  const t=document.getElementById('tabs');
  PANES.forEach(([name,icon],i)=>{const b=document.createElement('button');b.className='tab'+(i===0?' on':'');b.dataset.i=i;
    b.innerHTML=icon+'<span>'+name+'</span>';b.onclick=()=>select(i);t.appendChild(b);});
}
function select(i){
  CUR=i;document.querySelectorAll('#tabs .tab').forEach(b=>b.classList.toggle('on',+b.dataset.i===i));
  const app=document.getElementById('app');app.innerHTML='';app.appendChild(PANES[i][2]());app.appendChild(footer());
  if(i===0)paintWeather();
  window.scrollTo({top:0,behavior:'instant'});
}
function footer(){const f=document.createElement('footer');
  f.innerHTML='<b style="font-family:var(--font-display);font-weight:600;color:var(--ink)">Garden Ops</b> · '+esc(DATA.garden.location.city)+' · zone '+esc(DATA.garden.hardiness_zone)+
    ' · built from <code>data/</code> on '+esc(DATA.built)+'. Live weather: Open-Meteo (no key). '+
    'Rebuild after editing data: <code>python3 scripts/build_dashboard.py</code>. '+
    'Phase&nbsp;2: an MQTT soil sensor on a bed auto-overrides its watering recommendation.';
  return f;}

function initTheme(){
  let th='day';try{th=localStorage.getItem('gardenTheme')||'day';}catch(e){}
  setTheme(th);
  document.getElementById('themeBtn').onclick=()=>setTheme(document.documentElement.dataset.theme==='day'?'night':'day');
}
function setTheme(t){
  document.documentElement.dataset.theme=t;
  document.getElementById('themeBtn').innerHTML=t==='day'?I.moon:I.sun;
  document.querySelector('meta[name=theme-color]').setAttribute('content',t==='day'?'#dfe7d8':'#0d1410');
  try{localStorage.setItem('gardenTheme',t);}catch(e){}
  if(window._booted){drawSeasonRing();if(CUR===0)paintChart();} // repaint color-dependent SVG
}
async function boot(){
  initTheme();renderMast();mountTabs();
  const app=document.getElementById('app');app.innerHTML='';app.appendChild(PANES[0][2]());app.appendChild(footer());
  window._booted=true;
  await fetchWeather();paintWeather();
}
boot();
</script>
</body>
</html>"""

if __name__ == "__main__":
    main()
