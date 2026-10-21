"""Verify exact source pins, test counts and outcomes for A09."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
FREEZE = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
RESULT = json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8"))

assert RESULT["candidate_commit"] == FREEZE["candidate_commit"]
assert RESULT["decision"] == "PASS"
assert set(RESULT["sources"]) >= {row["path"] for row in FREEZE["suites"]}
for path, expected in RESULT["sources"].items():
    blob = subprocess.check_output(
        ["git", "-C", str(REPO), "rev-parse",
         f"{FREEZE['candidate_commit']}:{path}"], text=True
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

print("audit: PASS (4 frozen suites: 15 + 20 + 9 + 7 tests, normal and -O)")
