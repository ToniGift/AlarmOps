# Demo video script (target 2:50, hard limit 3:00)

Rules from the hackathon: under 3 minutes, public on YouTube, shows the automation running,
no third-party trademarks or copyrighted music. Judges need not watch past 3:00.

All numbers below were measured by the replay harness or seen on GitLab. Re-check them against
your screen before recording; if anything differs, say what you see, not what is written here.

## Before recording

- [ ] `GITLAB_API_TOKEN` is set (masked, not protected) and the pipelines on A, B and C were re-run
- [ ] MR A: red pipeline, the Duo "Fix CI/CD Pipeline" thread is visible and NOT resolved or applied
- [ ] MR B: red pipeline stopped at `security`; the Secret Detection report shows 1 critical finding
- [ ] MR C: green pipeline; **not merged yet**
- [ ] The README changes are already pushed to `main` (push docs BEFORE merging C, so the pipeline
      you record after the merge is the last one on `main`)
- [ ] `monitor_alarm_rate` has been run once on `main` and a monitoring issue exists
- [ ] Tabs open in order: README, MR A, MR B, MR C, main pipelines, monitoring issue
- [ ] Browser zoom 125%, notifications off, no tokens or personal info on screen
- [ ] Do NOT open the secret finding's detail page on camera (it may display the matched line)
- [ ] Record 1080p, no music

## Script

| Time | On screen | Say |
|---|---|---|
| 0:00 to 0:20 | README top, then the pipeline diagram | "Alarm limits tell plant operators something is wrong. If someone widens a limit by mistake, a real fault raises no alarm, and nobody measures that before the change ships. AlarmOps measures every limit change, and a human approves only the production step. This is a simulation, entered at the Supervised level." |
| 0:20 to 0:48 | **MR A**: the red pipeline stopping at `replay_review`; open the job summary or the CI comment showing 100% to 81.0% and the four missed tank faults | "Change A widens the tank high limit. The pipeline replays simulated faults against the old and new rules. Detection falls from 100 percent to 81 percent: four tank faults are no longer caught. The gate fails the pipeline and the merge is blocked." |
| 0:48 to 1:03 | **MR A**: scroll to the Duo thread on the `alarms.yaml` diff | "I then run GitLab's Duo pipeline-fix agent on the failure. It reads the change, explains that the detection drop broke the gate, and suggests restoring the old limits. I do not apply it, so the change stays blocked." |
| 1:03 to 1:20 | **MR B**: red pipeline at `security`, then the Security scan report (list view only) | "Change B adds a hard-coded credential. GitLab secret detection flags it as a critical finding, an AWS access key, and the pipeline stops at the security stage. The key is fake." |
| 1:20 to 2:05 | **MR C**: full green pipeline graph; open the change record artifact; show the `validate_staging` log. Merge. On `main`, show the manual `deploy_production` job waiting, click it, show the approval record | "Change C tightens the limit safely: 21 of 21 faults still detected, zero false alarms. It passes review, tests, scans and compliance, deploys to staging and is validated. Each change gets a change record and an SBOM. After the merge, production waits for a human. I approve, and the approver is recorded." |
| 2:05 to 2:30 | Monitoring issue with the diagnosis table | "After deployment, a monitor watches the alarm rate. Here the pump pressure alarms jump from under one per hour to nearly fourteen, and the monitor opens an issue with a diagnosis." |
| 2:30 to 2:50 | README lifecycle table | "AlarmOps maps its pipeline jobs onto the nine GitLab lifecycle stages: plan, create, verify, package, secure, release, configure, monitor and govern. The simulation shows how a change gets measured, blocked or approved, then monitored." |

## Check before saying each claim

- "The numbers are posted on the merge request": only say it if the CI comment is visible on MR A.
  Otherwise point at the job summary and drop that phrase.
- "Change record and an SBOM": only say it if both artifacts exist on C's pipeline.
- "Opens an issue with a diagnosis": only say it if the monitoring issue exists. Otherwise show the
  diagnosis file from the job artifacts and say "writes a diagnosis".
- "Approver is recorded": show `manifest.json` from the `deploy_production` job artifacts.
- The Duo beat: only include it if the Duo thread is visible on MR A. Say "GitLab's built-in Duo agent", never "my review agent".
- The nine-stages line: say it only if `monitor_alarm_rate` has run on GitLab. If it has not, drop "monitor" from the list and say "eight".

## Do not say

- Do not claim the Duo agent runs by itself. You triggered it with the "Fix pipeline with Duo" button.
- Do not claim the Duo agent fixed anything. It suggested a fix that you chose not to apply.
- Do not read out the Duo comment's mention of `ci_review.sh` as the place for thresholds. They are in `gate.yaml`.
- Do not claim real-plant safety, certification or compliance. The standards table is a reference mapping.
- Mention Google Cloud Run only if the live URL is on screen.

## After recording

- [ ] Upload to YouTube, visibility **Public** (not unlisted)
- [ ] Length under 3:00, plays without sign-in
- [ ] Put the link in `README.md` and in the Devpost form
- [ ] If you used an AI voice, say so in the video description

## Fallback if GitLab pipelines are not ready

Record the terminal instead: `python scripts/local_demo.py` prints the same A / B / C results.
Say clearly that this is the local runner. This is weaker evidence: the rules ask for visible
CI/CD pipeline history.
