"""Independent audit for the R12 counterbalanced live Win32 study."""
import hashlib
import json
from pathlib import Path

PACKET = Path(__file__).resolve().parent
RUN = PACKET / "run"
EXPECTED = {"saved": True, "text": "office", "clicked": True}
EXPECTED_ORDER = ["pair1-direct", "pair1-compiled", "pair2-compiled", "pair2-direct"]


def verify(path, base):
    failures = []
    rows = path.read_text(encoding="utf-8").splitlines()
    for row in rows:
        expected, relative = row.split("  ", 1)
        target = base / relative
        actual = hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None
        if actual != expected:
            failures.append({"path": relative, "expected": expected, "actual": actual})
    return {"entries": len(rows), "failures": failures}


pretrial = verify(PACKET / "PRETRIAL_SHA256SUMS", PACKET)
run_hashes = verify(RUN / "SHA256SUMS", RUN)
summary = json.loads((RUN / "summary.json").read_text(encoding="utf-8"))
cells = []
cell_audits = {}
for cell_id in EXPECTED_ORDER:
    folder = RUN / "cells" / cell_id
    data = json.loads((folder / "result.json").read_text(encoding="utf-8"))
    hashes = verify(folder / "SHA256SUMS", folder)
    events = data.get("events") or []
    oracle = data.get("task_oracle") or {}
    receipt = ((oracle.get("task_effect") or {}).get("receipt") or {})
    action_rows = data.get("arm_action_receipts") or []
    cleanup = data.get("cleanup") or {}
    checks = {
        "correct_cell_and_arm": data.get("cell_id") == cell_id and data.get("arm") == ("direct" if cell_id.endswith("direct") else "compiled"),
        "native_neutral_readback": (data.get("native_after") or {}).get("target_generation") == data.get("target_generation") and all(value is False for value in (data.get("native_after") or {}).get("states", {}).values()),
        "two_action_release_receipts": len(action_rows) == 2 and all(row.get("release_confirmed") is True for row in action_rows),
        "exact_fixture_effect_and_event_order": data.get("effect") == EXPECTED and sum(row.get("kind") == "click" for row in events) == 1 and [row.get("code") for row in events if row.get("kind") == "char"] == list(map(ord, "office")) and sum(row.get("kind") == "save" for row in events) == 1,
        "oracle_bound_to_terminal_action_and_generation": oracle.get("status") == "verified" and oracle.get("task_success") is True and receipt.get("call_id") == data.get("terminal_call_id") and receipt.get("operation_id") == ((data.get("terminal_retained_result") or {}).get("action") or {}).get("operation_id") and receipt.get("target_generation") == data.get("target_generation"),
        "provider_count_and_usage_reconciled": data.get("provider_turn_count") == (2 if data.get("arm") == "direct" else 1) and all(row.get("usage_matches_journal_fields") is True for row in data.get("provider_turns", [])),
        "generation_continuity": data.get("grounding_generation") == data.get("target_generation") and (data.get("checks") or {}).get("appserver_generation_continuity") is True,
        "fresh_effect_observation": (data.get("checks") or {}).get("fresh_post_dispatch_observation") is True,
        "clean_owned_resources": cleanup.get("fixture_exit_code") == 0 and cleanup.get("foreground_before") == cleanup.get("foreground_after_restore") and cleanup.get("appserver_closed") is True and data.get("server_close", {}).get("status") == "closed",
        "no_wslc_or_docker": data.get("wslc_used") is False and data.get("docker_used") is False,
        "cell_raw_hashes": not hashes["failures"],
    }
    if data.get("arm") == "direct":
        checks["second_model_decision_authorized_save"] = (data.get("direct_second_model_decision") or {}).get("save") is True
    else:
        compiled = data.get("compiled_receipt") or {}
        checks["compiled_two_transition_graph"] = (compiled.get("outcome") == "TASK_SUCCEEDED" and compiled.get("completed_transitions") == 2 and len(compiled.get("standard_action_call_ids", [])) == 2)
    passed = all(checks.values()) and data.get("status") == "PASS"
    cells.append({"cell_id": cell_id, "arm": data.get("arm"),
        "status": data.get("status"), "audit_pass": passed,
        "checks": checks, "raw_hash_audit": hashes,
        "elapsed_ns": data.get("elapsed_ns"),
        "appserver_latency_ns": data.get("appserver_latency_ns"),
        "provider_turn_count": data.get("provider_turn_count"),
        "reported_tokens": data.get("reported_tokens"),
        "public_call_counts": data.get("public_call_counts")})
    cell_audits[cell_id] = passed

pair_checks = []
for pair, direct_id, compiled_id in ((1, "pair1-direct", "pair1-compiled"),
                                     (2, "pair2-direct", "pair2-compiled")):
    pair_cells = [next((row for row in cells if row["cell_id"] == cid), None)
        for cid in (direct_id, compiled_id)]
    pair_checks.append({"pair": pair,
        "both_cells_present": all(pair_cells),
        "both_cells_pass": all(row and row["audit_pass"] for row in pair_cells)})

checks = {
    "all_four_cells_in_counterbalanced_order": summary.get("cell_count") == 4 and [row.get("cell_id") for row in summary.get("cells", [])] == EXPECTED_ORDER and summary.get("classification") == "PASS_SCOPED_COUNTERBALANCED_WIN32_MATCHED_STUDY",
    "every_cell_passes_independent_gates": len(cells) == 4 and all(cell_audits.values()),
    "both_matched_pairs_complete": len(pair_checks) == 2 and all(row["both_cells_present"] and row["both_cells_pass"] for row in pair_checks),
    "paired_differences_reconcile": len(summary.get("paired_differences", [])) == 2 and all(row.get("both_task_pass") is True for row in summary["paired_differences"]),
    "pretrial_hashes": not pretrial["failures"],
    "run_raw_hashes": not run_hashes["failures"],
    "no_wslc_or_docker": summary.get("wslc_used") is False and summary.get("docker_used") is False,
}
result = {"study_id": summary.get("study_id"),
    "classification": summary.get("classification"),
    "pretrial_hash_audit": pretrial, "run_raw_hash_audit": run_hashes,
    "cells": cells, "pairs": pair_checks, "checks": checks,
    "audit_pass": all(checks.values())}
(PACKET / "AUDIT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
    encoding="utf-8", newline="\n")
print(json.dumps(result, indent=2, sort_keys=True))
if not result["audit_pass"]:
    raise SystemExit(1)
