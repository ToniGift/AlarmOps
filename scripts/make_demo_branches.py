#!/usr/bin/env python3
"""Create the three demo branches from the base branch.

  demo-change-a  widens a tank alarm limit        -> the replay gate blocks it
  demo-change-b  adds a fake hard-coded credential -> secret scanning blocks it
  demo-change-c  a safe, valid tightening          -> passes every stage

The credential in B is FAKE and exists only on that branch. Never merge it.
"""
import argparse
import re
import subprocess
import sys

import _common  # noqa: F401
from _common import ROOT

RULES = ROOT / "alarms.yaml"


def git(*args, check=True):
    p = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    if check and p.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed: {p.stderr.strip()}")
    return p


def set_tank(high, high_high):
    """Edit the FIRST tag in alarms.yaml (tank_level)."""
    text = RULES.read_text()
    for key, val in (("high_high", high_high), ("high", high)):
        pattern = rf"(?m)^([ \t]+){key}: [\d.]+[ \t]*$"
        text, n = re.subn(pattern, rf"\g<1>{key}: {val}", text, count=1)
        if n != 1:
            sys.exit(f"could not find '{key}' in alarms.yaml")
    RULES.write_text(text)


def change_a():
    set_tank(88, 95)          # widened: real faults between 80 and 88 are no longer caught


def change_b():
    fake = "AKIA" + "ABCDEFGHIJKLMNOP"     # FAKE key, assembled at runtime
    (ROOT / "demo_fake_secret.txt").write_text(f"aws_access_key_id={fake}\n")


def change_c():
    set_tank(75, 88)          # tightened: still catches every labelled fault


BRANCHES = [
    ("demo-change-a", change_a, "Widen tank_level high limit (demo A: should be blocked by the replay gate)"),
    ("demo-change-b", change_b, "Add a fake credential file (demo B: should be blocked by secret scanning)"),
    ("demo-change-c", change_c, "Tighten tank_level high limits (demo C: valid change)"),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", default=None, help="base branch (default: current branch)")
    ap.add_argument("--force", action="store_true", help="recreate demo branches that already exist")
    a = ap.parse_args()

    base = a.base or git("branch", "--show-current").stdout.strip()
    if git("status", "--porcelain").stdout.strip():
        sys.exit("working tree is not clean; commit or stash your changes first")
    if not git("config", "user.name", check=False).stdout.strip():
        git("config", "user.name", "AlarmOps Demo")
        git("config", "user.email", "demo@example.invalid")
        print("(set a local git identity for this repo)")

    for name, apply, msg in BRANCHES:
        exists = git("rev-parse", "--verify", "-q", name, check=False).returncode == 0
        if exists and not a.force:
            print(f"{name}: already exists (use --force to recreate)")
            continue
        git("checkout", base)
        if exists:
            git("branch", "-D", name)
        git("checkout", "-b", name)
        apply()
        git("add", "-A")
        git("commit", "-m", msg)
        git("checkout", base)
        print(f"{name}: created")
    print(f"\nBack on '{base}'. Next: python scripts/local_demo.py")


if __name__ == "__main__":
    main()
