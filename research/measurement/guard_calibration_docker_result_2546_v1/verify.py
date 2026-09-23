import json
from pathlib import Path

root = Path(__file__).parent
result = json.loads((root / "RESULT.json").read_text())
audit = json.loads((root / "AUDIT.json").read_text())
assert result["formal_decision"] == "PASS_GUARD_POLICY_RECOVERABLE_X11_CALIBRATION_A3_SCOPED"
assert result["formal_invocations"] == 1
assert result["reruns"] == result["replacements"] == result["tuning"] == 0
assert result["independent_audit"]["pass"] is True
assert result["independent_audit"]["errors"] == []
assert all(value == 0 for value in result["calibration"]["negative_counts"].values())
assert audit["raw_formal_bytes"] > 2_000_000
print("PASS_DOCKER_A3_RESULT_LEDGER")
