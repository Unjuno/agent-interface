"""Independent read-only auditor for the Issue #3633 formal result."""
import hashlib
import json
import sys
from pathlib import Path


def canonical_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def main(path):
    raw = json.loads(Path(path).read_text())
    errors = []
    claimed = raw.pop("raw_sha256", None)
    if canonical_digest(raw) != claimed:
        errors.append("raw_digest_mismatch")
    if raw.get("allocation_id") != "issue3633-readiness-identity-v4-formal-01":
        errors.append("allocation_id")
    if raw.get("apps") != ["inkscape", "libreoffice", "chromium"]:
        errors.append("app_set")
    ops = raw.get("forbidden_operations", {})
    if ops != {"geometry": 0, "focus": 0, "input": 0, "model": 0, "network": 0}:
        errors.append("forbidden_operation_count")
    selected, repeated = raw.get("selected", {}), raw.get("repeated", {})
    expected = ("inkscape", "libreoffice", "chromium")
    valid = True
    identities = []
    for app in expected:
        a, b = selected.get(app), repeated.get(app)
        if not isinstance(a, dict) or not isinstance(b, dict):
            errors.append(f"identity_shape:{app}")
            valid = False
            continue
        for row in (a, b):
            if (type(row.get("window_id")) is not int or row["window_id"] <= 0
                    or type(row.get("pid")) is not int or row["pid"] <= 0
                    or row.get("display") != raw.get("display")
                    or not row.get("title") or not row.get("wm_class")):
                errors.append(f"identity_fields:{app}")
                valid = False
        if a != b:
            errors.append(f"identity_unstable:{app}")
            valid = False
        identities.append((a.get("window_id"), a.get("pid")))
        if not any(app_token in (a.get("title", "") + " " + a.get("wm_class", "")).casefold()
                   for app_token in ({"inkscape": ("inkscape",),
                                      "libreoffice": ("libreoffice calc",),
                                      "chromium": ("chromium",)}[app])):
            errors.append(f"app_filter:{app}")
            valid = False
    if len(set(identities)) != 3:
        errors.append("distinct_identity_set")
        valid = False
    unit = raw.get("unit_gate", {})
    if unit.get("returncode") != 0 or "Ran 4 tests" not in unit.get("stderr", ""):
        errors.append("unit_gate")
    cleanup = raw.get("cleanup", {})
    if not cleanup.get("x_socket_absent"):
        errors.append("x_socket_cleanup")
    for name, row in cleanup.items():
        if name == "x_socket_absent":
            continue
        if not row.get("reaped"):
            errors.append(f"process_not_reaped:{name}")
    decision = raw.get("decision")
    if decision == "PASS_READINESS_IDENTITY_V4_SCOPED" and not (valid and not errors):
        errors.append("pass_gate_not_satisfied")
    if decision == "STOP_READINESS_IDENTITY_UNAVAILABLE":
        readiness = raw.get("readiness")
        if readiness is None:
            if not raw.get("error"):
                errors.append("stop_without_readiness_or_reason")
        elif readiness.get("admitted") is not False or readiness.get("reason") not in (
                "app_set", "identity", "ambiguous", "unstable", "duplicate",
                "display", "expected_apps", "shape"):
            errors.append("stop_not_explained_by_readiness")
        elif valid:
            errors.append("stop_despite_valid_identities")
    classification = ("AUDIT_PASS_PASS_CLASSIFICATION"
                      if decision == "PASS_READINESS_IDENTITY_V4_SCOPED" and not errors
                      else "AUDIT_PASS_STOP_CLASSIFICATION"
                      if decision == "STOP_READINESS_IDENTITY_UNAVAILABLE" and not errors
                      else "AUDIT_FAIL")
    audit = {"decision": decision, "audit_classification": classification,
             "independent_errors": errors,
             "identity_shape_valid": valid, "raw_sha256": claimed,
             "PASS_READINESS_IDENTITY_V4_SCOPED":
                 decision == "PASS_READINESS_IDENTITY_V4_SCOPED" and valid and not errors}
    print(json.dumps(audit, sort_keys=True))
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
