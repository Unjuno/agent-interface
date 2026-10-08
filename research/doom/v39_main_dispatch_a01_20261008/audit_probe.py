"""Independent pin, scope and raw-output audit for the V39 main dispatch probe."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
result = json.loads((ROOT / "result.json").read_text(encoding="utf-8"))
assert freeze["main_commit"] == result["main_commit"]
for path, expected in freeze["source_files"].items():
    actual = subprocess.check_output(["git", "hash-object", path], cwd=REPO, text=True).strip()
    assert actual == expected, f"source blob mismatch: {path}: {actual}"
for mode in ("normal", "optimized"):
    assert (ROOT / f"{mode}.exit").read_text(encoding="utf-8").strip() == "0"
    stderr = (ROOT / f"{mode}.stderr.txt").read_text(encoding="utf-8")
    assert "Ran 1 test" in stderr and "OK" in stderr
assert result["classification"] == "CONSTRUCTION_ONLY_MAIN_LOOP_DISPATCH"
assert result["terminal_release"] == {"verified": True, "keys_down": [], "buttons_down": []}
assert result["source_refresh_status"] == "already_observed"
assert result["fresh_source_sequence"] == 11
assert result["mutation_controls"] == {
    "omit_latest_observation_update": "CAUGHT_FAIL",
    "omit_cancel_before_interrupt": "CAUGHT_FAIL"}
assert result["timeline"][0] == "typed_invalidation_returned_by_main_wait"
assert result["timeline"].index("executor_cancel_flush") < result["timeline"].index("planner_interrupt_request")
checks = {}
for path in sorted(ROOT.rglob("*")):
    if path.is_file() and "__pycache__" not in path.parts and path.name != "SHA256SUMS.txt":
        checks[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
lines = [line.split("  ", 1) for line in (ROOT / "SHA256SUMS.txt").read_text().splitlines()]
assert {name: digest for digest, name in lines} == checks
print(json.dumps({"audit_passed": True, "source_blobs": len(freeze["source_files"]),
                  "normal_and_optimized": "1/1 PASS each",
                  "scope": result["classification"], "checksummed_files": len(checks)}, indent=2))
