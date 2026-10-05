"""Independent source, regression, raw-log and scope audit for A01."""
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
result = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8"))

assert freeze["schema"] == "win32-focus-drift-fence-freeze-v1"
assert result["schema"] == "win32-focus-drift-fence-result-v1"
assert subprocess.check_output(
    ["git", "rev-parse", f"{freeze['base_sha']}:runtime/backends/win32_v1/backend.py"],
    cwd=ROOT, text=True,
).strip() == freeze["baseline_source_blob"]

for relative, expected in freeze["candidate_sha256"].items():
    actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    assert actual == expected, (relative, actual)

raw_logs = {
    "red-parent.log": result["baseline"]["sha256"],
    "green-normal.log": result["candidate"]["normal_sha256"],
    "green-optimized.log": result["candidate"]["optimized_sha256"],
}
for name, expected in raw_logs.items():
    actual = hashlib.sha256((HERE / name).read_bytes()).hexdigest()
    assert actual == expected, (name, actual)

red = (HERE / "red-parent.log").read_text(encoding="utf-8", errors="replace")
normal = (HERE / "green-normal.log").read_text(encoding="utf-8", errors="replace")
optimized = (HERE / "green-optimized.log").read_text(encoding="utf-8", errors="replace")
assert "Ran 2 tests" in red and "FAILED (failures=2)" in red
for log in (normal, optimized):
    assert "Ran 56 tests" in log and "OK" in log
assert result["baseline"]["exit_code"] == 1
assert result["candidate"]["normal_exit_code"] == 0
assert result["candidate"]["optimized_exit_code"] == 0
assert result["live_input"] is False
assert result["live_application"] is False
assert result["physical_keyboard_state_proven"] is False
assert result["application_delivery_proven"] is False
print("PASS_AUDIT_WIN32_FOCUS_DRIFT_A01")
