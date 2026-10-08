import hashlib
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
freeze = json.loads((root / "FREEZE.json").read_text(encoding="utf-8-sig"))
result = json.loads((root / "candidate-output.json").read_text(encoding="utf-8-sig"))
source = root.joinpath(freeze["source_path"]).read_bytes()
probe = (root / "probe.py").read_bytes()
checks = {}
checks["source_identity_matches"] = (
    hashlib.sha256(source).hexdigest() == freeze["source_sha256"] and
    len(source) == freeze["source_bytes"]
)
checks["probe_identity_matches"] = (
    hashlib.sha256(probe).hexdigest() == freeze["probe_sha256"] and
    len(probe) == freeze["probe_bytes"]
)
checks["result_has_three_cases"] = len(result.get("cases", {})) == 3
derived = {}
for name, case in result.get("cases", {}).items():
    events = case.get("events", [])
    outs = case.get("outcomes", [])
    if len(events) != 2 or len(outs) != 2 or outs[0] is not None:
        derived[name] = False
        continue
    a, b = events
    same_epoch = a.get("sequence") == b.get("sequence") and a.get("capture_ns") == b.get("capture_ns")
    transport_changed = a.get("event") != b.get("event")
    paired_content_equal = a.get("signals") == b.get("signals") and a.get("pointer_binding") == b.get("pointer_binding")
    frame_equal = a.get("frame_rgb_sha256") == b.get("frame_rgb_sha256")
    expected = "PRESERVE"
    actual = outs[1]
    if same_epoch and transport_changed and (not paired_content_equal or not frame_equal):
        expected = "signal_pair_duplicate_epoch_mismatch"
    elif same_epoch and transport_changed:
        expected = "PRESERVE"
    elif b.get("sequence", 0) > a.get("sequence", 0) and b.get("capture_ns", 0) > a.get("capture_ns", 0):
        expected = "PRESERVE"
    actual_label = "PRESERVE" if actual is None else actual.get("reason", actual.get("event"))
    derived[name] = actual_label == expected
checks["independent_event_derivation_passes"] = len(derived) == 3 and all(derived.values())
checks["recorded_expectations_pass"] = result.get("status") == "PASS_SYNTHETIC_BOUNDARY" and all(result.get("checks", {}).values())
checks["scope_is_construction_only"] = ("no game" in result.get("scope", "").lower() or "no doom" in result.get("scope", "").lower())
audit = {
    "status": "PASS_BOUNDARY_AUDIT" if all(checks.values()) else "FAIL_BOUNDARY_AUDIT",
    "checks": checks,
    "derived_case_checks": derived,
    "scope": "Arithmetic and event-relation audit of saved synthetic output; does not validate live threat semantics or gameplay."
}
print(json.dumps(audit, indent=2, sort_keys=True))
if not all(checks.values()):
    raise SystemExit(1)

