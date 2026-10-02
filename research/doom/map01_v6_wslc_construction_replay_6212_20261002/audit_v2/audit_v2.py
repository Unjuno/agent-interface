"""Independent audit v2: exact saved stdout and frozen source identities."""
import hashlib
import json
import pathlib
import sys

EXPECTED = [
    ("test_map01_recovery_cover_mechanism_v6.py", "PASS test_boundary_phase_is_retained\nPASS test_configure_new_allocation_and_workflow\nPASS test_source_orders_planner_end_before_cleanup\nPASS total 3\n"),
    ("test_map01_recovery_cover_mechanism_v5.py", "PASS test_configure_identity\nPASS test_wait_preserves_cancel_requested_then_terminal\nPASS test_wait_preserves_ordered_unmatched_events\nPASS test_wait_preserves_terminal_across_release_wait\nPASS total 4\n"),
    ("test_audit_map01_recovery_cover_mechanism_v5.py", "PASS test_allocation_substitution_and_restore\nPASS test_failure_semantics_preserved\nPASS test_hold_semantics_preserved\nPASS total 3\n"),
    ("test_audit_map01_recovery_cover_mechanism_v6.py", "PASS test_missing_summary_fails\nPASS test_valid_phase_preserves_pass\nPASS test_wrong_phase_fails\nPASS total 3\n"),
    ("test_audit_map01_recovery_cover_mechanism_v6_bound.py", "PASS_V6_BOUND_BINDINGS 6/6\n"),
]

def audit(evidence_dir, source_dir, result=None):
    evidence_dir, source_dir = pathlib.Path(evidence_dir), pathlib.Path(source_dir)
    errors = []
    if result is None:
        result = json.loads((evidence_dir / "candidate_result.json").read_text())
    manifest = json.loads((evidence_dir / "SOURCE_MANIFEST.json").read_text())
    if result.get("schema") != "wslc-construction-replay-v1": errors.append("schema")
    rows = result.get("children", [])
    if len(rows) != len(EXPECTED): errors.append("row_count")
    for i, (name, expected_stdout) in enumerate(EXPECTED):
        if i >= len(rows): break
        row = rows[i]
        if row.get("script") != name: errors.append(f"script_order:{i}")
        if row.get("exit_code") != 0: errors.append(f"exit:{name}")
        if row.get("stdout") != expected_stdout: errors.append(f"exact_stdout:{name}")
        if not isinstance(row.get("wall_ms"), (int, float)) or row["wall_ms"] <= 0: errors.append(f"wall:{name}")
    if result.get("all_children_exit_zero") is not True or any(r.get("exit_code") != 0 for r in rows): errors.append("aggregate_exit")
    cg = result.get("cgroup", {})
    if cg.get("cpu.max") != "200000 100000": errors.append("cpu_limit")
    if cg.get("memory.max") != "536870912": errors.append("memory_limit")
    try:
        peak = int(cg.get("memory.peak", "0"))
    except (TypeError, ValueError):
        peak = 0
    if peak <= 0 or peak >= 536870912: errors.append("memory_peak")
    if cg.get("memory.swap.max") != "max": errors.append("unexpected_swap_limit_claim")
    if len(manifest.get("files", [])) != 10: errors.append("source_manifest_count")
    for entry in manifest.get("files", []):
        path = source_dir / entry.get("path", "")
        try: data = path.read_bytes()
        except OSError:
            errors.append(f"missing_source:{entry.get('path')}")
            continue
        if hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest() != entry.get("blob_sha1"): errors.append(f"git_blob:{entry.get('path')}")
        if hashlib.sha256(data).hexdigest() != entry.get("sha256"): errors.append(f"sha256:{entry.get('path')}")
    return {"decision": "PASS_WSLC_CONSTRUCTION_PORTABILITY_SCOPED" if not errors else "FAIL_AUDIT",
            "errors": errors, "rows_audited": len(rows), "sources_audited": len(manifest.get("files", [])),
            "cgroup_memory_peak_bytes": peak, "cgroup_swap_limit": "unbounded_or_unavailable"}

if __name__ == "__main__":
    outcome = audit(sys.argv[1], sys.argv[2])
    print(json.dumps(outcome, sort_keys=True, separators=(",", ":")))
    raise SystemExit(bool(outcome["errors"]))
