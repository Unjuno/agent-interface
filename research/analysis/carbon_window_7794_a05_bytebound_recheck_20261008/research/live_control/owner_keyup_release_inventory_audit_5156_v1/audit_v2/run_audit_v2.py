"""Re-audit the retained request-parity fields without rerunning the fixture."""
import copy
import hashlib
import json
from pathlib import Path

from audit_request_sequences import audit_owner_behavior


HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
RAW_PATH = STUDY / "RUN_BYTE_IDENTICAL.json"
RAW_SHA256 = "019fb0fb2a01c3064ea8e88e8ad176b059f75cb67b201f444aeee08518dfe592"


def mutation_controls(owner_behavior):
    controls = {}

    changed_v11 = copy.deepcopy(owner_behavior)
    changed_v11["v11_requests"][0] = [99, 999]
    controls["v11_array_changed_flag_true"] = audit_owner_behavior(changed_v11)

    changed_both = copy.deepcopy(owner_behavior)
    changed_both["v10_requests"][0] = [99, 999]
    changed_both["v11_requests"][0] = [99, 999]
    controls["both_arrays_same_wrong_sequence"] = audit_owner_behavior(changed_both)

    changed_expected = copy.deepcopy(owner_behavior)
    changed_expected["expected_request_sequence"][0] = [99, 999]
    controls["self_reported_expected_sequence_changed"] = audit_owner_behavior(changed_expected)

    changed_type = copy.deepcopy(owner_behavior)
    changed_type["v11_requests"][0][0] = True
    controls["boolean_event_code"] = audit_owner_behavior(changed_type)

    changed_flag = copy.deepcopy(owner_behavior)
    changed_flag["v10_v11_behavior_equivalent"] = False
    controls["equivalence_flag_flipped"] = audit_owner_behavior(changed_flag)
    return controls


def run():
    raw_bytes = RAW_PATH.read_bytes()
    raw_sha = hashlib.sha256(raw_bytes).hexdigest()
    if raw_sha != RAW_SHA256:
        raise SystemExit("STOP_PINNED_RAW_HASH_MISMATCH:" + raw_sha)
    raw = json.loads(raw_bytes)
    behavior = raw.get("owner_behavior")
    pristine_errors = audit_owner_behavior(behavior)
    controls = mutation_controls(behavior)
    passed = not pristine_errors and len(controls) == 5 and all(controls.values())
    return {
        "schema": "owner-keyup-request-parity-audit-v2",
        "scope": "retained synthetic fake-Xlib output only; no fixture or formal rerun",
        "raw_sha256": raw_sha,
        "pristine_errors": pristine_errors,
        "mutation_controls": controls,
        "mutation_controls_rejected": sum(bool(errors) for errors in controls.values()),
        "mutation_controls_total": len(controls),
        "disposition": "PASS_REQUEST_SEQUENCE_PARITY_AUDIT_V2" if passed
        else "HOLD_REQUEST_SEQUENCE_PARITY_AUDIT_V2",
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
