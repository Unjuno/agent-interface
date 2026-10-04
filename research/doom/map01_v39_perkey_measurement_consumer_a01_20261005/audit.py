"""Independent raw-only audit; intentionally does not import candidate.py."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPECTED = "ad0b1c29da4b626e9be27e8716cdabfbb25ac49dcf0abd4dba4bd2f7a9f84e4e"


def independently_reconstruct(rows):
    if len(rows) != 2:
        raise ValueError("expected one down/up pair")
    down, up = rows
    if down.get("event") != "input_admission" or up.get("event") != "input_release_measurement":
        raise ValueError("event sequence mismatch")
    join = ("id", "step", "owner_id", "intent_token", "key")
    if any(down.get(k) != up.get(k) for k in join):
        raise ValueError("cross-edge identity mismatch")
    if type(down.get("step")) is not int or down["step"] < 0:
        raise ValueError("invalid step")
    dm = down["physical_key_measurement"]
    um = up["physical_key_measurement"]
    de, ue = dm["adapter_edge"], um["adapter_edge"]
    db, ub = dm["bracket"], um["bracket"]
    di, ui = de["interval"], ue["interval"]
    if (dm["classification"], de["status"], dm["identity_status"]) != (
            "CONFIRMED_PHYSICAL_DOWN", "CONFIRMED_PHYSICAL_DOWN", "MINTED"):
        raise ValueError("down edge not confirmed")
    if (um["classification"], ue["status"], um["identity_status"]) != (
            "CONFIRMED_PHYSICAL_UP", "CONFIRMED_PHYSICAL_UP", "RETIRED"):
        raise ValueError("up edge not confirmed")
    for edge in (de, ue):
        if edge["grants_input_authority"] is not False:
            raise ValueError("authority flag is not false")
    for measure in (dm, um):
        if measure["grants_input_authority"] is not False or measure["application_consumption_observed"] is not False:
            raise ValueError("measurement claims authority/effect")
    if de["actuation_id"] != ue["actuation_id"]:
        raise ValueError("actuation identity mismatch")
    if db["physical_down_interval"] != di or ub["physical_up_interval"] != ui:
        raise ValueError("edge/source bracket disagreement")
    if any(type(v) is not int for v in di + ui) or not (di[0] <= di[1] <= ui[0] <= ui[1]):
        raise ValueError("interval order/type invalid")
    lo, hi = ui[0] - di[1], ui[1] - di[0]
    return {
        "schema": "map01_v39_perkey_sample_bracket_consumer_v1",
        "source_pair": {"program_id": down["id"], "step": down["step"],
                        "owner_id": down["owner_id"], "intent_token": down["intent_token"],
                        "key": down["key"], "actuation_id": de["actuation_id"]},
        "down_state_interval_ns": di, "up_state_interval_ns": ui,
        "hold_duration_lower_bound_ns": lo, "hold_duration_upper_bound_ns": hi,
        "authority_granted": False, "application_effect_observed": False,
        "scope": "fake-display sample-bracketed key-state duration; not exact physical/game occupancy"
    }


def audit(input_path: Path, result_path: Path) -> dict:
    raw = input_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED:
        raise ValueError("frozen input hash mismatch")
    rows = [json.loads(x) for x in raw.decode("utf-8").splitlines() if x]
    result = json.loads(result_path.read_text())
    expected = independently_reconstruct(rows)
    errors = []
    if result.get("input_sha256") != EXPECTED: errors.append("result input hash mismatch")
    if result.get("input_event_count") != len(rows): errors.append("event count mismatch")
    if result.get("candidate") != expected: errors.append("candidate differs from raw reconstruction")
    if result.get("status") != "PASS_MEASUREMENT_CONSUMER_SCOPED": errors.append("candidate status mismatch")
    if result.get("environment", {}).get("new_os_input") is not False: errors.append("new OS input claim mismatch")
    return {"schema": "map01_v39_perkey_measurement_consumer_audit_v1",
            "disposition": "PASS_RECONSTRUCTED_SCOPED" if not errors else "FAIL_MISMATCH",
            "input_sha256": EXPECTED, "event_count": len(rows),
            "expected_candidate": expected, "error_count": len(errors), "errors": errors}


def main() -> None:
    result = audit(HERE / "INPUT_EVENTS.jsonl", HERE / "results" / "a01" / "RESULT.json")
    path = HERE / "results" / "a01" / "AUDIT.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    if result["errors"]:
        raise SystemExit(1)

if __name__ == "__main__": main()
