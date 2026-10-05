"""Additive fail-closed root-shape audit for the retained C02 evidence."""
import hashlib
import json
from pathlib import Path

import audit as parent_audit
import audit_temporal_v2 as previous_temporal_audit


ROOT = Path(__file__).resolve().parent
PASS = "PASS_V39_XVFB_KEYMAP_TEMPORAL_BINDING_V3_SCOPED"
FAIL = "FAIL_OR_HOLD_V39_KEYMAP_TEMPORAL_BINDING_V3"


def evaluate_temporal_binding(raw, cases):
    if not isinstance(raw, dict):
        return {"all_occurrences_temporally_bound": False,
                "occurrences": [], "reason": "raw_root_not_object"}
    if not isinstance(cases, dict):
        return {"all_occurrences_temporally_bound": False,
                "occurrences": [], "reason": "cases_root_not_object"}
    return previous_temporal_audit.evaluate_temporal_binding(raw, cases)


def build_report(raw, cases, freeze, started, environment):
    parent_error = None
    try:
        parent_checks = parent_audit.evaluate(raw, cases, freeze, started, environment)
    except Exception as exc:
        parent_checks = {}
        parent_error = f"{type(exc).__name__}: {exc}"
    temporal = evaluate_temporal_binding(raw, cases)
    checks = {f"parent_{name}": passed for name, passed in parent_checks.items()}
    checks["parent_evaluator_completed"] = parent_error is None
    checks["admission_timestamps_within_key_down_witness"] = temporal[
        "all_occurrences_temporally_bound"]
    report = {
        "schema": "map01-v39-owner-keymap-witness-audit-v3",
        "gate": PASS if all(checks.values()) else FAIL,
        "checks": checks,
        "failed_checks": sorted(name for name, passed in checks.items() if not passed),
        "scope": "virtual X11 server state and admission interval ordering only",
        "provenance": {
            "parent_freeze_sha256": hashlib.sha256((ROOT / "FREEZE.json").read_bytes()).hexdigest(),
            "candidate_raw_sha256": hashlib.sha256((ROOT / "candidate.raw.json").read_bytes()).hexdigest(),
            "cases_sha256": hashlib.sha256((ROOT / "cases.json").read_bytes()).hexdigest(),
            "auditor_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "temporal_v2_helper_sha256": hashlib.sha256(
                Path(previous_temporal_audit.__file__).read_bytes()).hexdigest(),
        },
        "admission_intervals": temporal["occurrences"],
    }
    if parent_error is not None:
        report["parent_evaluator_error"] = parent_error
    if "reason" in temporal:
        report["temporal_evaluator_error"] = temporal["reason"]
    return report


def main():
    names = ("candidate.raw.json", "cases.json", "FREEZE.json",
             "candidate.started.json", "ENVIRONMENT.json")
    documents = {}
    errors = []
    for name in names:
        try:
            value = json.loads((ROOT / name).read_text(encoding="utf-8"))
            if not isinstance(value, dict):
                raise ValueError(f"JSON root must be an object: {name}")
            documents[name] = value
        except Exception as exc:
            errors.append(f"{name}: {type(exc).__name__}: {exc}")
            documents[name] = {}
    raw = documents["candidate.raw.json"]
    cases = documents["cases.json"]
    freeze = documents["FREEZE.json"]
    started = documents["candidate.started.json"]
    environment = documents["ENVIRONMENT.json"]
    report = build_report(raw, cases, freeze, started, environment)
    if errors:
        report["checks"]["input_documents_are_objects"] = False
        report["checks"]["audit_completed"] = False
        report["failed_checks"] = sorted(
            name for name, passed in report["checks"].items() if not passed)
        report["gate"] = FAIL
        report["input_errors"] = errors
    (ROOT / "AUDIT_V3.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                                        encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if report["gate"] == PASS else 1)


if __name__ == "__main__":
    main()
