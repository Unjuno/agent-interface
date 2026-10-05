#!/usr/bin/env python3
"""Read-only structural audit of the V10 release retry artifact."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
lock = json.loads((ROOT / "SOURCE_LOCK.json").read_text())
checks = []

base = subprocess.run(
    ["git", "show", f"{lock['base_commit']}:research/live_control/input_owner_v10.py"],
    cwd=REPO, check=True, capture_output=True,
).stdout
checks.append(hashlib.sha256(base).hexdigest() == lock["base_source_sha256"])
baseline_source = (ROOT / "raw/baseline/input_owner_v10.py").read_bytes()
checks.append(hashlib.sha256(baseline_source).hexdigest() == lock["base_source_sha256"])

for item in (lock["changed_source"], lock["regression_test"]):
    content = (REPO / item["path"]).read_bytes()
    actual = hashlib.sha256(content).hexdigest()
    checks.append(actual == item["sha256"])

test_source = (REPO / lock["regression_test"]["path"]).read_text()
checks.append(hashlib.sha256(
    (ROOT / "raw/baseline/test_input_owner_v10_release_retry.py").read_bytes()
).hexdigest() == lock["regression_test"]["sha256"])
checks.extend(token in test_source for token in (
    "test_cleanup_retries_a_key_still_down_after_explicit_up",
    "test_cleanup_retries_a_wheel_release_omitted_by_server",
    "test_persistent_key_release_failure_remains_unverified",
    'self.assertFalse(receipt["verified"])',
))

source = (REPO / lock["changed_source"]["path"]).read_text()
checks.extend(token in source for token in (
    "for code in down:",
    "for button in buttons_down:",
    "if down or buttons_down:",
    "touched_buttons.add(button)",
))

checks.append("Ran 3 tests" in (ROOT / "raw/test-normal.txt").read_text())
checks.append("Ran 3 tests" in (ROOT / "raw/test-optimized.txt").read_text())
checks.append("Ran 1 test" in (ROOT / "raw/related-cancel-test.txt").read_text())
baseline_output = (ROOT / "raw/baseline/test-baseline.txt").read_text()
checks.append("FAILED (failures=1, errors=1)" in baseline_output)
checks.append("test_cleanup_retries_a_key_still_down_after_explicit_up" in baseline_output)
checks.append("test_cleanup_retries_a_wheel_release_omitted_by_server" in baseline_output)
print(json.dumps({"checks": len(checks), "passed": sum(checks),
                  "status": "PASS" if all(checks) else "FAIL",
                  "scope": "source/hash/raw structural audit only; no runtime or X11 claim"},
                 indent=2, sort_keys=True))
raise SystemExit(0 if all(checks) else 1)
