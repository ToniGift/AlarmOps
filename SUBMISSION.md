# Submission pack

Deadline: **27 Oct 2026, 13:00 UTC** (14:00 in Poland). Plan to submit on **26 Oct**.

## Devpost text description (draft; edit the Duo sentences to match what actually runs)

**Tagline:** Measure every alarm-limit change before it ships; a human approves only production.

**Inspiration / problem.** In industrial plants, alarm limits decide when operators are alerted.
They are edited over time, and a bad edit either hides real faults (limit too wide) or floods
operators with nuisance alarms (too narrow). Alarm-management practice expects controlled
change, but review is manual, the effect on detection is never measured, evidence is collected
by hand, and nothing watches the alarm rate after deployment.

**What it does.** AlarmOps is an agent-driven GitLab pipeline for alarm-limit changes. For
every merge request it replays a simulated, fault-labelled dataset against the old and new
rules and reports the change in fault-detection rate and false-alarm count. A change that loses
too much detection is blocked, and the measured numbers are posted on the merge request.
Secret detection blocks hard-coded credentials. The pipeline then generates a change record and
an SBOM, deploys to staging, validates the release, and waits for a human to approve production
(Supervised autonomy). After deployment a monitor watches the alarm rate and opens an issue with
a diagnosis when it drifts. A web page explains the system in plain English and has a "Try it yourself" lab where
anyone can edit a limit and watch the real gate pass or block it. <!-- Edit: describe each Duo flow that actually runs. -->

**How we used GitLab.** GitLab CI/CD for nine stages (plan, review, test, security, compliance,
deploy_staging, validate, approve, monitor), GitLab Secret Detection, merge request comments,
environments with a manual production gate, scheduled pipelines and issues for monitoring, and
GitLab Duo Agent Platform flows for merge request review, triage and diagnosis. Together these
touch all nine lifecycle stages.

**Results.** On the committed dataset (21 labelled faults): baseline detects 21/21 with 0 false
alarms. Widening a tank limit drops detection to 17/21 and is blocked. A safe tightening keeps
21/21 and passes to the approval gate. The monitor detects a simulated drift from 0.79 to 13.67
pump-pressure alarms per hour.

**Limitations.** Simulation only: synthetic data, simulated deployment, no real plant
connection. Standards references are a mapping, not a certification.

**Built with:** GitLab Duo Agent Platform, GitLab CI/CD, GitLab Secret Detection, Python,
PyYAML, pytest, CycloneDX, Docker.

## Fields to have ready

- [ ] Public GitLab repository URL (MIT license visible in the About section)
- [ ] YouTube video URL (public, under 3 minutes)
- [ ] Text description (above)
- [ ] Path: **A: Start Fresh**; autonomy level: **Supervised**
- [ ] Optional bonus: public Cloud Run URL (deploy with `cloud/cloudrun_deploy.sh`; add the URL to the README and Devpost; skip if not live)
- [ ] Optional: Most Environmentally Impactful opt-in (not pursued; skip)

## By-hand checklist

### Now
- [ ] Check GitLab Contributor approval (about 24 business hours after registering)
- [ ] Confirm you are registered on Devpost (the "Join hackathon" button)
- [ ] After approval: find the provisioned group, subgroup and project

### After approval
- [ ] Use the provisioned project; set visibility to **Public**
- [ ] Push `main` and the three `demo-change-*` branches
- [ ] Repository front page shows "MIT License" in the About section
- [ ] Add masked CI/CD variable `GITLAB_API_TOKEN` (project access token, `api` scope)
- [ ] Protect the `production` environment
- [ ] Merge `.gitlab/duo/agent-config.yml` to the default branch
- [ ] Day-1 gate: one Duo flow runs on an MR (see `docs/duo-agents.md`)

### Evidence for judges
- [ ] Open MR A, B, C; wait for pipelines. **Leave A and B unmerged and open**
- [ ] First pipeline run: confirm shared runners work (free accounts may need verification)
- [ ] Confirm `secret_detection` fails on B; if it only warns, `secret_guard` still blocks
- [ ] Confirm the MR comment appears on A and C
- [ ] Merge **C last**; confirm the manual `deploy_production` job appears on `main`; click it
- [ ] Add a pipeline schedule for `monitor_alarm_rate` and run it once
- [ ] Update the status column in `README.md` to match what really runs
- [ ] Never merge `demo-change-b` (fake credential)

### Google Cloud (optional bonus, up to +0.2)
- [ ] Create a Google Cloud project with billing; add a budget alert
- [ ] Install `gcloud`; `gcloud auth login`
- [ ] `gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com`
- [ ] `export GCP_PROJECT_ID=... GCP_REGION=europe-west1` then `sh cloud/cloudrun_deploy.sh`
- [ ] Open the printed URL; try the lab; put the URL in `README.md` (TODO marker) and Devpost
- [ ] Optional CI deploy: add CI variables `GCP_PROJECT_ID`, `GCP_REGION` and a File-type `GCP_SA_KEY`; never commit the key

### Before recording or demoing locally
- [ ] `python scripts/make_demo_branches.py --force` (the demo branches are copies of `main`; rebuild them whenever `main` changes)
- [ ] `python scripts/local_demo.py` and wait for "Back on 'main'" before touching the folder

### Submit
- [ ] Record the video (`DEMO_SCRIPT.md`), upload to YouTube as Public
- [ ] Put the video link in `README.md`
- [ ] Complete the Devpost "Enter a Submission" form; save as draft first
- [ ] Submit on 26 Oct, a day early
- [ ] Do not delete the repo, MRs or branches until after winners are announced (~16 Nov)

## Rules to remember
- The repo must stay public and open source (MIT) for judging.
- Do not put proprietary or unrelated code in this repository. GitLab receives a license
  to use the submission.
- All materials in English.
- AI assistance is not mentioned in the rules either way; the README states it honestly.
