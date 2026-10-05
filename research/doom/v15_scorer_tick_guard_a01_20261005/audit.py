"""Read-only source and result audit for the V15 scorer tick guard."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
result = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8"))
assert freeze["schema"] == "v15-scorer-tick-guard-freeze-v1"
assert result["disposition"] == "PASS_SCORER_TICK_CONTRACT"
assert subprocess.check_output(
    ["git", "rev-parse", f"{freeze['base_main']}:research/doom/session_map01_v15.py"],
    cwd=ROOT, text=True).strip() == freeze["baseline_source_blob"]
for relative, expected in freeze["candidate_sha256"].items():
    actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    assert actual == expected, (relative, actual)
assert result["baseline"]["fractional_tics"]["accepted"] is True
assert result["baseline"]["boolean_start"]["accepted"] is True
assert result["baseline"]["fractional_post_sample"]["accepted"] is True
assert result["candidate"]["focused_tests_normal"] == "3/3 passed"
assert result["candidate"]["focused_tests_optimized"] == "3/3 passed"
assert result["live_game"] is False and result["model_calls"] == 0
print("AUDIT_PASS: base blob, candidate hashes, recorded test gate, and scope")
