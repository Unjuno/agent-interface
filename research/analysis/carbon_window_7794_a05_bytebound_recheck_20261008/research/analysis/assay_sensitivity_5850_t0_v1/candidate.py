"""Deterministic claim-specific sensitivity-card classifier."""
import hashlib
import json
import pathlib

def qualify(card, threshold=10):
    if card["primary_defect"]:
        return "OUT_OF_SCOPE_UNDETECTED"
    if card["missing"]:
        return "HOLD_MISSING_OUTCOME"
    if card["target_events"] == 0:
        return "HOLD_NO_TARGET_EVENTS"
    if not card["pipeline_shared"]:
        return "HOLD_COMMON_PIPELINE_FAILURE"
    if card["control_delta"] < threshold:
        return "HOLD_CONTROL_BELOW_DELTA"
    if card["resolution"] > threshold:
        return "HOLD_INADEQUATE_RESOLUTION"
    if card["observed_effect"] == 0:
        return "NULL_INTERPRETABLE_NOT_EQUIVALENCE"
    return "DETECTED_CONTROL_AND_EFFECT"

def run(fixture_path):
    raw = pathlib.Path(fixture_path).read_bytes()
    fixture = json.loads(raw)
    return {"allocation": fixture["allocation"],
            "fixture_sha256": hashlib.sha256(raw).hexdigest(),
            "results": {c["id"]: qualify(c, fixture["meaningful_delta"]) for c in fixture["cases"]}}

if __name__ == "__main__":
    import sys
    print(json.dumps(run(sys.argv[1]), sort_keys=True, separators=(",", ":")))
