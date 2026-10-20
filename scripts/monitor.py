#!/usr/bin/env python3
"""Watch the simulated post-deploy alarm rate; on drift, write a diagnosis and open a GitLab issue.

Log format: CSV with an 'hour' column and one alarm-count column per tag.
Exit codes: 0 = ok (or drift reported), 3 = drift detected and --fail-on-drift set, 2 = error.
"""
import argparse
import csv
import os
import sys
from pathlib import Path

import _common  # noqa: F401

from alarmops import gitlab_api

ISSUE_TITLE = "AlarmOps monitor: alarm-rate drift after deployment"


def load_log(path):
    with open(path, newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise ValueError("alarm log is empty")
    tags = [c for c in rows[0] if c != "hour"]
    return tags, [{t: int(r[t]) for t in tags} for r in rows]


def analyse(tags, rows, baseline_hours, recent_hours, factor, min_increase):
    if len(rows) < baseline_hours + recent_hours:
        raise ValueError(f"need at least {baseline_hours + recent_hours} hours of log, got {len(rows)}")
    base, recent = rows[:baseline_hours], rows[-recent_hours:]
    mean = lambda rs, t: sum(r[t] for r in rs) / len(rs)
    per_tag = {t: {"baseline": mean(base, t), "recent": mean(recent, t)} for t in tags}
    b_total = sum(v["baseline"] for v in per_tag.values())
    r_total = sum(v["recent"] for v in per_tag.values())
    threshold = max(b_total * factor, b_total + min_increase)
    return {"baseline_per_hour": b_total, "recent_per_hour": r_total, "threshold": threshold,
            "drift": r_total > threshold, "per_tag": per_tag}


def diagnosis(res, a):
    top = max(res["per_tag"].items(), key=lambda kv: kv[1]["recent"] - kv[1]["baseline"])
    lines = [
        f"Alarm rate drifted after deployment (simulated log `{a.log}`).",
        "",
        f"- Baseline (first {a.baseline_hours} h): {res['baseline_per_hour']:.2f} alarms/hour",
        f"- Recent (last {a.recent_hours} h): {res['recent_per_hour']:.2f} alarms/hour",
        f"- Drift threshold: {res['threshold']:.2f} alarms/hour",
        "",
        "| Tag | Baseline /h | Recent /h |", "|---|---|---|",
    ]
    lines += [f"| {t} | {v['baseline']:.2f} | {v['recent']:.2f} |" for t, v in res["per_tag"].items()]
    lines += [
        "",
        f"**Largest contributor:** `{top[0]}` "
        f"({top[1]['baseline']:.2f} -> {top[1]['recent']:.2f} alarms/hour).",
        "",
        "Things to check (hypotheses, not conclusions):",
        f"- Was a limit, deadband or delay for `{top[0]}` tightened in a recent change record?",
        "- Is the signal itself drifting, or is the sensor chattering near a limit?",
        "- Consider a rollback of the latest alarm-limit change and re-run the replay gate.",
    ]
    return "\n".join(lines)


def open_issue(body):
    missing = gitlab_api.missing_env()
    if missing:
        print(f"\n[not opening a GitLab issue: missing env vars {missing}]")
        return
    try:
        existing = gitlab_api.request("GET", "/issues", query={
            "state": "opened", "labels": "alarmops-monitor", "search": ISSUE_TITLE, "in": "title"})
        if existing:
            print(f"open monitoring issue already exists (#{existing[0]['iid']}); not duplicating")
            return
        issue = gitlab_api.request("POST", "/issues", body={
            "title": ISSUE_TITLE, "description": body, "labels": "alarmops-monitor,monitoring"})
        print(f"opened issue #{issue['iid']}")
    except RuntimeError as exc:
        print(f"warning: could not open issue: {exc}", file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--log", default="data/post_deploy_alarm_log_drift.csv")
    ap.add_argument("--baseline-hours", type=int, default=24)
    ap.add_argument("--recent-hours", type=int, default=6)
    ap.add_argument("--factor", type=float, default=2.0)
    ap.add_argument("--min-increase", type=float, default=2.0)
    ap.add_argument("--out", default="out/monitor_diagnosis.md")
    ap.add_argument("--fail-on-drift", action="store_true")
    a = ap.parse_args()
    try:
        tags, rows = load_log(a.log)
        res = analyse(tags, rows, a.baseline_hours, a.recent_hours, a.factor, a.min_increase)
    except (OSError, ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"baseline={res['baseline_per_hour']:.2f}/h recent={res['recent_per_hour']:.2f}/h "
          f"threshold={res['threshold']:.2f}/h")
    if not res["drift"]:
        print("MONITOR: OK, no drift")
        return 0
    body = diagnosis(res, a)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(body + "\n", encoding="utf-8")
    print("MONITOR: DRIFT DETECTED\n")
    print(body)
    open_issue(body)
    return 3 if a.fail_on_drift else 0


if __name__ == "__main__":
    raise SystemExit(main())
