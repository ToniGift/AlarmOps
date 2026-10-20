"""HTML and JavaScript for the interactive lab section (served by web.py only)."""
from __future__ import annotations

from html import escape

LAB_CSS = """
.lab{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px}
.lab h3{margin:.2em 0 .4em;font-size:1.05rem}.row{display:flex;flex-wrap:wrap;gap:10px;align-items:end;margin:8px 0}
.row label{display:flex;flex-direction:column;font-size:.85rem;color:var(--mute)}
.row input{width:96px;padding:6px 8px;font:inherit;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg)}
textarea{width:100%;min-height:70px;padding:8px;font:14px/1.4 ui-monospace,Consolas,monospace;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg)}
button{font:inherit;padding:7px 12px;border:1px solid var(--accent);background:var(--accent);color:#fff;border-radius:6px;cursor:pointer}
button.alt{background:transparent;color:var(--accent)}button:disabled{opacity:.5;cursor:wait}
pre.term{background:#0e1116;color:#d6deeb;padding:12px;border-radius:8px;overflow:auto;font:13px/1.45 ui-monospace,Consolas,monospace;min-height:120px;white-space:pre-wrap;margin:10px 0 0}
.pills{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0 0}.pill{font-size:.8rem;padding:3px 9px;border-radius:99px;border:1px solid var(--line)}
.pill.pass{border-color:var(--ok);color:var(--ok)}.pill.fail{border-color:var(--bad);color:var(--bad)}.pill.manual{border-color:var(--warn);color:var(--warn)}
.pill.skipped,.pill.gitlab{color:var(--mute)}.banner{font-weight:700;margin:8px 0 0}
"""


def render_lab(rep: dict) -> str:
    t, a, c = rep["tank"], rep["scenarios"]["a"], rep["scenarios"]["c"]

    def field(fid: str, label: str, value) -> str:
        return (f'<label>{escape(label)}<input id="{fid}" type="number" step="any" '
                f'value="{escape(format(value, "g"))}" data-default="{escape(format(value, "g"))}"></label>')

    return f"""<h2>Try it yourself</h2>
<p>These buttons run the real AlarmOps code on the server, on the same simulated data. The panel prints what the command line would print.
The website cannot run anything else, and it stores nothing you type.</p>
<div class="lab" id="lab" data-a-high="{a['high']:g}" data-a-hh="{a['high_high']:g}" data-c-high="{c['high']:g}" data-c-hh="{c['high_high']:g}">
<h3>1. Change a limit and run the pipeline checks</h3>
<p class="mute">Edit the tank's alarm limits (percent), or pick a ready-made change.</p>
<div class="row">
{field('tank_low_low', 'low-low', t['low_low'])}{field('tank_low', 'low', t['low'])}
{field('tank_high', 'high', t['high'])}{field('tank_high_high', 'high-high', t['high_high'])}
{field('deadband', 'deadband', t['deadband'])}{field('delay_samples', 'delay (samples)', t['delay_samples'])}
</div>
<div class="row">
<button id="run-compare">Run the checks</button>
<button class="alt" id="preset-a">Load change A (loosen)</button>
<button class="alt" id="preset-c">Load change C (tighten)</button>
<button class="alt" id="preset-reset">Reset</button>
<button class="alt" id="run-baseline">Replay current limits</button>
</div>
<div id="banner" class="banner" aria-live="polite"></div>
<div id="pills" class="pills"></div>

<h3 style="margin-top:1.2em">2. Scan some text for passwords and keys</h3>
<textarea id="scan-text" maxlength="4000" aria-label="Text to scan" placeholder="Paste a config snippet here. Nothing is stored or shown back."></textarea>
<div class="row"><button id="run-scan">Run the secret scan</button><button class="alt" id="scan-example">Insert a fake example key</button></div>

<h3>3. Watch the alarm rate after a release</h3>
<div class="row"><button id="mon-healthy" class="alt">Healthy log</button><button id="mon-drift" class="alt">Drifting log</button></div>

<pre class="term" id="term" aria-live="polite">Pick a button above. Results appear here.</pre>
<p class="mute">Stages marked "GitLab only" are not run by this website; they run in the real pipeline.</p>
</div>
<script src="/lab.js" defer></script>
"""


LAB_JS = r"""
(function () {
  var $ = function (id) { return document.getElementById(id); };
  var term = $("term"), banner = $("banner"), pills = $("pills"), lab = $("lab");
  var ids = ["tank_low_low", "tank_low", "tank_high", "tank_high_high", "deadband", "delay_samples"];
  var buttons = lab.querySelectorAll("button");

  function busy(on) { buttons.forEach(function (b) { b.disabled = on; }); }
  function show(text) { term.textContent = text; }
  function clearVerdict() { banner.textContent = ""; banner.className = "banner"; pills.textContent = ""; }

  function call(url, opts) {
    busy(true);
    return fetch(url, opts).then(function (r) {
      return r.json().then(function (j) { if (!r.ok) { throw new Error(j.error || r.statusText); } return j; });
    }).catch(function (e) { clearVerdict(); show("error: " + e.message); return null; })
      .then(function (j) { busy(false); return j; });
  }

  function query() {
    return ids.map(function (i) { return i + "=" + encodeURIComponent($(i).value); }).join("&");
  }

  function drawStages(stages) {
    pills.textContent = "";
    stages.forEach(function (s) {
      var p = document.createElement("span");
      p.className = "pill " + s.status;
      var label = s.status === "gitlab" ? "GitLab only" : s.status;
      p.textContent = s.stage + ": " + label;
      p.title = s.job + " - " + s.detail;
      pills.appendChild(p);
    });
  }

  function setLimits(high, hh) { $("tank_high").value = high; $("tank_high_high").value = hh; }

  $("preset-a").onclick = function () { setLimits(lab.dataset.aHigh, lab.dataset.aHh); };
  $("preset-c").onclick = function () { setLimits(lab.dataset.cHigh, lab.dataset.cHh); };
  $("preset-reset").onclick = function () {
    ids.forEach(function (i) { $(i).value = $(i).dataset["default"]; });
    clearVerdict(); show("Reset to the current limits.");
  };

  $("run-compare").onclick = function () {
    call("/api/lab/compare?" + query()).then(function (r) {
      if (!r) { return; }
      show(r.output);
      banner.textContent = r.passed ? "PASSES the review gate. It would continue to the human approval step."
                                    : "BLOCKED. The change would not be merged.";
      banner.className = "banner " + (r.passed ? "passed" : "blocked");
      drawStages(r.stages);
    });
  };
  $("run-baseline").onclick = function () {
    call("/api/lab/baseline").then(function (r) { if (r) { clearVerdict(); show(r.output); } });
  };
  $("run-scan").onclick = function () {
    call("/api/lab/scan", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: $("scan-text").value })
    }).then(function (r) {
      if (!r) { return; }
      show(r.output);
      banner.textContent = r.blocked ? "BLOCKED by the security check." : "Nothing suspicious found.";
      banner.className = "banner " + (r.blocked ? "blocked" : "passed");
      pills.textContent = "";
    });
  };
  $("scan-example").onclick = function () {
    // a FAKE key, assembled at run time so this file never contains a key-shaped string
    $("scan-text").value = "aws_access_key_id=" + "AKIA" + "ABCDEFGHIJKLMNOP" + "\nregion=eu-west-1\n";
  };
  ["healthy", "drift"].forEach(function (name) {
    $("mon-" + name).onclick = function () {
      call("/api/lab/monitor?log=" + name).then(function (r) {
        if (!r) { return; }
        show(r.output); pills.textContent = "";
        banner.textContent = r.drift ? "DRIFT detected. In GitLab this opens an issue." : "No drift.";
        banner.className = "banner " + (r.drift ? "blocked" : "passed");
      });
    };
  });
})();
"""
