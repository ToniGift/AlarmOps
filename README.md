# AlarmOps

Agent-driven GitLab pipeline that reviews, tests, scans, documents, deploys and
monitors changes to industrial **alarm-limit** configuration.
**This is a simulation. It does not connect to real plant equipment.**

Built for the GitLab Transcend "Life After Code" hackathon. License: MIT.

> Status: Phases 1-4 done (app, replay harness, gate scripts, CI pipeline, local runner,
> demo branches). Full docs and Duo agent setup come next.

## Pipeline

`plan` -> `review` -> `test` -> `security` -> `compliance` -> `deploy_staging` ->
`validate` -> `approve` (manual, default branch only) -> `monitor`.
Deployment is **simulated**: a release is `alarms.yaml` plus a hashed manifest,
verified before the human-approved promotion to "production".

## Run it locally

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt && pip install -e .
python data/generate_dataset.py                      # optional: regenerate (seeded)
python -m pytest -q
python -m alarmops.replay --rules alarms.yaml --out reports/baseline.json
python -m alarmops.service --rules alarms.yaml --limit 5
```

## Gate a change

```bash
python scripts/compare_replay.py --base-ref main --head-rules alarms.yaml   # exit 1 = blocked
python scripts/change_record.py  --base-ref main --head-rules alarms.yaml
python scripts/monitor.py --log data/post_deploy_alarm_log_drift.csv
```

All detection and false-alarm figures are measured by replaying the simulated,
fault-labelled dataset in `data/`. Thresholds live in `gate.yaml`.

## Run everything locally (no GitLab needed)

```bash
pip install -r requirements-dev.txt && pip install -e .
pip install cyclonedx-bom            # optional: enables the SBOM job locally

python scripts/local_pipeline.py     # all stages on the current branch (asks at the approval gate)
python scripts/make_demo_branches.py # once: creates demo-change-a / -b / -c
python scripts/local_demo.py         # runs the pipeline on all three and prints a summary
```

What you should see:

| Branch | Change | Result |
|---|---|---|
| `demo-change-a` | widens the tank `high` limit | blocked at `review`: detection falls from 100% to 81% (17/21) |
| `demo-change-b` | adds a fake credential file | blocked at `security` |
| `demo-change-c` | safe tightening | passes every stage, then waits for human approval |

Per-job logs are written to `out/local/`. The fake credential on `demo-change-b` is
fake and must never be merged.
