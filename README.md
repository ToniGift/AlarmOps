# AlarmOps

Agent-driven GitLab pipeline that reviews, tests, scans, documents, deploys and
monitors changes to industrial **alarm-limit** configuration.
**This is a simulation. It does not connect to real plant equipment.**

Built for the GitLab Transcend "Life After Code" hackathon. License: MIT.

> Status: Phases 1-2 (application, replay harness, gate scripts). Pipeline,
> agents and full docs come in later phases.

## Run it locally

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt && pip install -e .
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
