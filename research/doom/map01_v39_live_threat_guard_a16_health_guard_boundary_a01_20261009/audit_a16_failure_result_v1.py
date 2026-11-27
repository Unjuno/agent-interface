"""Post-run reconciliation for an A16 terminal failure without report.json."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ALLOC = "map01-v39-live-threat-guard-a16-health-guard-boundary-20261009"
ROOT = REPO / "results-local/doom" / ALLOC
PROVENANCE = (
    "allocation_identity", "source_commit_is_verified_prelaunch_main",
    "runtime_source_closure_is_complete_and_frozen",
    "all_runtime_sources_match_local_and_frozen_main",
    "guest_host_source_mapping_is_frozen", "known_startup_dependencies_are_frozen",
    "no_preexisting_game_or_display_process", "runner_and_auditor_hashes_match_freeze",
    "fixture_hashes_match_freeze", "qualified_wad_hash_matches",
    "forwarded_images_host_receipts_valid",
)
SAFETY = (
    "all_accepted_programs_have_terminals", "cancellation_custody_reconciled",
    "per_key_release_rows_accounted", "terminal_releases_verified_empty",
    "no_stale_admission_after_guard",
)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def reconcile_owner_log(owner_rows, expected_keyup_count):
    if not isinstance(owner_rows, list) or not owner_rows:
        return {"closed": False, "reason": "missing_or_empty_log"}
    keyups = [row for row in owner_rows if row.get("event") == "owner_explicit_keyup"]
    releases = [row for row in owner_rows if row.get("event") == "owner_release"]
    close = [row for row in releases if row.get("reason") == "close"]
    keyups_ok = all(row.get("server_keyup_verified") is True and
                    row.get("server_sync_completed") is True and
                    row.get("server_key_down_after_keyup") is False
                    for row in keyups)
    releases_ok = all(row.get("verified") is True and row.get("keys_down") == [] and
                      row.get("buttons_down") == [] and row.get("keys_unknown") == []
                      and row.get("key_state_errors") == []
                      for row in releases)
    keyup_count_matches_custody = (
        type(expected_keyup_count) is int and expected_keyup_count >= 0 and
        len(keyups) == expected_keyup_count)
    closed = (owner_rows[-1] in close and len(close) == 1 and keyups_ok and releases_ok
              and keyup_count_matches_custody)
    return {
        "closed": closed,
        "close_receipt_count": len(close),
        "final_event_is_close": owner_rows[-1] in close,
        "explicit_keyup_count": len(keyups),
        "expected_explicit_keyup_count": (expected_keyup_count
                                           if type(expected_keyup_count) is int else None),
        "explicit_keyup_count_matches_custody": keyup_count_matches_custody,
        "verified_explicit_keyups": sum(
            row.get("server_keyup_verified") is True and
            row.get("server_sync_completed") is True and
            row.get("server_key_down_after_keyup") is False for row in keyups),
        "owner_release_count": len(releases),
        "verified_empty_owner_releases": sum(
            row.get("verified") is True and row.get("keys_down") == [] and
            row.get("buttons_down") == [] and row.get("keys_unknown") == [] and
            row.get("key_state_errors") == []
            for row in releases),
        "physical_key_state_authoritative": False,
    }


def observed_zero_matches(events, source_refresh):
    if not isinstance(source_refresh, dict):
        return False

    def typed_zero_at(sequence):
        matches = [row for row in events
                   if row.get("event") == "typed_observation" and
                   type(row.get("sequence")) is int and
                   row.get("sequence") == sequence]
        if len(matches) != 1:
            return False
        row = matches[0]
        signal = row.get("signals", {}).get("health", {})
        return (
            signal.get("signal_id") == "health" and
            signal.get("status") == "observed" and
            type(signal.get("value")) is int and signal.get("value") == 0 and
            type(signal.get("sequence")) is int and
            signal.get("sequence") == sequence and
            type(row.get("capture_ns")) is int and
            type(signal.get("capture_ns")) is int and
            signal.get("capture_ns") == row.get("capture_ns")
        )

    return (
        type(source_refresh.get("iteration")) is int and
        source_refresh.get("iteration") == 12 and
        type(source_refresh.get("source_sequence")) is int and
        source_refresh.get("source_sequence") == 338 and
        source_refresh.get("reason") == "invalid_observed_health" and
        typed_zero_at(325) and typed_zero_at(338)
    )


def build_result(freeze, audit, custody, host, score, failure, source_refresh,
                 events, owner_rows, *, report_present):
    if report_present:
        raise ValueError("failure reconciliation is only for runs without report.json")
    checks = audit.get("checks", {})
    provenance_ok = all(checks.get(key) is True for key in PROVENANCE)
    safety_ok = all(checks.get(key) is True for key in SAFETY)
    custody_ok = custody.get("custody_pass") is True
    owner_log = reconcile_owner_log(
        owner_rows, custody.get("owner_keyups_matching_key_and_token"))
    zero_health_join = observed_zero_matches(events, source_refresh)
    status = "FAIL" if not (provenance_ok and safety_ok and custody_ok and
                             owner_log["closed"] and zero_health_join) else "STOP"
    typed_health = [value for value in audit.get("health_values", [])
                    if type(value) is int]
    typed_ammo = [value for value in audit.get("ammo_values", [])
                  if type(value) is int]
    source_refresh = source_refresh if isinstance(source_refresh, dict) else {}
    counts = audit.get("counts", {})
    result = {
        "schema": "map01-v39-live-threat-guard-a16-health-guard-boundary-failure-result-v1",
        "allocation": ALLOC,
        "status": status,
        "original_audit_status_preserved": audit.get("status"),
        "provenance_checks_passed": provenance_ok,
        "terminal_input_checks_passed": safety_ok,
        "independent_cancellation_custody_passed": custody_ok,
        "owner_event_log_reconciled_by_event_schema": owner_log,
        "source_refresh_zero_health_matches_typed_event": zero_health_join,
        "signal_domain_source": {
            "path": "research/doom/doom_signal_value_domain_v1.py",
            "sha256": freeze.get("source_hashes", {}).get(
                "research/doom/doom_signal_value_domain_v1.py"),
            "configured_health_domain": [1, 200],
        },
        "observed_health_zero": {
            "sequence": 325,
            "typed_sample_count": sum(
                row.get("event") == "typed_observation" and
                row.get("signals", {}).get("health", {}).get("status") == "observed" and
                type(row.get("signals", {}).get("health", {}).get("value")) is int and
                row.get("signals", {}).get("health", {}).get("value") == 0
                for row in events),
            "matches_refused_refresh_sequence": source_refresh.get("source_sequence") == 338,
            "refresh_rejection": source_refresh.get("reason"),
        },
        "final_model_decision": {
            "decision_index": 11,
            "prompt_health": 4,
            "prompt_sha256": "8a52024818fab7748e5d4206d73f30689b178b2bcd10184c7c62d70f41dbe681",
            "response": {
                "assessment": "Active; health is critically low at 4 with a close enemy on the right. Execute an immediate emergency retreat while firing and strafe left.",
                "commands": ["retreat_fire:pulse", "strafe_left:pulse"],
                "next_cover_validity": {"critical_health_minimum": 1,
                                         "maximum_health_loss": 3},
                "action_validity": {"critical_health_minimum": 1,
                                    "maximum_health_loss": 3},
            },
            "interpretation": (
                "The model requested emergency retreat at health 4, while both authored "
                "validity bounds allowed health down to 1. The next typed observation "
                "reported health 0. This documents the policy boundary and subsequent "
                "refusal; it does not establish that a stricter threshold would have "
                "prevented death."
            ),
        },
        "decision_report_present": False,
        "source_refresh_failure": {
            "iteration": source_refresh.get("iteration"),
            "source_sequence": source_refresh.get("source_sequence"),
            "reason": source_refresh.get("reason"),
        },
        "controller_failure": {
            "type": (failure or {}).get("primary_error_type"),
            "stage": (failure or {}).get("failed_stage"),
            "cleanup_complete": (failure or {}).get("cleanup_complete"),
            "input_terminals_complete": (failure or {}).get("input_terminals_complete"),
            "input_releases_verified_empty": (failure or {}).get(
                "input_releases_verified_empty"),
            "owner_events_closed": (failure or {}).get("owner_events_closed"),
        },
        "hard_health_guard_count": counts.get("hard_health_guard_exposures", 0),
        "useful_events_during_pending_model": counts.get(
            "useful_events_during_model_wait", 0),
        "recovery_classification": "not_applicable_no_hard_health_guard_and_no_decision_report",
        "custody": {
            "matched_cancellations": custody.get("matched_cancellations"),
            "accounted_cancellations": custody.get("accounted_cancellations"),
            "unaccounted_cancellations": custody.get("unaccounted_cancellations"),
            "per_key_release_transitions": custody.get("per_key_release_transitions"),
            "owner_keyups_matching_key_and_token": custody.get(
                "owner_keyups_matching_key_and_token"),
            "terminals": custody.get("terminals"),
            "terminals_with_verified_empty_release": custody.get(
                "terminals_with_verified_empty_release"),
        },
        "episode": {
            "health_min": min(typed_health) if typed_health else None,
            "health_max": max(typed_health) if typed_health else None,
            "ammo_min": min(typed_ammo) if typed_ammo else None,
            "ammo_max": max(typed_ammo) if typed_ammo else None,
            "kill_count": score.get("kill_count"),
            "death_count": score.get("death_count"),
            "player_dead": score.get("player_dead"),
            "map_exit": score.get("map_exit"),
            "episode_finished": score.get("episode_finished"),
        },
        "runtime": {
            "model_turns_started": counts.get("model_turns_started"),
            "model_turns_completed": counts.get("model_turns_completed"),
            "guest_exit": host.get("guest_exit"),
            "app_server_exit": host.get("app_server_exit"),
            "retry_count": host.get("retry_count"),
            "elapsed_seconds": host.get("elapsed_seconds"),
        },
        "interpretation": (
            "The first A16 outcome is preserved. The final model prompt reported health 4; "
            "its response requested emergency retreat but set both policy bounds to 1, "
            "allowing that policy down to health 1. The next typed sample reported health "
            "0 at sequence 325. A later source refresh at sequence 338 was refused as "
            "outside the configured 1..200 signal domain (source SHA is recorded). This "
            "sequence does not establish that a stricter threshold would have prevented "
            "death. "
            "The frozen audit records 16/16 empty terminal releases and the independent "
            "custody audit accounts for all cancellations and per-key releases, while "
            "the controller's generic top-level cleanup receipt is incomplete. The "
            "event-schema read confirms the owner log's verified close, key-ups, and "
            "empty owner releases; it does not establish hardware key state. No authored-cover "
            "hard-health guard was exposed. Missing report.json prevents action-level "
            "recovery classification; this result is STOP, not a retry or success claim."
        ),
    }
    return result


def main():
    read = lambda name: json.loads((ROOT / name).read_text())
    report_path = ROOT / "episode/report.json"
    failure = read("episode/controller-failure.json")
    refreshes = read("episode/source-refreshes.json")
    events = [json.loads(line) for line in
              (ROOT / "episode/runtime/events.jsonl").read_text().splitlines()
              if line.strip()]
    owner_rows = read("episode/runtime/owner-events.json")
    result = build_result(
        read("FREEZE.json"), read("AUDIT.json"), read("A16_CUSTODY_INDEPENDENT.json"),
        read("HOST.json"), read("episode/runtime/score.json"), failure,
        refreshes[-1] if refreshes else None, events, owner_rows,
        report_present=report_path.is_file())
    inputs = ["FREEZE.json", "HOST.json", "AUDIT.json",
              "A16_CUSTODY_INDEPENDENT.json", "A16_AUDIT_RECONCILIATION_V2_1.json",
              "A16_AUDIT_RECONCILIATION_V3.json", "episode/controller-failure.json",
              "episode/runtime/score.json", "episode/source-refreshes.json",
              "episode/runtime/events.jsonl", "episode/runtime/owner-events.json"]
    result["input_sha256"] = {name: sha256(ROOT / name) for name in inputs}
    (ROOT / "A16_FAILURE_RECONCILIATION.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")
    public = {
        "schema": "map01-v39-live-threat-guard-a16-health-guard-boundary-public-v2",
        "allocation": ALLOC,
        "issue": 59,
        "status": result["status"],
        "source_main_sha": read("FREEZE.json").get("source_commit"),
        "experiment_tree_commit": read("FREEZE.json").get("experiment_tree_commit"),
        "fixture_seed": read("FREEZE.json").get("fixture_seed"),
        "model": read("FREEZE.json").get("runtime", {}).get("model"),
        "effort": read("FREEZE.json").get("runtime", {}).get("effort"),
        "runtime": result["runtime"],
        "episode": result["episode"],
        "hard_health_guard_count": result["hard_health_guard_count"],
        "source_refresh_failure": result["source_refresh_failure"],
        "controller_cleanup_complete": result["controller_failure"]["cleanup_complete"],
        "all_cancellation_and_key_release_custody_reconciled": result[
            "independent_cancellation_custody_passed"],
        "owner_event_log_closed_by_event_schema": result[
            "owner_event_log_reconciled_by_event_schema"]["closed"],
        "report_present": False,
        "scope": (
            "One descriptive live episode. STOP after player death and out-of-domain "
            "health 0; no authored-cover hard guard was exposed, no report was emitted, "
            "and no recovery or task-completion claim is made. The allocation is consumed; "
            "no retry."
        ),
    }
    (ROOT / "A16_RESULT.json").write_text(json.dumps(result, indent=2) + "\n",
                                           encoding="utf-8")
    (ROOT / "A16_RESULT_PUBLIC.json").write_text(json.dumps(public, indent=2) + "\n",
                                                  encoding="utf-8")
    print(json.dumps(public, indent=2))
    return 0 if result["status"] == "STOP" else 1


if __name__ == "__main__":
    raise SystemExit(main())
