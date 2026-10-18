"""Independent raw-only audit; never imports or re-executes the candidate."""
import hashlib
import json
import subprocess
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha(path):
    return sha_bytes(Path(path).read_bytes())


def git_bytes(revision, path):
    return subprocess.run(["git", "show", f"{revision}:{path}"], cwd=REPO,
                          check=True, capture_output=True).stdout


def main():
    af = json.loads((HERE / "AUDIT_FREEZE.json").read_text())
    mismatches = []
    for relative, expected in af["local_inputs"].items():
        if sha(HERE / relative) != expected["sha256"]:
            mismatches.append({"path": relative, "error": "local-input-hash-mismatch"})

    freeze = json.loads((HERE / "FREEZE.json").read_text())
    for relative, expected in freeze["inputs"].items():
        if sha(REPO / relative) != expected["sha256"]:
            mismatches.append({"path": relative, "error": "working-tree-source-hash-mismatch"})
        if sha_bytes(git_bytes(freeze["base_main_sha"], relative)) != expected["sha256"]:
            mismatches.append({"path": relative, "error": "pinned-main-source-hash-mismatch"})
        blob = subprocess.run(["git", "rev-parse", f"{freeze['base_main_sha']}:{relative}"],
                              cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()
        if blob != expected["git_blob_sha"]:
            mismatches.append({"path": relative, "error": "pinned-main-blob-mismatch"})

    candidate_paths = {
        "SOURCE/input_owner_v13_candidate.py": "research/doom/map01_v39_cancel_release_fix_a01_20261005/input_owner_v13_candidate.py",
        "SOURCE/bridge_v2_candidate.py": "research/doom/map01_v39_cancel_release_fix_a01_20261005/bridge_v2_candidate.py",
    }
    for local, remote in candidate_paths.items():
        candidate_bytes = (HERE / local).read_bytes()
        if sha_bytes(candidate_bytes) != freeze["local_inputs"][local]["sha256"]:
            mismatches.append({"path": local, "error": "candidate-snapshot-hash-mismatch"})
        if sha_bytes(git_bytes(freeze["candidate_pr_head"], remote)) != sha_bytes(candidate_bytes):
            mismatches.append({"path": local, "error": "candidate-pr-source-mismatch"})

    owner_source = (HERE / "SOURCE/input_owner_v13_candidate.py").read_text()
    release_start = owner_source.index("def release(reason):")
    release_end = owner_source.index("        try:\n            while True", release_start)
    release_body = owner_source[release_start:release_end]
    order = [
        release_body.find("per_key_release_measurements.append"),
        release_body.find("mask = d.screen().root.query_pointer().mask"),
        release_body.find("bitmap = d.query_keymap()"),
        release_body.find("self.records.append(record)"),
    ]
    if any(position < 0 for position in order) or order != sorted(order):
        mismatches.append({"error": "owner-source-order-does-not-match-probe-boundary", "positions": order})
    bridge_source = (HERE / "SOURCE/bridge_v2_candidate.py").read_text()
    if 'if record.get("event") != "owner_release":' not in bridge_source:
        mismatches.append({"error": "bridge-does-not-show-owner-release-drain-gate"})

    raw = json.loads((HERE / "results/construction-a01/outcome.json").read_text())
    cases = {row.get("case"): row for row in raw.get("cases", [])}
    if set(cases) != {"control", "pointer_failure", "keymap_failure"}:
        mismatches.append({"error": "case-set-mismatch"})
    c = cases.get("control", {})
    if (c.get("injected_failure_count") != 0 or c.get("owner_release_record_count") != 1
            or c.get("owner_release_measurement_rows") != 1
            or c.get("bridge_release_measurement_rows") != 1
            or c.get("fake_physical_keys_at_boundary") != []
            or c.get("bridge_held_at_boundary") != []
            or c.get("owner_state_at_boundary", {}).get("owned_keycodes") != []
            or c.get("query_keymap_count") != 5):
        mismatches.append({"case": "control", "error": "control-outcome-mismatch"})
    control_release = next((r for r in c.get("owner_records_at_boundary", [])
                            if r.get("event") == "owner_release"), {})
    control_rows = control_release.get("per_key_release_measurements", [])
    if (not control_release.get("verified") or len(control_rows) != 1
            or control_rows[0].get("physical_key_measurement", {}).get("classification") != "CONFIRMED_PHYSICAL_UP"
            or control_rows[0].get("physical_key_measurement", {}).get("adapter_edge", {}).get("edge") != "up"):
        mismatches.append({"case": "control", "error": "confirmed-up-control-row-mismatch"})

    for label, expected_query_count in (("pointer_failure", 4), ("keymap_failure", 5)):
        case = cases.get(label, {})
        if (case.get("injected_failure_count") != 1 or case.get("execution_exception") is not None
                or case.get("fake_physical_keys_at_boundary") != []
                or case.get("owner_release_record_count") != 0
                or case.get("owner_release_measurement_rows") != 0
                or case.get("bridge_release_measurement_rows") != 0
                or case.get("bridge_held_at_boundary") != ["F8"]
                or case.get("owner_state_at_boundary", {}).get("owned_keycodes") != [74]
                or case.get("query_keymap_count") != expected_query_count):
            mismatches.append({"case": label, "error": "post-up-loss-outcome-mismatch"})
        if [r.get("event") for r in case.get("bridge_event_rows", [])] != ["input_admission"]:
            mismatches.append({"case": label, "error": "unexpected-bridge-event-rows"})

    audit = {
        "schema": "map01-v39-release-query-failure-probe-a01-audit-v2",
        "disposition": "PASS_RAW_AUDITED_RECORD_LOSS_REPRODUCTION" if not mismatches else "FAIL_AUDIT_MISMATCH",
        "runner_decision": raw.get("decision"),
        "base_main_source_bindings_rechecked": len(freeze["inputs"]),
        "candidate_pr_source_bindings_rechecked": len(candidate_paths),
        "cases_recomputed": len(cases),
        "release_rows_by_case": {k: cases.get(k, {}).get("bridge_release_measurement_rows")
                                  for k in ("control", "pointer_failure", "keymap_failure")},
        "owner_source_order_positions": order,
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "scope": "independent source-integrity, source-order, and raw-outcome audit; no candidate/test rerun",
        "limits": "fake-display owner/bridge ordering only; no real X11, application, task effect, useful feedback, recovery, live frequency, physical keyboard, or gameplay",
        "prior_audit_attempt": "results/audit-stop-a01/AUDIT-attempt01.json (wrapper hash-object comparison error preserved)",
    }
    (HERE / "AUDIT.json").write_text(json.dumps(audit, indent=2) + "\n")
    result = {
        "schema": "map01-v39-release-query-failure-probe-a01-result-v2",
        "disposition": audit["disposition"],
        "source_commit": raw.get("source_commit"),
        "base_main": raw.get("base_main"),
        "cases": {key: {
            "owner_release_records": cases.get(key, {}).get("owner_release_record_count"),
            "owner_measurement_rows": cases.get(key, {}).get("owner_release_measurement_rows"),
            "bridge_release_rows": cases.get(key, {}).get("bridge_release_measurement_rows"),
            "physical_keys": cases.get(key, {}).get("fake_physical_keys_at_boundary"),
            "owner_keycodes": cases.get(key, {}).get("owner_state_at_boundary", {}).get("owned_keycodes"),
            "bridge_held": cases.get(key, {}).get("bridge_held_at_boundary"),
            "query_keymap_count": cases.get(key, {}).get("query_keymap_count"),
        } for key in ("control", "pointer_failure", "keymap_failure")},
        "claim": "Both injected aggregate-query failures occurred after fake physical key-up but before owner_release append, losing the per-key row and leaving stale owner/bridge held ledgers; the uninjected control retained one confirmed-up row and reconciled neutral.",
        "limits": audit["limits"],
        "audit": "AUDIT.json",
    }
    (HERE / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"disposition": audit["disposition"], "cases": len(cases),
                      "mismatch_count": len(mismatches)}))
    if mismatches:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
