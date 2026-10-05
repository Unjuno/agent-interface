"""Independent raw-only audit of the one-shot query-failure probe."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    mismatches = []
    for path, expected in freeze["inputs"].items():
        if sha(REPO / path) != expected:
            mismatches.append({"path": path, "error": "input-hash-mismatch"})
    for path, expected in freeze["local_inputs"].items():
        if sha(HERE / path) != expected:
            mismatches.append({"path": path, "error": "local-input-hash-mismatch"})

    raw = json.loads((HERE / "results/construction-a01/outcome.json").read_text())
    by_case = {row.get("case"): row for row in raw.get("cases", [])}
    if set(by_case) != {"control", "pointer_failure", "keymap_failure"}:
        mismatches.append({"error": "case-set-mismatch"})
    control = by_case.get("control", {})
    if (control.get("injected_failure_count") != 0 or control.get("owner_release_record_count") != 1
            or control.get("owner_release_measurement_rows") != 1
            or control.get("bridge_release_measurement_rows") != 1
            or control.get("fake_physical_keys_at_boundary") != []
            or control.get("bridge_held_at_boundary") != []
            or control.get("owner_state_at_boundary", {}).get("owned_keycodes") != []):
        mismatches.append({"case": "control", "error": "control-row-or-neutrality-mismatch"})

    for label in ("pointer_failure", "keymap_failure"):
        case = by_case.get(label, {})
        if (case.get("injected_failure_count") != 1 or case.get("fake_physical_keys_at_boundary") != []
                or case.get("owner_release_record_count") != 0
                or case.get("owner_release_measurement_rows") != 0
                or case.get("bridge_release_measurement_rows") != 0
                or case.get("bridge_held_at_boundary") != ["F8"]
                or case.get("owner_state_at_boundary", {}).get("owned_keycodes") != [74]):
            mismatches.append({"case": label, "error": "expected-post-up-record-loss-not-observed"})

    expected = not mismatches
    audit = {
        "schema": "map01-v39-release-query-failure-probe-a01-audit-v1",
        "disposition": "PASS_RAW_AUDITED_RECORD_LOSS_REPRODUCTION" if expected else "FAIL_AUDIT_MISMATCH",
        "cases_recomputed": len(by_case),
        "source_hashes_checked": len(freeze["inputs"]),
        "local_source_hashes_checked": len(freeze["local_inputs"]),
        "raw_runner_decision": raw.get("decision"),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "scope": "independent integrity and raw-row audit; no candidate/test rerun",
        "limits": "fake-display owner/bridge ordering only; no real X11, application, task effect, useful feedback, recovery, live frequency, or gameplay",
    }
    (HERE / "AUDIT.json").write_text(json.dumps(audit, indent=2) + "\n")
    result = {
        "schema": "map01-v39-release-query-failure-probe-a01-result-v1",
        "disposition": audit["disposition"],
        "source_commit": raw.get("source_commit"),
        "base_main": raw.get("base_main"),
        "cases": {key: {"owner_release_records": by_case.get(key, {}).get("owner_release_record_count"),
                        "owner_measurement_rows": by_case.get(key, {}).get("owner_release_measurement_rows"),
                        "bridge_release_rows": by_case.get(key, {}).get("bridge_release_measurement_rows"),
                        "physical_keys": by_case.get(key, {}).get("fake_physical_keys_at_boundary"),
                        "owner_keycodes": by_case.get(key, {}).get("owner_state_at_boundary", {}).get("owned_keycodes"),
                        "bridge_held": by_case.get(key, {}).get("bridge_held_at_boundary")}
                   for key in ("control", "pointer_failure", "keymap_failure")},
        "claim": "Both injected aggregate-query failures occurred after fake physical key-up but before owner_release append, losing the per-key row and leaving stale owner/bridge held ledgers; the uninjected control retained one row and reconciled neutral.",
        "limits": audit["limits"],
        "audit": "AUDIT.json",
    }
    (HERE / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"disposition": audit["disposition"], "cases": len(by_case),
                      "mismatch_count": len(mismatches)}))
    if mismatches:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
