"""Clean-checkout raw-only audit; no Git objects or candidate execution required."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def git_blob_sha(data):
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    freeze = read_json(HERE / "FREEZE.json")
    audit_freeze = read_json(HERE / "AUDIT_FREEZE.json")
    repro_freeze = read_json(HERE / "REPRODUCTION_FREEZE.json")
    mismatches = []

    for relative, expected in repro_freeze["package_files"].items():
        path = HERE / relative
        if not path.is_file():
            mismatches.append({"path": relative, "error": "package-file-missing"})
        elif sha256(path.read_bytes()) != expected:
            mismatches.append({"path": relative, "error": "package-file-hash-mismatch"})

    for relative, frozen in freeze["inputs"].items():
        snapshot = HERE / "SOURCE" / "base" / relative
        if not snapshot.is_file():
            mismatches.append({"path": relative, "error": "base-source-snapshot-missing"})
            continue
        data = snapshot.read_bytes()
        if sha256(data) != frozen["sha256"]:
            mismatches.append({"path": relative, "error": "base-source-sha256-mismatch"})
        if git_blob_sha(data) != frozen["git_blob_sha"]:
            mismatches.append({"path": relative, "error": "base-source-git-blob-mismatch"})

    for relative, binding in audit_freeze["candidate_source_bindings"].items():
        snapshot = HERE / relative
        if not snapshot.is_file():
            mismatches.append({"path": relative, "error": "candidate-source-snapshot-missing"})
            continue
        data = snapshot.read_bytes()
        if sha256(data) != binding["sha256"]:
            mismatches.append({"path": relative, "error": "candidate-source-sha256-mismatch"})
        if git_blob_sha(data) != binding["blob_sha"]:
            mismatches.append({"path": relative, "error": "candidate-source-git-blob-mismatch"})

    owner_source = (HERE / "SOURCE/input_owner_v13_candidate.py").read_text(encoding="utf-8")
    release_start = owner_source.find("def release(reason):")
    release_end = owner_source.find("        try:\n            while True", release_start)
    if release_start < 0 or release_end < 0:
        mismatches.append({"error": "owner-release-function-boundary-missing"})
        release_order = []
    else:
        release_body = owner_source[release_start:release_end]
        release_order = [
            release_body.find("per_key_release_measurements.append"),
            release_body.find("mask = d.screen().root.query_pointer().mask"),
            release_body.find("bitmap = d.query_keymap()"),
            release_body.find("self.records.append(record)"),
        ]
        if any(position < 0 for position in release_order) or release_order != sorted(release_order):
            mismatches.append({"error": "owner-source-order-mismatch", "positions": release_order})

    bridge_source = (HERE / "SOURCE/bridge_v2_candidate.py").read_text(encoding="utf-8")
    if 'if record.get("event") != "owner_release":' not in bridge_source:
        mismatches.append({"error": "bridge-owner-release-drain-gate-missing"})

    raw = read_json(HERE / "results/construction-a01/outcome.json")
    cases = {row.get("case"): row for row in raw.get("cases", [])}
    expected_cases = {"control", "pointer_failure", "keymap_failure"}
    if set(cases) != expected_cases:
        mismatches.append({"error": "case-set-mismatch", "observed": sorted(cases)})

    control = cases.get("control", {})
    if (control.get("injected_failure_count") != 0
            or control.get("owner_release_record_count") != 1
            or control.get("owner_release_measurement_rows") != 1
            or control.get("bridge_release_measurement_rows") != 1
            or control.get("fake_physical_keys_at_boundary") != []
            or control.get("bridge_held_at_boundary") != []
            or control.get("owner_state_at_boundary", {}).get("owned_keycodes") != []
            or control.get("query_keymap_count") != 5):
        mismatches.append({"case": "control", "error": "control-outcome-mismatch"})
    control_release = next((row for row in control.get("owner_records_at_boundary", [])
                            if row.get("event") == "owner_release"), {})
    control_rows = control_release.get("per_key_release_measurements", [])
    if (not control_release.get("verified") or len(control_rows) != 1
            or control_rows[0].get("physical_key_measurement", {}).get("classification") != "CONFIRMED_PHYSICAL_UP"
            or control_rows[0].get("physical_key_measurement", {}).get("adapter_edge", {}).get("edge") != "up"):
        mismatches.append({"case": "control", "error": "confirmed-up-row-mismatch"})

    for label, expected_query_count in (("pointer_failure", 4), ("keymap_failure", 5)):
        case = cases.get(label, {})
        if (case.get("injected_failure_count") != 1
                or case.get("execution_exception") is not None
                or case.get("fake_physical_keys_at_boundary") != []
                or case.get("owner_release_record_count") != 0
                or case.get("owner_release_measurement_rows") != 0
                or case.get("bridge_release_measurement_rows") != 0
                or case.get("bridge_held_at_boundary") != ["F8"]
                or case.get("owner_state_at_boundary", {}).get("owned_keycodes") != [74]
                or case.get("query_keymap_count") != expected_query_count
                or [row.get("event") for row in case.get("bridge_event_rows", [])] != ["input_admission"]):
            mismatches.append({"case": label, "error": "post-up-record-loss-outcome-mismatch"})

    audit = {
        "schema": "map01-v39-release-query-failure-probe-a01-clean-checkout-audit-v3",
        "disposition": "PASS_RAW_AUDITED_RECORD_LOSS_REPRODUCTION" if not mismatches else "FAIL_AUDIT_MISMATCH",
        "raw_runner_decision": raw.get("decision"),
        "base_source_snapshots_checked": len(freeze["inputs"]),
        "candidate_source_snapshots_checked": len(audit_freeze["candidate_source_bindings"]),
        "cases_recomputed": len(cases),
        "release_rows_by_case": {key: cases.get(key, {}).get("bridge_release_measurement_rows")
                                  for key in ("control", "pointer_failure", "keymap_failure")},
        "owner_source_order_positions": release_order,
        "package_files_checked": len(repro_freeze["package_files"]),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "scope": "independent package-byte, source-order, and raw-outcome audit; no Git object access or candidate rerun",
        "limits": "fake-display owner/bridge ordering only; no real X11, application, task effect, useful feedback, recovery, live frequency, physical keyboard, or gameplay",
    }
    print(json.dumps(audit, indent=2))
    if mismatches:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
