"""Supplement the frozen C02 audit with admission-to-keymap time binding."""
import hashlib
import json
import os
import tempfile
from pathlib import Path

import audit as parent_audit


ROOT = Path(__file__).resolve().parent
PASS = "PASS_V39_XVFB_KEYMAP_TEMPORAL_BINDING_SCOPED"
FAIL = "FAIL_OR_HOLD_V39_KEYMAP_TEMPORAL_BINDING"


def _write_report(path, report):
    """Replace the report atomically so readers never see a partial JSON file."""
    path = Path(path)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(report, stream, sort_keys=True, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


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
    report_path = ROOT / "AUDIT_V2.json"
    report = {
        "schema": "map01-v39-owner-keymap-witness-audit-v2",
        "gate": FAIL,
        "checks": {"audit_completed": False, "input_documents_are_objects": False},
        "failed_checks": ["audit_completed", "input_documents_are_objects"],
        "scope": "virtual X11 server state and admission interval ordering only",
        "error": "audit did not complete",
    }
    # Remove any prior PASS before reading inputs. If loading, validation, or
    # evaluation fails, the final structured report below replaces this HOLD.
    _write_report(report_path, report)
    try:
        names = ("candidate.raw.json", "cases.json", "FREEZE.json",
                 "candidate.started.json", "ENVIRONMENT.json")
        documents = {
            name: json.loads((ROOT / name).read_text(encoding="utf-8"))
            for name in names
        }
        malformed = [name for name, value in documents.items()
                     if not isinstance(value, dict)]
        if malformed:
            raise ValueError("JSON roots must be objects: " + ", ".join(malformed))
        report = build_report(
            documents["candidate.raw.json"], documents["cases.json"],
            documents["FREEZE.json"], documents["candidate.started.json"],
            documents["ENVIRONMENT.json"],
        )
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
    report["checks"]["audit_completed"] = "error" not in report
    report["checks"]["input_documents_are_objects"] = "error" not in report
    report["failed_checks"] = sorted(
        name for name, passed in report["checks"].items() if not passed
    )
    _write_report(report_path, report)
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if report["gate"] == PASS and not report["failed_checks"] else 1)


if __name__ == "__main__":
    main()
