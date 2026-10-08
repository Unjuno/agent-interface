"""Verify candidate source pins and both recorded regression-suite outcomes."""
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
assert RESULT["normal"]["exit_code"] == 0
assert RESULT["optimized"]["exit_code"] == 0
for name in ("normal", "optimized"):
    output = (ROOT / f"{name}.stderr.txt").read_text(encoding="utf-8")
    match = re.search(r"Ran (\d+) tests? in", output)
    assert match and int(match.group(1)) == 16, (name, match.group(0) if match else "missing")
    assert output.rstrip().endswith("OK"), name
print("audit: PASS (7 frozen overlay files; normal and -O each ran 16 tests)")
