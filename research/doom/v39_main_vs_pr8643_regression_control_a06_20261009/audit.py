"""Independently check frozen source IDs and discriminating outcomes."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
FREEZE = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
RESULT = json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8"))

for path, expected in FREEZE["overlay_paths"].items():
    ref = FREEZE[expected["ref"]]
    blob = subprocess.check_output(
        ["git", "-C", str(REPO), "rev-parse", f"{ref}:{path}"], text=True
    ).strip()
    data = subprocess.check_output(["git", "-C", str(REPO), "cat-file", "blob", blob])
    assert blob == expected["blob"]
    assert hashlib.sha256(data).hexdigest() == expected["sha256"]

assert RESULT["main_commit"] == FREEZE["main_commit"]
assert RESULT["candidate_commit"] == FREEZE["candidate_commit"]
assert RESULT["decision"] == "DISCRIMINATING_BASELINE"
assert RESULT["dependency_sources"]
for source in RESULT["dependency_sources"]:
    blob = subprocess.check_output(
        ["git", "-C", str(REPO), "rev-parse",
         f"{FREEZE['main_commit']}:{source['path']}"], text=True
    ).strip()
    data = subprocess.check_output(["git", "-C", str(REPO), "cat-file", "blob", blob])
    assert blob == source["blob"]
    assert hashlib.sha256(data).hexdigest() == source["sha256"]
expected_failure = FREEZE["expected_case_dispositions"]
for mode in ("normal", "optimized"):
    assert RESULT["runs"][mode]["exit_code"] != 0
    output = (ROOT / f"{mode}.stderr.txt").read_text(encoding="utf-8")
    assert re.search(r"Ran 9 tests? in", output)
    assert re.search(r"FAILED \(failures=1, errors=1\)", output)
    stale_case = "test_stale_partial_action_does_not_reuse_discarded_remaining_cover"
    cancel_case = "test_initial_cover_invalidation_cancels_before_planner_and_requires_empty_release"
    assert re.search(re.escape(stale_case) + r" .*FAIL", output)
    assert re.search(re.escape(cancel_case) + r" .*ERROR", output)
    assert "cancel_initial_cover_before_planner" in output

# The candidate's exact same nine-test file passed in the separately retained A05 run.
a05 = REPO / "research" / "doom" / "v39_pr8643_overlay_regression_a05_20261008"
a05_freeze = json.loads((a05 / "FREEZE.json").read_text(encoding="utf-8"))
a05_result = json.loads((a05 / "RESULT.json").read_text(encoding="utf-8"))
assert a05_freeze["candidate_commit"] == FREEZE["candidate_commit"]
assert a05_result["candidate_commit"] == FREEZE["candidate_commit"]
for path, expected in a05_freeze["overlay_paths"].items():
    blob = subprocess.check_output(
        ["git", "-C", str(REPO), "rev-parse",
         f"{FREEZE['candidate_commit']}:{path}"], text=True
    ).strip()
    data = subprocess.check_output(["git", "-C", str(REPO), "cat-file", "blob", blob])
    assert blob == expected["blob"]
    assert hashlib.sha256(data).hexdigest() == expected["sha256"]
for row in (a05 / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
    expected_hash, name = row.split("  ", 1)
    assert hashlib.sha256((a05 / name).read_bytes()).hexdigest() == expected_hash
for mode in ("normal", "optimized"):
    output = (a05 / f"test_map01_overlap_controller_v39.{mode}.stderr.txt").read_text(
        encoding="utf-8")
    assert re.search(r"Ran 9 tests? in", output)
    assert output.rstrip().endswith("OK")
assert FREEZE["candidate_control_result"]["decision"] == "PASS"
print("audit: PASS (main reproduces 2 expected regressions in normal/-O; candidate passes 9/9 in both)")
