"""Verify exact source pins, test counts and outcomes for A12."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
FREEZE = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
RESULT = json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8"))
carry = json.loads((ROOT / "MAIN_CARRY_FORWARD.json").read_text(encoding="utf-8"))

assert RESULT["source_commit"] == FREEZE["source_commit"]
assert RESULT["decision"] == "PASS"
assert carry["frozen_source_commit"] == FREEZE["source_commit"]
assert carry["status"] == "PASS_BYTE_IDENTICAL_CURRENT_MAIN_CARRY_FORWARD"
assert carry["changed_paths_overlapping_pinned_sources"] == []
assert carry["source_paths_verified"] == len(RESULT["sources"])
carry_sources = {row["path"]: row for row in carry["sources"]}
assert set(carry_sources) == set(RESULT["sources"])
for path, frozen in RESULT["sources"].items():
    assert carry_sources[path]["blob"] == frozen["blob"], path
    assert carry_sources[path]["sha256"] == frozen["sha256"], path
assert set(RESULT["sources"]) >= {row["path"] for row in FREEZE["suites"]}
for path, expected in RESULT["sources"].items():
    blob = subprocess.check_output(
        ["git", "-C", str(REPO), "rev-parse",
         f"{FREEZE['source_commit']}:{path}"], text=True
    ).strip()
    data = subprocess.check_output(["git", "-C", str(REPO), "cat-file", "blob", blob])
    assert blob == expected["blob"], path
    assert hashlib.sha256(data).hexdigest() == expected["sha256"], path

for suite in FREEZE["suites"]:
    key = suite["key"]
    for mode in ("normal", "optimized"):
        assert RESULT["runs"][key][mode]["exit_code"] == 0
        output = (ROOT / f"{key}.{mode}.stderr.txt").read_text(encoding="utf-8")
        assert re.search(rf"Ran {suite['tests']} tests? in", output), (key, mode)
        assert output.rstrip().endswith("OK"), (key, mode)

counts = " + ".join(str(row["tests"]) for row in FREEZE["suites"])
print(f"audit: PASS (4 frozen suites: {counts} tests, normal and -O)")
