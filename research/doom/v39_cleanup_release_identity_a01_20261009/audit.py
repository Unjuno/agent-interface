import hashlib
import json
import re
import subprocess
from pathlib import Path


HERE = Path(__file__).resolve().parent
DOOM = HERE.parent
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
errors = []


def check(condition, label):
    if not condition:
        errors.append(label)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


check(sha256(DOOM / "doom_controller_failure_cleanup_v1.py") ==
      FREEZE["candidate_helper_sha256"], "candidate helper SHA-256")
check(sha256(DOOM / "test_controller_failure_cleanup_v39.py") ==
      FREEZE["test_sha256"], "regression test SHA-256")
blob = subprocess.run(
    ["git", "rev-parse", "origin/main:research/doom/doom_controller_failure_cleanup_v1.py"],
    cwd=DOOM, check=True, capture_output=True, text=True).stdout.strip()
check(blob == FREEZE["baseline_helper_git_blob"], "baseline helper Git blob")


def exit_code(name):
    return int((HERE / f"{name}.exit.txt").read_text(encoding="utf-8").strip())


baseline_log = (HERE / "baseline.stderr.txt").read_text(encoding="utf-8")
candidate_log = (HERE / "candidate.stderr.txt").read_text(encoding="utf-8")
check(exit_code("baseline") == 1, "baseline expected failure exit")
check("Ran 3 tests" in baseline_log and "FAILED (failures=1)" in baseline_log,
      "baseline three-case result")
check("AssertionError: True is not false" in baseline_log,
      "baseline mismatch-control failure")
check(exit_code("candidate") == 0, "candidate exit")
check("Ran 3 tests" in candidate_log and "OK" in candidate_log,
      "candidate three-case result")

expected_counts = {
    "compat-suite-normal": 20,
    "compat-suite-optimized": 20,
    "v39-controller-normal": 16,
    "v39-controller-optimized": 16,
    "pending-drain-normal": 21,
    "pending-drain-optimized": 21,
}
for name, count in expected_counts.items():
    log = (HERE / f"{name}.stderr.txt").read_text(encoding="utf-8")
    check(exit_code(name) == 0, f"{name} exit")
    check(re.search(rf"Ran {count} tests? in ", log) is not None,
          f"{name} count")
    check("OK" in log, f"{name} status")
for name in ("py_compile", "diff_check"):
    check(exit_code(name) == 0, f"{name} exit")

if errors:
    print(json.dumps({"audit_pass": False, "errors": errors}, indent=2))
    raise SystemExit(1)
print(json.dumps({
    "audit_pass": True,
    "baseline": "3 cases, expected mismatch-certification failure observed",
    "candidate": "3 cases passed, including legacy token omission",
    "regression_cases": sum(expected_counts.values()),
    "checks": 28,
    "scope": "offline Windows construction regression only; no physical release claim",
}, indent=2))
