"""Independent raw-only audit for the one-shot Issue #3311 GUI allocation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(root: Path, source: Path):
    errors = []
    result_path = root / "RUNNER_RESULT.json"
    base = source / "research/integration/issue3311_intermediate_feedback_x11_v1"
    freeze_v1 = base / "FREEZE.json"
    freeze_v2 = base / "FREEZE_FORMAL02.json"
    runtime_path = source / "research/live_control/compiled_gui_interface_v1.py"
    if not result_path.is_file() or not freeze_v1.is_file() or not freeze_v2.is_file() or not runtime_path.is_file():
        return {"schema": "issue3311_intermediate_feedback_x11_audit_v1",
                "status": "FAIL_RAW_MISSING", "errors": ["required_file_missing"]}
    result = json.loads(result_path.read_text())
    allocation = result.get("allocation_id", "")
    freeze_path = (base / "FREEZE_FORMAL04.json" if allocation.endswith("-04") else
                   base / "FREEZE_FORMAL03.json" if allocation.endswith("-03") else
                   freeze_v2 if allocation.endswith("-02") else freeze_v1)
    freeze = json.loads(freeze_path.read_text())
    check = lambda name, ok: None if ok else errors.append(name)
    check("allocation_id", result.get("allocation_id") == freeze["allocation_id"])
    check("container_image_id", result.get("container_image_id") == freeze["container"]["image_id"])
    check("runtime_source_hash", sha(runtime_path) == freeze["runtime_source"]["sha256"] == result.get("runtime_source_sha256"))
    runner_path = source / "research/integration/issue3311_intermediate_feedback_x11_v1/runner.py"
    auditor_path = source / "research/integration/issue3311_intermediate_feedback_x11_v1/audit_raw.py"
    check("runner_harness_hash", sha(runner_path) == freeze["harness_sha256"][str(runner_path.relative_to(source))])
    check("auditor_harness_hash", sha(auditor_path) == freeze["harness_sha256"][str(auditor_path.relative_to(source))])
    if "preflight_sha256" in freeze:
        preflight_path = source / "research/integration/issue3311_intermediate_feedback_x11_v1/preflight_interface.py"
        check("interface_preflight_hash", sha(preflight_path) == freeze["preflight_sha256"])
    check("runner_exit_zero", result.get("runner_exit") == 0)
    check("runtime_task_succeeded", result.get("runtime_receipt", {}).get("outcome") == "TASK_SUCCEEDED")
    receipt = result.get("runtime_receipt", {})
    check("two_transitions", receipt.get("completed_transitions") == 2 and len(receipt.get("transitions", [])) == 2)
    check("zero_frontier_resumptions", receipt.get("frontier_model_resumptions") == 0)
    check("transition_action_order", [x.get("action") for x in receipt.get("transitions", [])] == ["request_save", "confirm_save"])
    observations = result.get("observations", [])
    titles = [row.get("window_title") for row in observations]
    check("three_distinct_live_states", titles == ["EDITING", "CONFIRMING", "SAVED"])
    window_ids = {row.get("window_id") for row in observations}
    check("same_window_identity", len(window_ids) == 1 and None not in window_ids)
    for index, row in enumerate(observations, 1):
        file = root / "observations" / f"observation-{index:02d}.png"
        check(f"observation_{index}_file", file.is_file())
        if file.is_file():
            check(f"observation_{index}_sha", sha(file) == row.get("observation", {}).get("evidence_digest"))
    admissions = result.get("admissions", [])
    check("two_fresh_admissions", len(admissions) == 2 and all(x.get("result", {}).get("eligible") is True for x in admissions))
    check("admission_state_order", [x.get("title") for x in admissions] == ["EDITING", "CONFIRMING"])
    check("admission_sequence_matches", [x.get("result", {}).get("expected_sequence") for x in admissions] == [1, 2])
    terminals = result.get("terminals", [])
    check("two_click_terminals", len(terminals) == 2 and [x.get("expected_title") for x in terminals] == ["CONFIRMING", "SAVED"])
    check("all_mouse_releases_verified", len(terminals) == 2 and all(x.get("terminal", {}).get("release") == {"verified": True, "keys_down": [], "buttons_down": []} for x in terminals))
    check("each_click_observed_expected_state", len(terminals) == 2 and all(x.get("click_exit") == 0 and x.get("mouseup_exit") == 0 and x.get("title_observed") is True for x in terminals))
    effects = result.get("independent_effect_checks", [])
    check("two_independent_stage_checks", len(effects) == 2 and all(x.get("result", {}).get("status") == "succeeded" for x in effects))
    oracle = result.get("server_oracle", {})
    check("oracle_stage_order", [x.get("stage") for x in oracle.get("events", [])] == ["CONFIRMING", "SAVED"])
    subs = oracle.get("submissions", [])
    check("one_exact_submission", len(subs) == 1 and subs[0].get("token") == "AI-3311-UNIT-01")
    if len(subs) == 1:
        check("exact_submission_bytes", subs[0].get("raw") == '{"token":"AI-3311-UNIT-01"}')
    check("page_hash", result.get("page_sha256") == freeze.get("page_sha256"))
    return {"schema": "issue3311_intermediate_feedback_x11_audit_v1",
            "status": "PASS_LIVE_INTERMEDIATE_FEEDBACK_AND_EXACT_EFFECT" if not errors else "FAIL_RAW_AUDIT",
            "checks": 30, "passed": 30 - len(errors), "errors": errors,
            "source_sha256": sha(runtime_path), "result_sha256": sha(result_path)}


if __name__ == "__main__":
    out = audit(Path(sys.argv[1]), Path(sys.argv[2]))
    print(json.dumps(out, sort_keys=True, indent=2))
    raise SystemExit(0 if not out["errors"] else 1)
