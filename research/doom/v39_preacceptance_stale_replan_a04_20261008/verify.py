"""Independent source-pin, invariant, output-parity and package audit."""
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
RESULT = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8"))
expected = FREEZE["sources"]
assert len(expected) == 7
actual = {path: subprocess.check_output(
    ["git", "-C", str(REPO), "rev-parse", f"{FREEZE['main_commit']}:{path}"], text=True).strip()
          for path in expected}
assert actual == expected
assert RESULT["main_commit"] == FREEZE["main_commit"]
assert RESULT["source_blobs"] == expected
assert RESULT["disposition"] == "PASS_EXACT_PRODUCER_TO_EXECUTOR_RECOVERY_COMPOSITION"
assert RESULT["producer_pair"] == {"sequence": 2, "typed_before_full": True,
                                  "capture_binding_hash_match": True, "health": 86, "ammo": 12}
assert RESULT["stale_sequence_1"] == {
    "reason": "latest observation sequence required before input", "compiled_once": True,
    "accepted_events": 0, "backend_validation_calls": 0, "worker_starts": 0,
    "retried_after_rejection": False}
fresh = RESULT["fresh_sequence_2"]
assert fresh["planner_turn_count"] == 2 and fresh["used_exact_producer_image"] and fresh["used_paired_typed_hud"]
assert fresh["accepted_events"] == 1 and fresh["backend_validation_calls"] == 1
assert fresh["worker_started_inertly"] is True and fresh["physical_input"] is False
drift = RESULT["second_drift_sequence_3"]
assert drift == {"reason": "latest observation sequence required before input",
                 "accepted_events": 0, "backend_validation_calls": 0, "worker_starts": 0}
assert RESULT["controls"] == {
    "non_stale_rejection": "refused", "no_fresh_observation": "refused",
    "missing_typed_event": "refused", "binding_mismatch": "refused",
    "frame_hash_mismatch": "refused"}
normal = (HERE / "normal.stdout.txt").read_bytes()
optimized = (HERE / "optimized.stdout.txt").read_bytes()
assert normal == optimized
assert json.loads(normal.decode("utf-8")) == RESULT
for name in ("normal", "optimized"):
    assert (HERE / f"{name}.exit.txt").read_text(encoding="ascii").strip() == "0"
    assert not (HERE / f"{name}.stderr.txt").read_bytes()
for line in (HERE / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
    digest, name = line.split("  ", 1)
    assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == digest, name
print("PASS: 7 pinned source blobs, exact producer/recovery/admission invariants, output parity, and package hashes")
