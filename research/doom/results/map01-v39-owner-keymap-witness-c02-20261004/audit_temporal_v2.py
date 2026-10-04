"""Supplement the frozen C02 audit with admission-to-keymap time binding."""
import hashlib
import json
from pathlib import Path

import audit as parent_audit


ROOT = Path(__file__).resolve().parent
PASS = "PASS_V39_XVFB_KEYMAP_TEMPORAL_BINDING_SCOPED"


def evaluate_temporal_binding(raw, cases):
    rows = []
    occurrences = raw.get("occurrences") if isinstance(raw.get("occurrences"), list) else []
    events = raw.get("events") if isinstance(raw.get("events"), list) else []
    overall = (len(occurrences) == cases.get("occurrences") == 2
               and all(isinstance(event, dict) for event in events))
    for occurrence in occurrences:
        if not isinstance(occurrence, dict):
            rows.append({"ordered_within_down_interval": False,
                         "reason": "occurrence_not_object"})
            overall = False
            continue
        token = occurrence.get("intent_token")
        admissions = [event for event in events
                      if isinstance(event, dict)
                      and event.get("event") == "input_admission"
                      and event.get("intent_token") == token
                      and event.get("key") == cases.get("key")]
        samples = [occurrence.get("pre_down"), occurrence.get("post_down")]
        times = []
        for sample, field in ((samples[0], "sample_finished_ns"),
                              (samples[1], "sample_started_ns"),
                              (samples[1], "sample_finished_ns")):
            value = sample.get(field) if isinstance(sample, dict) else None
            times.append(value if type(value) is int else None)
        admitted = admissions[0].get("admitted_ns") if len(admissions) == 1 else None
        acknowledged = admissions[0].get("input_ack_ns") if len(admissions) == 1 else None
        valid_until = admissions[0].get("valid_until_ns") if len(admissions) == 1 else None
        valid = (
            len(admissions) == 1
            and all(type(value) is int for value in times)
            and type(admitted) is int and type(acknowledged) is int
            and type(valid_until) is int
            and times[0] <= admitted <= acknowledged <= times[1] <= times[2]
            and times[2] < valid_until
        )
        rows.append({
            "intent_token": token,
            "matching_admission_count": len(admissions),
            "pre_down_finished_ns": times[0],
            "admitted_ns": admitted,
            "input_ack_ns": acknowledged,
            "valid_until_ns": valid_until,
            "post_down_started_ns": times[1],
            "post_down_finished_ns": times[2],
            "ordered_within_down_interval": valid,
        })
        overall = overall and valid
    return {"all_occurrences_temporally_bound": overall,
            "occurrences": rows}


def build_report(raw, cases, freeze, started, environment):
    parent_error = None
    try:
        parent_checks = parent_audit.evaluate(raw, cases, freeze, started, environment)
    except Exception as exc:
        # Malformed retained evidence must produce a failing report, not abort
        # before replacing a stale PASS report.
        parent_checks = {}
        parent_error = f"{type(exc).__name__}: {exc}"
    temporal = evaluate_temporal_binding(raw, cases)
    checks = {f"parent_{name}": passed for name, passed in parent_checks.items()}
    checks["parent_evaluator_completed"] = parent_error is None
    checks["admission_timestamps_within_key_down_witness"] = temporal[
        "all_occurrences_temporally_bound"]
    report = {
        "schema": "map01-v39-owner-keymap-witness-audit-v2",
        "gate": PASS if all(checks.values()) else "FAIL_OR_HOLD_V39_KEYMAP_TEMPORAL_BINDING",
        "checks": checks,
        "failed_checks": sorted(name for name, passed in checks.items() if not passed),
        "scope": "virtual X11 server state and admission interval ordering only",
        "provenance": {
            "parent_freeze_sha256": hashlib.sha256((ROOT / "FREEZE.json").read_bytes()).hexdigest(),
            "candidate_raw_sha256": hashlib.sha256((ROOT / "candidate.raw.json").read_bytes()).hexdigest(),
            "cases_sha256": hashlib.sha256((ROOT / "cases.json").read_bytes()).hexdigest(),
            "auditor_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
        "admission_intervals": temporal["occurrences"],
    }
    if parent_error is not None:
        report["parent_evaluator_error"] = parent_error
    return report


def main():
    raw = json.loads((ROOT / "candidate.raw.json").read_text(encoding="utf-8"))
    cases = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    started = json.loads((ROOT / "candidate.started.json").read_text(encoding="utf-8"))
    environment = json.loads((ROOT / "ENVIRONMENT.json").read_text(encoding="utf-8"))
    report = build_report(raw, cases, freeze, started, environment)
    (ROOT / "AUDIT_V2.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                                        encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if report["gate"] == PASS else 1)


if __name__ == "__main__":
    main()
