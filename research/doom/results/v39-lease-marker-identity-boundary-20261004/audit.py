"""Independent checks for the retained lease-marker identity result."""
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
BEFORE = json.loads((HERE / "BEFORE.json").read_text(encoding="utf-8"))
AFTER = json.loads((HERE / "AFTER.json").read_text(encoding="utf-8"))

pre_fix_bytes = subprocess.check_output(
    ["git", "show", f"{FREEZE['pre_fix_commit']}:{FREEZE['pre_fix_source_path']}"],
    cwd=ROOT,
)
fixed_bytes = subprocess.check_output(
    ["git", "show", "HEAD:research/live_control/input_transition_owner_v3.py"],
    cwd=ROOT,
)
test_bytes = subprocess.check_output(
    ["git", "show", "HEAD:research/live_control/test_input_transition_owner_v3.py"],
    cwd=ROOT,
)
assert hashlib.sha256(pre_fix_bytes).hexdigest() == BEFORE["source_bytes_sha256"]
assert hashlib.sha256(fixed_bytes).hexdigest() == AFTER["source_bytes_sha256"]
assert hashlib.sha256(test_bytes).hexdigest() == FREEZE["red_test_current_test_sha256"]
assert BEFORE["distinct_lease_objects"] is True
assert BEFORE["new_lease_had_no_admission"] is True
assert BEFORE["forced_id_collision"] is True
assert BEFORE["owner_release_history_complete"] is True
assert BEFORE["ordinary_release_candidate"] is True
assert AFTER["distinct_lease_objects"] is True
assert AFTER["new_lease_had_no_admission"] is True
assert AFTER["forced_id_collision"] is True
assert AFTER["owner_release_history_complete"] is False
assert AFTER["ordinary_release_candidate"] is False

for line in (HERE / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
    expected, identity = line.split("  ", 1)
    if identity.startswith("git:"):
        _, ref, path = identity.split(":", 2)
        content = subprocess.check_output(["git", "show", f"{ref}:{path}"], cwd=ROOT)
    else:
        content = (ROOT / identity).read_bytes()
    assert hashlib.sha256(content).hexdigest() == expected, identity

print("PASS_LEASE_MARKER_IDENTITY_CONSTRUCTION_PRE_AND_POST")
