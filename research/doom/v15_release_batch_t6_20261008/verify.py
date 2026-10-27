"""Independent check of current producer pins, adapter invariants, and hashes."""
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
RESULT = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8"))
blob = subprocess.check_output(["git", "-C", str(REPO), "rev-parse",
                                f"{FREEZE['current_main_commit']}:{FREEZE['current_backend_path']}"], text=True).strip()
assert blob == FREEZE["current_backend_blob"]
for path, expected in FREEZE["candidate_sources"].items():
    raw = (HERE / path).read_bytes()
    header = f"blob {len(raw)}\0".encode()
    assert hashlib.sha1(header + raw).hexdigest() == expected, path
assert RESULT["disposition"] == "PASS_CURRENT_PRODUCER_TO_FAIL_CLOSED_ADAPTER_COMPOSITION"
assert RESULT["producer"] == {"release_rows": 2, "delivery_positions": [0, 1],
                              "delivery_states": ["confirmed", "confirmed"],
                              "owner_transition_verified": [True, True],
                              "physical_verification_authoritative": False}
assert RESULT["baseline"] == {"trace_integrity": "SOURCE_ROWS_JOINED",
                              "attribution": "TEMPORALLY_UNIQUE",
                              "causal_attribution": "NOT_ESTABLISHED"}
assert RESULT["controls"] == {
    "mixed_position_schema": "HOLD_INCOMPLETE_RELEASE_BATCH/UNRESOLVED",
    "duplicate_position": "HOLD_INCOMPLETE_RELEASE_BATCH/UNRESOLVED",
    "delivery_gap": "HOLD_INCOMPLETE_RELEASE_BATCH/UNRESOLVED",
    "missing_release_row": "UNRESOLVED",
    "row_reordering": "same_disposition"}
assert (HERE / "normal.stdout.txt").read_bytes() == (HERE / "optimized.stdout.txt").read_bytes()
assert json.loads((HERE / "normal.stdout.txt").read_text(encoding="utf-8")) == RESULT
for name in ("normal", "optimized"):
    assert (HERE / f"{name}.exit.txt").read_text(encoding="ascii").strip() == "0"
    assert not (HERE / f"{name}.stderr.txt").read_bytes()
for line in (HERE / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
    digest, name = line.split("  ", 1)
    assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == digest, name
print("PASS: current-main release methods, bundled T5 source, fail-closed controls, and package hashes")
