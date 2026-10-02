"""Independent reconstruction of T0 state transitions and fail-closed gates."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def audit(result):
    errors = []
    rows = result.get("rows", [])
    expected = 9 * 3 * 32
    if len(rows) != expected:
        errors.append(f"row cardinality:{len(rows)}!={expected}")
    for row in rows:
        name = f"{row.get('scenario')}/{row.get('policy')}/{row.get('seed')}"
        events = row.get("events", [])
        snap = row.get("snapshot")
        if row.get("hazard") or row.get("zero_slack") or row.get("privacy_forbidden"):
            if events and events[0] != "safe_release_or_stop":
                errors.append(name + ": safety not first")
            if snap is not None or row.get("disposition") != "SNAPSHOT_SKIPPED_SAFETY":
                errors.append(name + ": forbidden snapshot")
        if row.get("stale_source") or row.get("receipt_missing") or row.get("observer_perturbs"):
            if snap is not None or not row.get("recovery_completed"):
                errors.append(name + ": blocked evidence promoted or immediate recovery omitted")
        if snap is not None:
            if snap.get("source_id") != row.get("source_id") or snap.get("failure_id") is None:
                errors.append(name + ": source/failure binding missing")
            if snap.get("authority") is not False:
                errors.append(name + ": snapshot grants authority")
            if "private_payload" in snap:
                if row.get("policy") != "CAPTURE_EVERYTHING" or row.get("disposition") != "CAPTURED_OVERBROAD":
                    errors.append(name + ": private payload not confined to negative control")
        expected_cost = 1 if row.get("policy") == "PRE_RECOVERY_MINIMAL_CAPTURE" and snap else (9 if row.get("policy") == "CAPTURE_EVERYTHING" and snap else 0)
        if row.get("capture_cost") != expected_cost or row.get("deadline_missed") != (expected_cost > row.get("slack_budget", -1)):
            errors.append(name + ": capture budget accounting mismatch")
        if row.get("policy") == "PRE_RECOVERY_MINIMAL_CAPTURE" and snap and row.get("deadline_missed"):
            errors.append(name + ": bounded capture exceeded deadline budget")
            if "capture_minimal" in events and events.index("capture_minimal") > events.index("recover"):
                errors.append(name + ": minimal capture after recovery")
        if row.get("diagnosis_signal") is not None:
            if row.get("cause") not in {"A", "B"} or snap is None or snap.get("source_id") != row.get("source_id"):
                errors.append(name + ": unsupported diagnosis")
        if row.get("post_recovery_signal") is not None:
            errors.append(name + ": recovery failed to erase transient signal")
    by_key = {(r["seed"], r["scenario"], r["policy"]): r for r in rows}
    for seed in range(32):
        for scenario in ("cause_a", "cause_b"):
            immediate = by_key[(seed, scenario, "IMMEDIATE_RECOVER")]
            minimal = by_key[(seed, scenario, "PRE_RECOVERY_MINIMAL_CAPTURE")]
            if immediate["diagnosis_signal"] is not None:
                errors.append(f"{seed}/{scenario}: immediate policy invented signal")
            expected_signal = "transient_focus_loss" if scenario == "cause_a" else "transient_modal_race"
            if minimal["diagnosis_signal"] != expected_signal:
                errors.append(f"{seed}/{scenario}: minimal policy lost planted distinction")
        null_row = by_key[(seed, "null_cause", "PRE_RECOVERY_MINIMAL_CAPTURE")]
        if null_row["diagnosis_signal"] is not None:
            errors.append(f"{seed}: null cause generated diagnosis")
        overbroad = by_key[(seed, "cause_a", "CAPTURE_EVERYTHING")]
        if overbroad["disposition"] != "CAPTURED_OVERBROAD" or "private_payload" not in overbroad["snapshot"]:
            errors.append(f"{seed}: negative control failed to expose overcollection")
    return {"schema": "issue5960-presnapshot-audit-v1",
            "status": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD",
            "errors": errors,
            "counts": {"rows": len(rows), "seeded_comparisons": 32,
                       "policies": 3, "scenarios": 9},
            "scope": "synthetic FSM construction only; no empirical diagnosis, runtime safety, latency or privacy claim"}


def main():
    result = json.loads((HERE / "candidate_result.json").read_text(encoding="utf-8"))
    audited = audit(result)
    (HERE / "audit_result.json").write_text(json.dumps(audited, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audited, sort_keys=True))
    raise SystemExit(0 if audited["status"] == "PASS_METHOD_SCOPED" else 1)


if __name__ == "__main__":
    main()
