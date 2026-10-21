"""Audit current-main/candidate source pins and exact regression dispositions."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
FREEZE = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
RESULT = json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8"))
LATEST = json.loads((ROOT / "LATEST_HEAD_RECHECK.json").read_text(encoding="utf-8"))

assert RESULT["main_commit"] == FREEZE["main_commit"]
assert RESULT["candidate_commit"] == FREEZE["candidate_commit"]
assert RESULT["decision"] == "DISCRIMINATING_BASELINE"
for variant, commit in (("main", FREEZE["main_commit"]),
                        ("candidate", FREEZE["candidate_commit"])):
    records = RESULT["sources"][variant]
    assert len(records) >= 10
    for path, expected in records.items():
        desired_ref = (FREEZE["candidate_commit"]
                       if path == FREEZE["test_path"] else commit)
        assert expected["ref"] == desired_ref
        blob = subprocess.check_output(
            ["git", "-C", str(REPO), "rev-parse", f"{desired_ref}:{path}"],
            text=True,
        ).strip()
        data = subprocess.check_output(
            ["git", "-C", str(REPO), "cat-file", "blob", blob]
        )
        assert blob == expected["blob"]
        assert hashlib.sha256(data).hexdigest() == expected["sha256"]

for mode in ("normal", "optimized"):
    main_output = (ROOT / f"main.{mode}.stderr.txt").read_text(encoding="utf-8")
    candidate_output = (ROOT / f"candidate.{mode}.stderr.txt").read_text(encoding="utf-8")
    assert RESULT["runs"]["main"][mode]["exit_code"] != 0
    assert RESULT["runs"]["candidate"][mode]["exit_code"] == 0
    assert re.search(rf"Ran {FREEZE['test_count']} tests? in", main_output)
    assert (f"FAILED (failures={FREEZE['main_outcomes'][mode]['failures']}, "
            f"errors={FREEZE['main_outcomes'][mode]['errors']})" in main_output)
    for name in FREEZE["expected_main_regressions"]:
        assert name in main_output
    for name in FREEZE["new_followup_cases"]:
        assert name in main_output
    assert re.search(rf"Ran {FREEZE['test_count']} tests? in", candidate_output)
    assert candidate_output.rstrip().endswith("OK")

assert LATEST["candidate_head_tested"] == FREEZE["candidate_commit"]
for path, tested_key, latest_key in (
        (LATEST["controller_path"], "controller_blob_at_tested_head",
         "controller_blob_at_latest_head"),
        (LATEST["controller_test_path"], "controller_test_blob_at_tested_head",
         "controller_test_blob_at_latest_head")):
    assert RESULT["sources"]["candidate"][path]["blob"] == LATEST[tested_key]
    blob = subprocess.check_output(
        ["git", "-C", str(REPO), "rev-parse", f"origin/pr-8643:{path}"], text=True
    ).strip()
    assert blob == LATEST[latest_key]
print("audit: PASS (main has 1 failure/7 errors across 15 tests; candidate 15/15 in normal and -O)")
print("latest-head audit: PASS (tested controller and controller-test blobs unchanged)")
