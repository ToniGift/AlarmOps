# Demo video script (target 2:50, hard limit 3:00)

Rules from the hackathon: under 3 minutes, public on YouTube, shows the automation running,
no third-party trademarks or copyrighted music. Judges need not watch past 3:00.

All numbers below were measured by the replay harness. Re-check them against your screen
before recording; if anything differs, say what you see, not what is written here.

## Before recording

- [ ] The three merge requests (A, B, C) already have finished pipelines on GitLab
- [ ] Tabs open in this order: README, MR A, MR B, MR C pipeline, monitoring issue
- [ ] Browser zoom 125%, notifications off, no tokens or personal info on screen
- [ ] If the Duo MR review flow works: its comment is visible on MR A
- [ ] Record 1080p, your own voice, no music

## Script

| Time | On screen | Say |
|---|---|---|
| 0:00 to 0:20 | README top, then the pipeline diagram | "Alarm limits tell plant operators something is wrong. If someone widens a limit by mistake, a real fault raises no alarm, and nobody measures that before the change ships. AlarmOps measures every limit change, and a human approves only the production step. This is a simulation, entered at the Supervised level." |
| 0:20 to 0:55 | **MR A**: pipeline graph stopping red at `replay_review`, then the `AlarmOps replay gate` comment | "Change A widens the tank high limit. The pipeline replays simulated faults against the old and new rules. Detection falls from 100 percent to 81 percent: four tank faults are no longer caught. The gate blocks the merge and posts the numbers on the merge request." |
| 0:55 to 1:00 | *(if the flow works)* Duo review comment on MR A | "The Duo review agent explains the risk in plain language." |
| 1:00 to 1:20 | **MR B**: pipeline red at `security` | "Change B adds a hard-coded credential. Secret scanning blocks it at the security stage, and the value is never printed." |
| 1:20 to 2:05 | **MR C**: full green pipeline graph. Open `change_record` artifact. Show `validate_staging` log. Merge. On `main`, show the manual `deploy_production` job waiting, click it, show the approval record | "Change C tightens the limit safely: 21 of 21 faults still detected, zero false alarms. It passes review, tests, scans, compliance, deploys to staging and is validated. Each change gets a change record and an SBOM. Production waits for a human. I approve, and the approver is recorded." |
| 2:05 to 2:30 | Monitoring issue with the diagnosis table | "After deployment, a monitor watches the alarm rate. Here the pump pressure alarms jump from under one per hour to nearly fourteen, and the monitor opens an issue with a diagnosis." |
| 2:30 to 2:50 | README lifecycle table | "AlarmOps touches all nine GitLab lifecycle stages: plan, create, verify, package, secure, release, configure, monitor and govern. The simulation shows how a change gets measured, blocked or approved, then monitored." |

## Do not say

- Do not claim real-plant safety, certification or compliance. The standards table is a
  reference mapping.
- Do not claim a Duo flow does something it did not do on screen.
- Do not claim a Google Cloud deployment unless the public Cloud Run URL is live and you show it on screen.

## After recording

- [ ] Upload to YouTube, visibility **Public** (not unlisted)
- [ ] Length under 3:00, plays without sign-in
- [ ] Paste the link into the Devpost form and into `README.md`

## Fallback if GitLab pipelines are not ready

Record the terminal instead: `python scripts/local_demo.py` prints the same A / B / C results.
Say clearly that this is the local runner. This is weaker evidence: the rules ask for visible
CI/CD pipeline history, so get GitLab pipelines running before submitting.
