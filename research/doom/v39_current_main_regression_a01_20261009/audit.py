#!/usr/bin/env python3
"""Independently validate source pins, predecessor drift, and saved test output."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
FREEZE = json.loads((ROOT / "FREEZE.json").read_text())
RESULT = json.loads((ROOT / "RESULT.json").read_text())
PINS = json.loads((ROOT / "SOURCE_PINS.json").read_text())
PREVIOUS = json.loads((ROOT / "PREDECESSOR_SOURCE_PINS.json").read_text())
errors = []


def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()


if PINS["commit"] != FREEZE["main_commit"]:
    errors.append("current source pin commit differs from freeze")
if len(PINS["source_files"]) != FREEZE["current_source_pin_count"]:
    errors.append("current source pin count differs from freeze")
if len(PREVIOUS["source_files"]) != FREEZE["predecessor_a14_pin_count"]:
    errors.append("predecessor source pin count differs from freeze")
if PREVIOUS.get("commit") != FREEZE["predecessor_a14_commit"]:
    errors.append("predecessor pin commit differs from freeze")

for item in PINS["source_files"]:
    path = item["path"]
    try:
        blob = git("rev-parse", f"{PINS['commit']}:{path}")
        content = subprocess.check_output(["git", "show", f"{PINS['commit']}:{path}"])
    except subprocess.CalledProcessError:
        errors.append(f"missing current source: {path}")
        continue
    if blob != item["git_blob"]:
        errors.append(f"git blob mismatch: {path}")
    if hashlib.sha256(content).hexdigest() != item["sha256"]:
        errors.append(f"sha256 mismatch: {path}")

for item in PREVIOUS["source_files"]:
    path = item["path"]
    try:
        blob = git("rev-parse", f"{PREVIOUS['commit']}:{path}")
        content = subprocess.check_output(
            ["git", "show", f"{PREVIOUS['commit']}:{path}"])
    except subprocess.CalledProcessError:
        errors.append(f"missing predecessor source: {path}")
        continue
    if blob != item["git_blob"]:
        errors.append(f"predecessor git blob mismatch: {path}")
    if hashlib.sha256(content).hexdigest() != item["sha256"]:
        errors.append(f"predecessor sha256 mismatch: {path}")

current = {item["path"]: item["git_blob"] for item in PINS["source_files"]}
changed = sorted(
    item["path"] for item in PREVIOUS["source_files"]
    if current.get(item["path"]) != item["git_blob"]
)
if changed != sorted(FREEZE["changed_predecessor_pins"]):
    errors.append(f"predecessor drift mismatch: {changed}")
if changed != sorted(RESULT["changed_predecessor_pins"]):
    errors.append("result changed-source list differs from reconstructed drift")

for mode, filename in (("normal", "run-normal.log"),
                       ("optimized", "run-optimized.log")):
    output = (ROOT / filename).read_text()
    lines = output.splitlines()
    if not lines or lines[0] != "." * RESULT[mode]["tests"]:
        errors.append(f"{mode}: unittest dot count mismatch")
    if not any(re.fullmatch(
            rf"Ran {RESULT[mode]['tests']} tests in [0-9.]+s", line)
            for line in lines):
        errors.append(f"{mode}: test summary missing")
    if "OK" not in lines:
        errors.append(f"{mode}: success marker missing")
    if RESULT[mode]["exit"] != 0 or RESULT[mode]["passed"] != RESULT[mode]["tests"]:
        errors.append(f"{mode}: result record is not a complete pass")

if errors:
    print(json.dumps({"status": "FAIL", "errors": errors}, indent=2))
    sys.exit(1)

print(json.dumps({
    "status": "PASS_SCOPED_SOURCE_AND_OUTPUT_AUDIT",
    "commit": PINS["commit"],
    "source_files_verified": len(PINS["source_files"]),
    "predecessor_source_files_verified": len(PREVIOUS["source_files"]),
    "predecessor_changed_files": changed,
    "normal_tests": RESULT["normal"]["tests"],
    "optimized_tests": RESULT["optimized"]["tests"],
    "scope": "source identity and retained test output only; no live-effect inference"
}, indent=2))
