"""Independent saved-result and frozen-source auditor for C01-A02."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
raw = json.loads((HERE / "RAW.json").read_text(encoding="utf-8"))
actual = {}
for rel, expected_sha in freeze["sources"].items():
    data = (HERE / rel).read_bytes()
    actual[rel] = hashlib.sha256(data).hexdigest()
source_matches = actual == freeze["sources"]
checks = {
    "raw_probe_id": raw.get("probe_id") == "V13-V4-EXPLICIT-UP-COMPOSITION-C01",
    "v13_returns_release_rpc": raw.get("v13_call_result", {}).get("event") == "input_release_rpc",
    "v13_call_bounds": raw.get("v13_call_result", {}).get("release_transition_interval_ns") == [100, 145],
    "v13_release_rpc_scope": raw.get("v13_call_result", {}).get("application_consumption_observed") is False
        and raw.get("v13_call_result", {}).get("continuous_physical_state_sampled") is False,
    "v4_rejects_payload": raw.get("v4_integration_result", {}).get("raised_type") == "AssertionError",
    "v4_failure_message": raw.get("v4_integration_result", {}).get("raised_message") == "InputOwner v10 explicit release unexpectedly returned payload",
    "no_display_or_input": raw.get("xlib_display_started") is False and raw.get("xlib_input_called") is False,
    "single_invocation": raw.get("tries") == 1 and freeze.get("candidate_invocations") == 1,
    "frozen_source_set": len(actual) == 7 and source_matches,
}
(HERE / "SOURCE_SHA256.json").write_text(json.dumps(actual, indent=2, sort_keys=True) + "\n", encoding="utf-8")
result = {"classification": "STOP_COMPOSITION_API_MISMATCH", "checks": checks,
          "source_hashes": actual, "passed": sum(checks.values()), "total": len(checks)}
(HERE / "AUDIT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, sort_keys=True))
if not all(checks.values()):
    raise SystemExit(1)
