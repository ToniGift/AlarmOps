# AlarmOps

Agent-driven GitLab pipeline that reviews, tests, scans, documents, deploys and
monitors changes to industrial **alarm-limit** configuration.
**This is a simulation. It does not connect to real plant equipment.**

Built for the GitLab Transcend "Life After Code" hackathon. License: MIT.

> Status: Phases 1-3 done (application, replay harness, gate scripts, CI pipeline).
> Demo branches, full docs and Duo agent setup come next.

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
