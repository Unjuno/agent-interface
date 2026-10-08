"""Successor audit binding synthetic diagnoses to exact frozen capture identity."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
SIGNALS = {"cause_a": "transient_focus_loss", "cause_b": "transient_modal_race", "null_cause": None}


def audit(result):
    errors = []
    rows = result.get("rows", [])
    if len(rows) != 864:
        errors.append("row cardinality mismatch")
    for row in rows:
        seed, scenario, policy = row.get("seed"), row.get("scenario"), row.get("policy")
        name = f"{scenario}/{policy}/{seed}"
        expected_source = f"src-{seed}-{scenario}"
        expected_failure = f"failure-{seed}-{scenario}"
        expected_receipt = f"receipt-{seed}-{scenario}"
        expected_signal = SIGNALS.get(scenario)
        should_skip = row.get("hazard") or row.get("zero_slack") or row.get("privacy_forbidden")
        should_hold = row.get("stale_source") or row.get("receipt_missing") or row.get("observer_perturbs")
        snap = row.get("snapshot")
        events = row.get("events", [])
        if row.get("source_id") != expected_source:
            errors.append(name + ": row source identity mismatch")
        if should_skip:
            if not events or events[0] != "safe_release_or_stop" or snap is not None:
                errors.append(name + ": safety/privacy gate did not skip capture first")
            if row.get("disposition") != "SNAPSHOT_SKIPPED_SAFETY":
                errors.append(name + ": safety disposition mismatch")
        elif should_hold:
            if snap is not None or not row.get("recovery_completed") or "recover" not in events:
                errors.append(name + ": blocked evidence was not discarded before immediate recovery")
        elif policy == "IMMEDIATE_RECOVER":
            if snap is not None or row.get("diagnosis_signal") is not None:
                errors.append(name + ": immediate-recovery evidence was promoted")
        else:
            if not isinstance(snap, dict):
                errors.append(name + ": expected capture missing")
            else:
                if snap.get("failure_id") != expected_failure:
                    errors.append(name + ": snapshot failure ID mismatch")
                if snap.get("source_id") != expected_source:
                    errors.append(name + ": snapshot source ID mismatch")
                if snap.get("receipt_id") != expected_receipt:
                    errors.append(name + ": snapshot receipt ID mismatch")
                if snap.get("signal") != expected_signal:
                    errors.append(name + ": captured signal differs from planted source evidence")
                if snap.get("authority") is not False:
                    errors.append(name + ": snapshot has authority")
                if policy == "PRE_RECOVERY_MINIMAL_CAPTURE":
                    if set(snap) != {"failure_id", "source_id", "receipt_id", "signal", "authority"}:
                        errors.append(name + ": minimal capture contains unexpected fields")
                    if row.get("capture_cost") != 1 or row.get("deadline_missed"):
                        errors.append(name + ": minimal capture budget mismatch")
                else:
                    if snap.get("private_payload") != "FORBIDDEN_SYNTHETIC_SECRET":
                        errors.append(name + ": overcollection negative control lacks its synthetic marker")
                    if row.get("capture_cost") != 9 or not row.get("deadline_missed"):
                        errors.append(name + ": overcollection budget violation not represented")
                capture_event = "capture_minimal" if policy == "PRE_RECOVERY_MINIMAL_CAPTURE" else "capture_everything"
                if capture_event not in events or "recover" not in events or events.index(capture_event) > events.index("recover"):
                    errors.append(name + ": capture did not precede recovery")
                expected_diagnosis = expected_signal if scenario in ("cause_a", "cause_b") else None
                if row.get("diagnosis_signal") != expected_diagnosis:
                    errors.append(name + ": diagnosis unsupported by eligible captured signal")
        if row.get("post_recovery_signal") is not None:
            errors.append(name + ": transient signal remained after recovery")
        if row.get("diagnosis_signal") is not None and (snap is None or row["diagnosis_signal"] != snap.get("signal")):
            errors.append(name + ": promoted diagnosis is not bound to captured signal")
    return {"schema": "issue5960-presnapshot-lineage-audit-v1",
            "status": "PASS_AUDIT_LINEAGE_SCOPED" if not errors else "FAIL_AUDIT_LINEAGE",
            "errors": errors, "rows_audited": len(rows), "candidate_invocations": 0,
            "scope": "identity and signal lineage audit of synthetic retained construction only"}


def load_parent():
    path = PARENT / "candidate_result.json"
    data = path.read_bytes()
    return load_parent_bytes(data)


def load_parent_bytes(data):
    expected = "db147417f197b4f86d9894b5638e9a265375600acbe6476802895e461e26687c"
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError("parent candidate result SHA-256 mismatch")
    return json.loads(data.decode("utf-8"))


def main():
    result = audit(load_parent())
    (HERE / "audit_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS_AUDIT_LINEAGE_SCOPED" else 1)


if __name__ == "__main__":
    main()
