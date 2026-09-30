#!/usr/bin/env python3
"""Independent audit of T12 stdout and retained SQLite evidence; no candidate imports."""
import json
from pathlib import Path
import sqlite3
import sys

TARGET = "target-7"
EXPECTED = [
    ("pre_consume", "before_consume", None, True, False, "NOT_STARTED"),
    ("post_consume", "after_consume", None, True, True, "UNKNOWN"),
    ("effect_pre_observation", "after_effect", "matching", True, True, "CONFIRMED_SAME_ATTEMPT"),
    ("wrong_target", None, "wrong_target", True, False, "UNKNOWN"),
    ("foreign_lineage", None, "foreign_lineage", True, False, "UNKNOWN"),
    ("observer_unavailable", None, "matching", False, False, "UNKNOWN"),
    ("normal_valid", None, "matching", True, False, "CONFIRMED_SAME_ATTEMPT"),
]


def db_state(path):
    with sqlite3.connect(path) as db:
        row = db.execute("SELECT receipt_id,generation,state,attempt_id,delivery_id FROM receipts").fetchone()
    return dict(zip(("receipt_id", "generation", "state", "attempt_id", "delivery_id"), row))


def db_effects(path):
    with sqlite3.connect(path) as db:
        return [dict(zip(("delivery_id", "attempt_id", "target", "effect"), row))
                for row in db.execute("SELECT delivery_id,attempt_id,target,effect FROM deliveries ORDER BY delivery_id")]


def expected_result(receipt, effects, observer_available):
    if receipt["state"] == "AVAILABLE":
        return "NOT_STARTED"
    if receipt["state"] != "CONSUMED" or not observer_available:
        return "UNKNOWN"
    matches = [e for e in effects if e["attempt_id"] == receipt["attempt_id"]
               and e["delivery_id"] == receipt["delivery_id"]]
    target = effects[0]["target"] if len(effects) == 1 else None
    if len(matches) == 1 and target == TARGET and matches[0]["target"] == TARGET:
        return "CONFIRMED_SAME_ATTEMPT"
    return "UNKNOWN"


def audit(path):
    path = Path(path)
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    errors = []
    if len(rows) != 8 or rows[0].get("kind") != "manifest":
        errors.append("manifest_or_line_count")
    if not rows or rows[0].get("schema") != "issue-5508-affine-receipt-t12-v1":
        errors.append("schema")
        return {"audit": "FAIL", "errors": errors}
    traces = rows[1:]
    if len(traces) != len(EXPECTED):
        errors.append("scenario_count")
    counts = {"NOT_STARTED": 0, "UNKNOWN": 0, "CONFIRMED_SAME_ATTEMPT": 0}
    for i, (trace, exp) in enumerate(zip(traces, EXPECTED)):
        cid, crash, effect_mode, observer_available, retry, expected_decision = exp
        spec = {"case_id": cid, "crash": crash, "effect": effect_mode,
                "observer": observer_available, "retry": retry}
        if trace.get("kind") != "trace" or trace.get("case") != spec:
            errors.append(f"case_spec:{i}")
            continue
        try:
            receipt_path = path.parent / trace["journal_db"].removeprefix("raw/")
            effect_path = path.parent / trace["effect_db"].removeprefix("raw/")
            receipt = db_state(receipt_path)
            effects = db_effects(effect_path)
        except Exception as e:
            errors.append(f"database_read:{i}:{type(e).__name__}")
            continue
        if trace.get("receipt_rows") != [receipt]: errors.append(f"receipt_snapshot:{i}")
        if trace.get("effect_rows") != effects: errors.append(f"effect_snapshot:{i}")
        expected_state = "AVAILABLE" if crash == "before_consume" else "CONSUMED"
        if receipt["state"] != expected_state: errors.append(f"receipt_state:{i}")
        expected_attempt = None if expected_state == "AVAILABLE" else f"attempt-{cid}"
        expected_delivery = None if expected_state == "AVAILABLE" else f"delivery-{cid}"
        if (receipt["attempt_id"], receipt["delivery_id"]) != (expected_attempt, expected_delivery):
            errors.append(f"receipt_lineage:{i}")
        if crash in ("before_consume", "after_consume", "after_effect"):
            if trace.get("worker", {}).get("exit_code") != -9: errors.append(f"kill_exit:{i}")
        else:
            if trace.get("worker", {}).get("exit_code") != 0: errors.append(f"normal_exit:{i}")
        if retry:
            rr = trace.get("retry")
            if not rr or rr.get("exit_code") != 0 or "REJECTED_REPLAY" not in rr.get("events", []):
                errors.append(f"retry_rejection:{i}")
        elif trace.get("retry") is not None:
            errors.append(f"unexpected_retry:{i}")
        if effect_mode is None and effects:
            errors.append(f"unexpected_effect:{i}")
        if effect_mode is not None and len(effects) != 1:
            errors.append(f"effect_count:{i}")
        if effect_mode == "foreign_lineage" and effects and (effects[0]["attempt_id"], effects[0]["delivery_id"]) != ("attempt-foreign", "delivery-foreign"):
            errors.append(f"foreign_lineage_setup:{i}")
        if effect_mode == "wrong_target" and effects and effects[0]["target"] != "target-wrong":
            errors.append(f"wrong_target_setup:{i}")
        # Recompute what the isolated observer can see, without trusting its embedded JSON.
        if observer_available:
            computed_observer = {"available": True, "deliveries": effects,
                                 "target": effects[0]["target"] if effects else "initial"}
        else:
            computed_observer = {"available": False, "deliveries": [], "target": None}
        if trace.get("observer") != computed_observer: errors.append(f"observer_snapshot:{i}")
        decision = expected_result(receipt, effects, observer_available)
        counts[decision] = counts.get(decision, 0) + 1
        if trace.get("recovery") != decision or decision != expected_decision:
            errors.append(f"recovery_decision:{i}")
    if rows[0].get("scenario_count") != 7: errors.append("manifest_scenario_count")
    if rows[0].get("recovery_counts") != counts: errors.append("manifest_counts")
    manifest_decision = "PASS" if counts == {"NOT_STARTED": 1, "UNKNOWN": 4, "CONFIRMED_SAME_ATTEMPT": 2} else "FAIL"
    if rows[0].get("decision") != manifest_decision: errors.append("manifest_decision")
    return {"audit": "PASS" if not errors else "FAIL", "errors": errors,
            "scenario_count": len(traces), "independently_reconstructed": counts,
            "reconstructed_decision": manifest_decision}


if __name__ == "__main__":
    print(json.dumps(audit(sys.argv[1]), sort_keys=True, separators=(",", ":")))
