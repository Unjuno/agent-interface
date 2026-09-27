"""Independent stdlib-only raw-output auditor for successor Issue #4998."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

EXPECTED_SOURCE_HASHES = {
    "base_model.py": "eb6f025b2557728683d54ebf86fcb0b32c48f3e12a9debbf736eddeb51c5774f",
    "cases.json": "75d26a48ca7ed3d24587170f2a66dd6c9da6027bc0602917b82ef9add796d84e",
    "candidate.py": "efbd1765a4d7fe331fcf37331b592497cd0ae5228b4a4756ad8992eb59e60194",
    "runner.py": "96f81090666b7992724f4aaa5241334c2c026f3d1f8ceb3e7cd274edaf9c4915",
}
EXPECTED = [
    ("capability_touch_missing", "pointer_track_v2", "EXECUTABLE", False),
    ("mae_out_of_envelope", "raw_current_v1", "FALLBACK", False),
    ("hint_no_revalidation", "fresh_resolve_v1", "FALLBACK", False),
    ("hint_with_revalidation", "cached_route_v1", "EXECUTABLE_AFTER_REVALIDATION", True),
    ("resource_conflict", "keyboard_adjust_v1", "FALLBACK", False),
    ("surface_mismatch", "desktop_click_v1", "FALLBACK", False),
    ("version_envelope", "reveal_v2", "EXECUTABLE", False),
    ("universal_fallback", "universal_control_v1", "FALLBACK", False),
]
CONTROL_IDS = {
    "no_selection", "wrong_candidate", "hint_before_revalidation",
    "wrong_session_receipt", "stale_receipt", "tampered_provenance",
    "hint_role_promotion",
}


def audit(raw_path: Path, source_dir: Path) -> dict:
    errors: list[str] = []
    def check(ok: bool, label: str) -> None:
        if not ok:
            errors.append(label)

    try:
        payload = json.loads(raw_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"schema": "issue-4998-independent-audit-v1", "pass": False,
                "errors": [f"raw_json:{type(exc).__name__}:{exc}"]}

    check(payload.get("schema") == "skill-card-two-phase-4976-raw-v1", "schema")
    check(payload.get("issue") == 4998, "issue")
    check(payload.get("allocation") == "skill-card-two-phase-4976-20260928-01", "allocation")
    check(payload.get("main_commit") == "4fa988e2872e20f4da840c91fbdd83a8d0ff8d12", "main_commit")
    actual_hashes = {
        name: hashlib.sha256((source_dir / name).read_bytes()).hexdigest()
        for name in EXPECTED_SOURCE_HASHES
    }
    check(actual_hashes == EXPECTED_SOURCE_HASHES, "frozen_source_hashes")
    check(payload.get("source_hashes") == EXPECTED_SOURCE_HASHES, "reported_source_hashes")
    check(payload.get("registry_sha256_before") == payload.get("registry_sha256_after"), "registry_immutable")
    for field in ("model_calls", "gui_calls", "action_emissions", "authority_grants"):
        check(payload.get(field) == 0, f"zero_{field}")

    rows = payload.get("rows")
    check(isinstance(rows, list) and len(rows) == len(EXPECTED), "row_count")
    if isinstance(rows, list) and len(rows) == len(EXPECTED):
        for index, (row, expected) in enumerate(zip(rows, EXPECTED)):
            case_id, key, final_status, needs_revalidation = expected
            check(row.get("case_id") == case_id, f"row_{index}_case")
            check(row.get("expected_key") == key and row.get("selected_key") == key, f"row_{index}_selected_key")
            check(row.get("expected_status") == final_status and row.get("final_status") == final_status,
                  f"row_{index}_final_status")
            check(row.get("selected_status") == ("REVALIDATION_REQUIRED" if needs_revalidation else final_status),
                  f"row_{index}_selected_status")
            check(row.get("candidate_keys") == [key], f"row_{index}_single_candidate")
            check(row.get("preselection_detail_loads") == [], f"row_{index}_preselection_no_detail")
            check(row.get("detail_loaded") == [key], f"row_{index}_only_selected_detail")
            check(row.get("detail") == {
                "implementation_ref": {
                    "pointer_track_v2": "impl://pointer-track-v2", "raw_current_v1": "impl://raw-current-v1",
                    "fresh_resolve_v1": "impl://fresh-resolve-v1", "cached_route_v1": "impl://cached-route-v1",
                    "keyboard_adjust_v1": "impl://keyboard-adjust-v1", "desktop_click_v1": "impl://desktop-click-v1",
                    "reveal_v2": "impl://reveal-v2", "universal_control_v1": "impl://universal-control-v1",
                }[key],
                "provenance": {
                    "pointer_track_v2": "evidence://6-pointer", "raw_current_v1": "evidence://raw-fallback",
                    "fresh_resolve_v1": "evidence://current-resolution", "cached_route_v1": "evidence://663-hint",
                    "keyboard_adjust_v1": "evidence://keyboard", "desktop_click_v1": "evidence://desktop",
                    "reveal_v2": "evidence://new-envelope", "universal_control_v1": "evidence://universal",
                }[key],
                "version": "2" if key in ("pointer_track_v2", "reveal_v2") else "1",
            }, f"row_{index}_detail_integrity")
            events = row.get("events")
            wanted = ["PRESENT_CANDIDATES", "SELECT_CANDIDATE"]
            if needs_revalidation:
                wanted.append("REVALIDATE_CURRENT")
            wanted.append("LOAD_SELECTED_DETAIL")
            check(isinstance(events, list) and [e.get("type") for e in events] == wanted,
                  f"row_{index}_event_order")
            if isinstance(events, list):
                check([e.get("seq") for e in events] == list(range(1, len(wanted) + 1)),
                      f"row_{index}_event_sequence")
                check(all(e.get("session_id") == f"session-{index:02d}" and e.get("case_id") == case_id for e in events),
                      f"row_{index}_event_scope")
                check(events[-1].get("candidate_key") == key, f"row_{index}_load_bound_to_selection")
            check(row.get("filter_log") and row["filter_log"][-1].get("applicable") is True,
                  f"row_{index}_filter_accepts_selected")
            if needs_revalidation:
                receipt = row.get("revalidation_receipt")
                check(isinstance(receipt, dict), "hint_receipt_present")
                if isinstance(receipt, dict):
                    check(receipt.get("source_role") == "HINT" and
                          receipt.get("output_role") == "ADMISSION_DEPENDENCY" and
                          receipt.get("freshness") == "CURRENT" and
                          receipt.get("candidate_key") == key and
                          receipt.get("session_id") == f"session-{index:02d}" and
                          receipt.get("case_id") == case_id and
                          receipt.get("source_skill_version") == "1" and
                          receipt.get("source_provenance") == "evidence://663-hint" and
                          receipt.get("event_seq") == 3 and
                          receipt.get("receipt_id") == f"current-revalidation::{key}::{case_id}",
                          "hint_receipt_scope_and_provenance")
            else:
                check(row.get("revalidation_receipt") is None, f"row_{index}_no_unneeded_receipt")

    controls = payload.get("negative_controls")
    check(isinstance(controls, list) and {c.get("control_id") for c in controls} == CONTROL_IDS,
          "negative_control_inventory")
    if isinstance(controls, list):
        for control in controls:
            name = control.get("control_id", "unknown")
            check(control.get("refused") is True and bool(control.get("reason")), f"control_{name}_refused")
            check(control.get("detail_loaded") == [], f"control_{name}_no_detail")
            check(isinstance(control.get("events"), list) and
                  all(event.get("type") != "LOAD_SELECTED_DETAIL" for event in control["events"]),
                  f"control_{name}_no_load_event")
            if name in {"wrong_session_receipt", "stale_receipt", "tampered_provenance"}:
                check([e.get("type") for e in control["events"]] ==
                      ["PRESENT_CANDIDATES", "SELECT_CANDIDATE", "REVALIDATE_CURRENT"],
                      f"control_{name}_rejected_after_revalidation_before_load")
    report = {"schema": "issue-4998-independent-audit-v1", "pass": not errors,
              "errors": errors, "rows_checked": len(rows) if isinstance(rows, list) else 0,
              "controls_checked": len(controls) if isinstance(controls, list) else 0,
              "source_hashes": actual_hashes, "side_effects": "all_zero" if not errors else "see_errors"}
    return report


if __name__ == "__main__":
    root = Path(sys.argv[1])
    result = audit(root / "raw.json", root / "src")
    print(json.dumps(result, sort_keys=True))
    if not result["pass"]:
        raise SystemExit(1)
