"""Verify candidate source pins and all recorded regression-suite outcomes."""
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
    blob = subprocess.check_output(
        ["git", "-C", str(REPO), "rev-parse",
         f"{FREEZE['candidate_commit']}:{path}"], text=True).strip()
    data = subprocess.check_output(["git", "-C", str(REPO), "cat-file", "blob", blob])
    assert blob == expected["blob"], path
    assert hashlib.sha256(data).hexdigest() == expected["sha256"], path

assert RESULT["candidate_commit"] == FREEZE["candidate_commit"]
assert RESULT["dependency_base_commit"] == FREEZE["dependency_base_commit"]
assert RESULT["dependency_tree_unchanged_outside_evidence"] is True
assert RESULT["decision"] == "PASS"
counts = {"test_map01_v39_pending_observation_drain.py": 17,
          "test_map01_overlap_controller_v39.py": 9}
for pattern, expected_count in counts.items():
    for mode in ("normal", "optimized"):
        assert RESULT["runs"][pattern][mode]["exit_code"] == 0
        stem = pattern.removesuffix(".py")
        output = (ROOT / f"{stem}.{mode}.stderr.txt").read_text(encoding="utf-8")
        match = re.search(r"Ran (\d+) tests? in", output)
        assert match and int(match.group(1)) == expected_count, (pattern, mode)
        assert output.rstrip().endswith("OK"), (pattern, mode)
print("audit: PASS (8 frozen overlay files; drain 17/17 and controller 9/9 in normal and -O)")
