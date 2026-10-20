import json
import shutil
import threading
import urllib.error
import urllib.request

import pytest
from conftest import BASELINE_RULES, ROOT

from alarmops.explainer import render_explainer
from alarmops.scenarios import build_report, set_tank_limits_text
from alarmops.web import make_handler
from http.server import ThreadingHTTPServer

BASE_TEXT = "tags:\n  tank_level:\n    high: 80\n    high_high: 90\n  other:\n    high: 1\n    high_high: 2\n"


def test_set_tank_limits_only_edits_first_tag():
    out = set_tank_limits_text(BASE_TEXT, 88, 95)
    assert "high: 88" in out and "high_high: 95" in out and "high: 1\n" in out


def test_set_tank_limits_missing_key():
    with pytest.raises(ValueError):
        set_tank_limits_text("tags: {}", 1, 2)


@pytest.fixture(scope="module")
def report(tmp_path_factory):
    # frozen baseline rules, not the live alarms.yaml (which changes with every limit change)
    root = tmp_path_factory.mktemp("root")
    shutil.copy(BASELINE_RULES, root / "alarms.yaml")
    shutil.copy(ROOT / "gate.yaml", root / "gate.yaml")
    shutil.copytree(ROOT / "data", root / "data")
    return build_report(root)


def test_report_measures_the_three_changes(report):
    a, c = report["scenarios"]["a"], report["scenarios"]["c"]
    assert a["blocked"] and a["faults_detected"] < report["baseline"]["faults_detected"]
    assert not c["blocked"] and c["faults_detected"] == report["baseline"]["faults_detected"]
    assert len(a["newly_missed"]) == report["baseline"]["faults_detected"] - a["faults_detected"]


def test_page_uses_measured_numbers_and_says_simulation(report):
    html = render_explainer(report)
    a = report["scenarios"]["a"]
    assert "simulation" in html.lower()
    assert f"{a['faults_detected']} of {a['faults_total']}" in html
    assert "<script" not in html


@pytest.fixture()
def server(report):
    srv = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(report))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()
    srv.server_close()


def get(url, method="GET"):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method=method), timeout=10) as r:
            return r.status, r.headers, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers, e.read()


def test_endpoints(server, report):
    code, hdr, body = get(server + "/healthz")
    assert code == 200 and json.loads(body)["status"] == "ok"
    code, hdr, body = get(server + "/")
    assert code == 200 and b"AlarmOps" in body and hdr["X-Content-Type-Options"] == "nosniff"
    code, _, body = get(server + "/api/replay")
    data = json.loads(body)
    assert code == 200 and data["scenarios"]["a"]["blocked"] and "series" not in data
    assert get(server + "/nope")[0] == 404
    assert get(server + "/", "POST")[0] == 405
    assert get(server + "/", "HEAD")[0] == 200


def test_cloud_run_deploy_is_optional_manual_and_secret_free():
    import yaml
    from conftest import ROOT

    ci = yaml.safe_load((ROOT / ".gitlab-ci.yml").read_text(encoding="utf-8"))
    job = ci["deploy_cloud_run"]
    assert job["allow_failure"] is True and "deploy_production" in job["needs"]
    assert all(r.get("when") == "manual" and "CI_DEFAULT_BRANCH" in r["if"] for r in job["rules"])
    script = (ROOT / "cloud" / "cloudrun_deploy.sh").read_text(encoding="utf-8")
    assert "GCP_PROJECT_ID" in script and "--allow-unauthenticated" in script
    assert "BEGIN PRIVATE KEY" not in script and "private_key" not in script
