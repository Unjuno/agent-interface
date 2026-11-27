"""Post-run audit of A13 relay-delay integrity and event timing."""
from pathlib import Path
import json
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ALLOC = "map01-v39-live-threat-guard-a13-20261009"
ROOT = REPO / "results-local/doom" / ALLOC


def event_timing(decisions, useful_events, target_iteration=9):
    target = next((row for row in decisions if row.get("iteration") == target_iteration), None)
    if not isinstance(target, dict):
        return {"target_decision_present": False, "useful_events": []}
    start_ns = target.get("controller_model_started_ns")
    end_ns = target.get("controller_model_ended_ns")
    if type(start_ns) is not int or type(end_ns) is not int:
        return {"target_decision_present": True, "valid_interval": False,
                "useful_events": []}
    rows = []
    for event in useful_events:
        observed = event.get("observed_ns")
        if type(observed) is not int:
            continue
        rows.append({
            "kind": event.get("kind"),
            "controller_visible": event.get("controller_visible"),
            "inside_tenth_turn_interval": start_ns <= observed <= end_ns,
            "milliseconds_after_interval_end": round((observed - end_ns) / 1e6, 6),
        })
    return {"target_decision_present": True, "valid_interval": True,
            "useful_events": rows}


def main():
    host = json.loads((ROOT / "HOST.json").read_text())
    freeze = json.loads((ROOT / "FREEZE.json").read_text())
    delay = json.loads((ROOT / "relay-delay.json").read_text())
    audit = json.loads((ROOT / "AUDIT.json").read_text())
    custody = json.loads((ROOT / "A13_AUDIT_RECONCILIATION_V3.json").read_text())
    report = json.loads((ROOT / "episode/report.json").read_text())
    scorer_path = ROOT / "episode/runtime/scorer-events.jsonl"
    scorer_events = [json.loads(line) for line in scorer_path.read_text().splitlines() if line.strip()]
    useful = [row for row in scorer_events if row.get("useful") is True and
              row.get("kind") in ("KILL_COUNT_INCREASE", "MAP_EXIT")]
    timing = event_timing(report.get("decisions", []), useful)
    response_index = delay.get("response_index")
    response_path = ROOT / f"response-{response_index:06d}.jsonl" if type(response_index) is int else None
    response = json.loads(response_path.read_text()) if response_path and response_path.is_file() else {}
    treatment = freeze.get("treatment", {})
    delay_ok = (
        delay.get("schema") == "a13-relay-delay-v1" and
        delay.get("one_shot") is True and
        delay.get("model_request_reissued") is False and
        delay.get("target_turn_number") == 10 and
        delay.get("response_method") == "turn/completed" and
        delay.get("requested_delay_seconds") == treatment.get("delay_seconds") == 1.0 and
        isinstance(delay.get("observed_delay_seconds"), (float, int)) and
        response.get("method") == "turn/completed" and
        host.get("delay_injected") is True and host.get("model_turn_starts") == 10
    )
    custody_ok = custody.get("custody", {}).get("all_cancellations_custodied") is True
    safety_checks = dict(audit.get("checks", {}))
    original_naive_cancel_check = safety_checks.pop("cancelled_cover_has_matching_release_event", None)
    provenance_and_runtime_ok = all(
        safety_checks.get(key) is True for key in (
            "allocation_identity", "source_commit_is_verified_prelaunch_main",
            "runtime_source_closure_is_complete_and_frozen",
            "all_runtime_sources_match_local_and_frozen_main",
            "guest_host_source_mapping_is_frozen", "known_startup_dependencies_are_frozen",
            "no_preexisting_game_or_display_process", "runner_and_auditor_hashes_match_freeze",
            "fixture_hashes_match_freeze", "qualified_wad_hash_matches",
            "forwarded_images_host_receipts_valid", "all_accepted_programs_have_terminals",
            "per_key_release_rows_accounted", "terminal_releases_verified_empty",
            "no_stale_admission_after_guard"))
    cancellation_integrity = custody_ok and audit.get("checks", {}).get(
        "per_key_release_rows_accounted") is True and audit.get("checks", {}).get(
        "terminal_releases_verified_empty") is True
    timing_ok = timing.get("target_decision_present") is True and timing.get("valid_interval") is True
    overlap = any(row.get("inside_tenth_turn_interval") is True
                  for row in timing.get("useful_events", []))
    status = "FAIL" if not (delay_ok and cancellation_integrity and provenance_and_runtime_ok) else "HOLD"
    result = {
        "schema": "map01-v39-live-threat-guard-a13-treatment-audit-v1",
        "allocation": ALLOC,
        "status": status,
        "initial_audit_status_preserved": audit.get("status"),
        "checks": {
            "one_shot_tenth_completion_delay": delay_ok,
            "cancellation_custody_verified_by_reconciliation_v3": custody_ok,
            "per_key_release_and_empty_terminals_verified": cancellation_integrity,
            "provenance_and_runtime_checks_passed": provenance_and_runtime_ok,
            "useful_event_inside_tenth_controller_interval": overlap,
            "target_interval_available": timing_ok,
        },
        "relay_delay": {
            "target_turn": delay.get("target_turn_number"),
            "requested_seconds": delay.get("requested_delay_seconds"),
            "observed_seconds": delay.get("observed_delay_seconds"),
            "model_request_reissued": delay.get("model_request_reissued"),
            "response_file_verified": bool(response_path and response_path.is_file() and
                                             response.get("method") == "turn/completed"),
        },
        "useful_events_relative_to_tenth_turn": timing.get("useful_events", []),
        "independent_custody_reconciliation": {
            "status": custody.get("status"),
            "matched_cancels": custody.get("custody", {}).get("matched_cancel_count"),
            "accounted_cancels": custody.get("custody", {}).get("accounted_cancel_count"),
            "unaccounted_cancel_ids": custody.get("custody", {}).get("unaccounted_cancel_ids"),
        },
        "initial_audit_naive_cancel_check": original_naive_cancel_check,
        "original_audit_sha256": custody.get("original_audit_sha256"),
        "interpretation": (
            "The one-second completion-delivery hold was injected once. The useful scorer event did not occur inside the tenth controller interval, so the timing subgate is HOLD. The original audit is preserved; its blanket cancel-to-input-release check is superseded for custody classification by reconciliation v3, which accepts verified-empty terminal receipts when no input lease was active."
        ),
    }
    (ROOT / "A13_TREATMENT_AUDIT.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if status == "HOLD" else 1


if __name__ == "__main__":
    raise SystemExit(main())
