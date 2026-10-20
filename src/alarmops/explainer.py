"""Render the plain-English explainer page from measured results (see scenarios.build_report)."""
from __future__ import annotations

from html import escape
from typing import Any

from .labpage import LAB_CSS, render_lab

CSS = """
:root{--bg:#fafaf7;--fg:#1f2430;--mute:#5b6270;--card:#fff;--line:#e2e4ea;--ok:#1b7f4b;--bad:#b3261e;--warn:#9a6700;--accent:#2f5bd8}
@media (prefers-color-scheme:dark){:root{--bg:#14161c;--fg:#e8eaf0;--mute:#a0a6b4;--card:#1c1f27;--line:#2c303b;--ok:#52c98b;--bad:#ff8a80;--warn:#e3b341;--accent:#8aa4ff}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:17px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
main{max-width:920px;margin:0 auto;padding:24px 16px 64px}h1{font-size:2rem;margin:.2em 0}h2{margin:1.8em 0 .4em;font-size:1.35rem}
.sim{background:var(--card);border:1px solid var(--warn);border-left:6px solid var(--warn);padding:10px 14px;border-radius:8px;margin:16px 0}
.lead{font-size:1.15rem;color:var(--mute)}
.steps{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;list-style:none;padding:0;counter-reset:s}
.steps li{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 12px;counter-increment:s;font-size:.95rem}
.steps li::before{content:counter(s);display:inline-block;width:1.5em;height:1.5em;line-height:1.5em;text-align:center;border-radius:50%;background:var(--accent);color:#fff;margin-right:.5em;font-size:.8rem}
.steps li.human{border:2px solid var(--warn)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px}
.card h3{margin:.1em 0 .3em;font-size:1.05rem}.verdict{font-weight:700;margin:.5em 0}
.blocked{color:var(--bad)}.passed{color:var(--ok)}.big{font-size:1.6rem;font-weight:700}
.mute{color:var(--mute);font-size:.92rem}svg{width:100%;height:auto;background:var(--card);border:1px solid var(--line);border-radius:10px}
details{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 14px;margin-top:12px}
table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;font-size:.95rem}
code{font-size:.9em}
"""

STAGES = [
    ("Plan", "Check the change is well-formed."),
    ("Review", "Replay simulated faults on the old and new limits, and compare."),
    ("Test", "Run the automatic tests."),
    ("Security", "Scan for passwords and keys saved in the code."),
    ("Compliance", "Write the change record and a parts list (SBOM)."),
    ("Deploy to staging", "Release to a practice environment."),
    ("Validate", "Check the practice release works."),
    ("Human approval", "A person decides. This is the only manual step."),
    ("Monitor", "Watch alarm counts after release and open an issue if they drift."),
]


def _pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def chart_svg(rep: dict[str, Any]) -> str:
    """Tank level over time, with the labelled faults and the old and widened limits."""
    t, y = rep["series"]["t"], rep["series"]["tank_level"]
    n = max(t) or 1
    w, h, pad = 900, 280, 36
    ymax = max(100.0, max(y))
    sx = lambda v: pad + (w - 2 * pad) * v / n
    sy = lambda v: h - pad - (h - 2 * pad) * v / ymax
    pts = " ".join(f"{sx(t[i]):.1f},{sy(y[i]):.1f}" for i in range(0, len(t), 4))
    base_hi = rep["tank"]["high"]
    a = rep["scenarios"]["a"]
    missed = {m["fault_id"] for m in a["newly_missed"]}
    bands = []
    for f in rep["tank_faults"]:
        x0, x1 = sx(f["start"]), max(sx(f["end"]), sx(f["start"]) + 4)
        colour = "#b3261e" if f["fault_id"] in missed else "#2f5bd8"
        bands.append(f'<rect x="{x0:.1f}" y="{pad}" width="{x1 - x0:.1f}" height="{h - 2 * pad}" '
                     f'fill="{colour}" opacity="0.22"/>')
    return f"""<svg viewBox="0 0 {w} {h}" role="img" aria-label="Tank level over time with injected faults, the current high limit and a widened limit">
{''.join(bands)}
<polyline points="{pts}" fill="none" stroke="#6b7280" stroke-width="1"/>
<line x1="{pad}" x2="{w - pad}" y1="{sy(base_hi):.1f}" y2="{sy(base_hi):.1f}" stroke="#1b7f4b" stroke-width="2"/>
<text x="{w - pad - 4}" y="{sy(base_hi) + 17:.1f}" text-anchor="end" font-size="13" fill="#1b7f4b">current high limit ({base_hi:g})</text>
<line x1="{pad}" x2="{w - pad}" y1="{sy(a['high']):.1f}" y2="{sy(a['high']):.1f}" stroke="#b3261e" stroke-width="2" stroke-dasharray="7 5"/>
<text x="{w - pad - 4}" y="{sy(a['high']) - 5:.1f}" text-anchor="end" font-size="13" fill="#b3261e">widened limit ({a['high']:g})</text>
<text x="{pad}" y="{h - 8}" font-size="12" fill="#6b7280">time (simulated samples)</text>
<text x="{pad}" y="{pad - 10}" font-size="12" fill="#6b7280">tank level (%)</text>
</svg>"""


def _card_a(rep: dict) -> str:
    a, b = rep["scenarios"]["a"], rep["baseline"]
    verdict = "BLOCKED" if a["blocked"] else "Allowed"
    cls = "blocked" if a["blocked"] else "passed"
    missed = len(a["newly_missed"])
    return f"""<div class="card"><h3>Change A: someone loosens a limit</h3>
<p>The tank's "too full" alarm is moved from {rep['tank']['high']:g}% up to {a['high']:g}%.</p>
<p class="big">{b['faults_detected']} of {b['faults_total']} <span class="mute">before</span><br>{a['faults_detected']} of {a['faults_total']} <span class="mute">after</span></p>
<p>Simulated faults the system notices. After the change it would have missed {missed} more.</p>
<p class="verdict {cls}">{verdict} before it could ship.</p></div>"""


def _card_b() -> str:
    return """<div class="card"><h3>Change B: a password is saved in the code</h3>
<p>Someone commits a key that gives access to a cloud account. (The key in the demo is fake.)</p>
<p class="big">Not a limit change</p>
<p>It is not about alarms, so there is no detection figure. A scanner looks for secrets in every change.</p>
<p class="verdict blocked">BLOCKED by the security check.</p></div>"""


def _card_c(rep: dict) -> str:
    c = rep["scenarios"]["c"]
    ok = not c["blocked"]
    verdict = "Passes every check and waits for a person to approve it." if ok else "BLOCKED."
    return f"""<div class="card"><h3>Change C: a safe tightening</h3>
<p>The "too full" alarm is moved from {rep['tank']['high']:g}% down to {c['high']:g}%, so it speaks up earlier.</p>
<p class="big">{c['faults_detected']} of {c['faults_total']}</p>
<p>Simulated faults noticed, with {c['false_alarm_count']} false alarms.</p>
<p class="verdict {'passed' if ok else 'blocked'}">{verdict}</p></div>"""


def render_explainer(rep: dict[str, Any], interactive: bool = False) -> str:
    base, gate = rep["baseline"], rep["gate"]
    steps = "".join(
        f'<li class="{"human" if name == "Human approval" else ""}"><b>{escape(name)}</b><br>'
        f'<span class="mute">{escape(text)}</span></li>' for name, text in STAGES)
    tag_rows = "".join(
        f"<tr><td>{escape(tag)}</td><td>{v['faults_detected']} / {v['faults_total']}</td>"
        f"<td>{v['false_alarms']}</td></tr>" for tag, v in rep["per_tag"].items())
    a = rep["scenarios"]["a"]
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AlarmOps explained</title><style>{CSS}{LAB_CSS if interactive else ''}</style></head><body><main>
<h1>AlarmOps</h1>
<p class="lead">Before anyone changes a safety alarm, this system measures what the change would do, and a person approves only the final step.</p>
<div class="sim"><b>This is a simulation.</b> It uses made-up sensor readings. It is not connected to any real plant or equipment.</div>

<h2>The problem</h2>
<p>In a factory, an <b>alarm limit</b> is the number at which the control system warns an operator. For example: "tell someone if the tank is more than 80% full."
Over the years people edit these numbers. If a limit is loosened by mistake, a real problem can happen with <b>no warning at all</b>. If it is tightened too far, operators drown in false alarms and start ignoring them.
Today these edits are usually checked by eye, and nobody measures what they really do.</p>

<h2>What AlarmOps does</h2>
<p>Every proposed change goes through nine automatic steps. Only one needs a human.</p>
<ol class="steps">{steps}</ol>

<h2>See it in action</h2>
<p>We made up {base['faults_total']} faults (sudden spikes, slow drifts, stuck readings) and hid them in simulated sensor data.
The tank chart below shows the real simulated data. Shaded bands are the hidden faults. The red bands are the ones a <b>widened limit would miss</b>.</p>
{chart_svg(rep)}
<p class="mute">Green line: the current limit. Red dashed line: the loosened limit from change A. Red bands: faults that would go unnoticed.</p>

<div class="cards">{_card_a(rep)}{_card_b()}{_card_c(rep)}</div>
<p class="mute">Figures come from replaying the data on each version of the rules, every time this page is built. None are typed in by hand.</p>

{render_lab(rep) if interactive else ''}
<h2>What this is not</h2>
<ul><li>It is a <b>simulation</b>, not a product for real plants.</li>
<li>The mapping to industry standards (ISA-18.2, IEC 62443) is a <b>reference, not a certification</b>.</li>
<li>The pass/fail thresholds are choices for this demo, not an industry standard.</li></ul>

<details><summary>For engineers</summary>
<p>Baseline: {base['faults_detected']}/{base['faults_total']} faults detected, {base['false_alarm_count']} false alarms.
Gate: at least {_pct(gate['min_detection_rate'])} detection, drop of at most {_pct(gate['max_detection_rate_drop'])} versus the target branch,
at most {int(gate['max_false_alarms'])} false alarms, at most {int(gate['max_false_alarm_increase'])} added.</p>
<table><tr><th>Tag</th><th>Faults detected</th><th>False alarms</th></tr>{tag_rows}</table>
<p>Change A ({escape(', '.join(a['violations']) or 'no violations')}).</p>
<p>A fault counts as detected when an alarm for its tag starts between the fault's start and {rep['meta']['detection_window_samples']} samples after its end.
JSON: <a href="/api/replay"><code>/api/replay</code></a>. Source: MIT licensed.</p></details>
</main></body></html>
"""
