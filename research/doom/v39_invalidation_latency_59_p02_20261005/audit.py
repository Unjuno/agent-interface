#!/usr/bin/env python3
"""Independent audit of the retained visible-threat invalidation result."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FREEZE = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))


def source_blob(path, receipt):
    raw = subprocess.check_output([
        "git", "show", f"{FREEZE['source_base_commit']}:{path}"
    ])
    valid = (hashlib.sha256(raw).hexdigest() == receipt["sha256"] and
             subprocess.check_output(["git", "hash-object", "--stdin"], input=raw)
             .decode().strip() == receipt["git_blob"])
    if not valid:
        raise SystemExit("STOP_SOURCE_IDENTITY_MISMATCH:" + path)
    return raw


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, default=ROOT / "RESULT.json",
                        help="candidate result path; default is RESULT.json beside this script")
    parser.add_argument("--output", type=Path, default=ROOT / "AUDIT.json",
                        help="write-once audit path; default is AUDIT.json beside this script")
    args = parser.parse_args()
    if not args.result.exists():
        raise SystemExit("STOP_RESULT_MISSING")
    result = json.loads(args.result.read_text(encoding="utf-8"))
    if hashlib.sha256(Path(__file__).read_bytes()).hexdigest() != FREEZE["audit_sha256"]:
        raise SystemExit("STOP_AUDIT_HASH_MISMATCH")
    raw = {path: source_blob(path, receipt)
           for path, receipt in FREEZE["source_blobs"].items()}
    report_path, events_path = list(FREEZE["source_blobs"])[:2]
    report = json.loads(raw[report_path])
    events = [json.loads(line) for line in raw[events_path].splitlines() if line]
    try:
        subprocess.check_call([
            "git", "merge-base", "--is-ancestor", FREEZE["source_base_commit"],
            FREEZE["observed_main_recheck_commit"],
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        source_ancestor = True
    except subprocess.CalledProcessError:
        source_ancestor = False
    runtime_matches = {}
    runtime_ids_valid = {}
    for path, ids in FREEZE["runtime_source_comparison"].items():
        run_bytes = subprocess.check_output([
            "git", "show", f"{FREEZE['source_base_commit']}:{path}"
        ])
        main_bytes = subprocess.check_output([
            "git", "show", f"{FREEZE['observed_main_recheck_commit']}:{path}"
        ])
        run_id = subprocess.check_output(["git", "hash-object", "--stdin"],
                                         input=run_bytes).decode().strip()
        main_id = subprocess.check_output(["git", "hash-object", "--stdin"],
                                          input=main_bytes).decode().strip()
        runtime_ids_valid[path] = (run_id == ids["run_blob"] and
                                   main_id == ids["current_main_blob"] and
                                   hashlib.sha256(run_bytes).hexdigest() == ids["run_sha256"] and
                                   hashlib.sha256(main_bytes).hexdigest() == ids["current_main_sha256"])
        runtime_matches[path] = run_bytes == main_bytes
    selection = FREEZE["selection"]
    decisions = [row for row in report["decisions"]
                 if row.get("iteration") == selection["decision_iteration"]]
    checks = {}
    checks["frozen_source_identities"] = True
    checks["run_base_is_ancestor_of_main_recheck"] = source_ancestor
    checks["runtime_source_identities_verified"] = all(runtime_ids_valid.values())
    checks["runtime_source_comparison_recomputed"] = bool(
        all(result.get("source_runtime_code_matches_current_main", {}).get(path, {}).get(
            "same_source") == same for path, same in runtime_matches.items()) and
        result.get("changed_runtime_source_paths") == sorted(
            path for path, same in runtime_matches.items() if not same))
    current_controller = subprocess.check_output([
        "git", "show", f"{FREEZE['observed_main_recheck_commit']}:research/doom/map01_overlap_controller_v39.py"
    ]).decode("utf-8")
    checks["current_main_paired_fire_guard_source_check"] = bool(
        all(marker in current_controller for marker in
            ("class DoomCoverSignalPairMonitor", "def cover_requires_ammo",
             "requires_ammo=cover_requires_ammo")) and
        result.get("current_main_paired_fire_cover_guard_present") is True)
    checks["single_selected_decision"] = len(decisions) == 1
    if len(decisions) != 1:
        decisions = [{}]
    decision = decisions[0]
    start = decision.get("controller_model_started_ns", 0)
    end = decision.get("controller_model_ended_ns", 0)
    terminal = decision.get("planner_terminal_observed_ns", 0)
    invalidation = (decision.get("final_action_admission", {})
                    .get("policy_invalidation") or {})
    outcome = invalidation.get("outcome") or {}
    sequence = selection["typed_observation_sequence"]
    observations = [row for row in events
                    if row.get("event") == "typed_observation" and
                    row.get("sequence") == sequence]
    checks["one_trigger_observation"] = len(observations) == 1
    observation = observations[0] if len(observations) == 1 else {}
    capture = observation.get("capture_ns", 0)
    earlier = [row for row in events
               if row.get("event") == "typed_observation" and
               start <= row.get("capture_ns", -1) < capture]
    prior = max(earlier, key=lambda row: row["capture_ns"]) if earlier else {}
    earlier_values = [row.get("signals", {}).get("health", {}).get("value")
                      for row in earlier
                      if row.get("signals", {}).get("health", {}).get("status") == "observed" and
                      type(row.get("signals", {}).get("health", {}).get("value")) is int]
    monitor = invalidation.get("monitor_received_ns", 0)
    evaluated = invalidation.get("outcome_evaluated_ns", 0)
    checks["typed_capture_inside_wait"] = bool(start <= capture <= end)
    checks["observed_floor_crossing_interval"] = bool(
        prior.get("sequence") == result.get("previous_typed_observation", {}).get("sequence") and
        prior.get("signals", {}).get("health", {}).get("value") ==
        result.get("previous_typed_observation", {}).get("health") and
        prior.get("signals", {}).get("health", {}).get("value") ==
        outcome.get("hard_minimum") and
        all(value >= outcome.get("hard_minimum") for value in earlier_values) and
        observation.get("signals", {}).get("health", {}).get("value") <
        outcome.get("hard_minimum") and
        result.get("timing_ms", {}).get(
            "last_at_or_above_floor_to_below_floor_capture_interval") ==
        round((capture - prior.get("capture_ns", 0)) / 1e6, 6))
    checks["health_hard_invalidation_matches_trigger"] = bool(
        outcome.get("status") == "HARD_INVALIDATED" and
        outcome.get("signal_id") == "health" and
        outcome.get("reason") == "below_hard_minimum" and
        outcome.get("current_value") ==
        observation.get("signals", {}).get("health", {}).get("value") and
        type(outcome.get("hard_minimum")) is int and
        outcome.get("current_value") < outcome.get("hard_minimum"))
    checks["evaluation_precedes_planner_terminal"] = bool(
        evaluated < terminal <= end and decision.get("planner_turn_status") == "interrupted" and
        decision.get("planner_answer_eligible") is False and
        decision.get("planner_cancellation_requested") is True)
    checks["cover_closed_before_plan"] = bool(
        selection["required_cover_action"] in
        [item.get("action") for item in (decision.get("cover_policy") or [])] and
        decision.get("cover_terminal_before_plan") is True and
        decision.get("plan_terminal") == "not_admitted")
    visual_ok = True
    frame_event_rows = []
    for sequence in selection["reviewed_observation_sequences"]:
        typed_rows = [row for row in events if row.get("event") == "typed_observation"
                      and row.get("sequence") == sequence]
        full_rows = [row for row in events if row.get("event") == "observation"
                     and row.get("sequence") == sequence]
        image_path = next((path for path in FREEZE["source_blobs"]
                           if path.endswith(f"runtime/{sequence:03}.png")), None)
        visual_ok = visual_ok and len(typed_rows) == 1 and len(full_rows) == 1 and image_path is not None
        if len(typed_rows) == 1 and len(full_rows) == 1 and image_path is not None:
            visual_ok = visual_ok and full_rows[0].get("exact") is True
            visual_ok = visual_ok and typed_rows[0].get("frame_rgb_sha256") == full_rows[0].get("frame_rgb_sha256")
            visual_ok = visual_ok and full_rows[0].get("image", "").endswith(f"runtime/{sequence:03}.png")
            frame_event_rows.append((sequence, typed_rows[0], full_rows[0]))
    result_frames = {row.get("sequence"): row
                     for row in result.get("visual_frame_bindings", [])}
    visual_values_match = True
    for sequence, typed_row, full_row in frame_event_rows:
        result_frame = result_frames.get(sequence, {})
        capture_ns = typed_row.get("capture_ns", 0)
        visual_values_match = visual_values_match and (
            result_frame.get("capture_ns") == capture_ns and
            result_frame.get("full_observation_exact") is True and
            result_frame.get("typed_full_rgb_hash_match") is True and
            result_frame.get("health") == typed_row.get("signals", {}).get("health", {}).get("value") and
            result_frame.get("ammo") == typed_row.get("signals", {}).get("ammo", {}).get("value") and
            result_frame.get("in_model_wait") is (start <= capture_ns <= end))
    checks["reviewed_frames_bound_to_exact_observations"] = bool(
        visual_ok and visual_values_match and
        len(frame_event_rows) == len(selection["reviewed_observation_sequences"]) and
        result.get("visual_review", {}).get("independent_visual_review") is False)

    cover_id = selection["cover_program_id"]
    cover_terminals = [row for row in events if row.get("event") == "terminal"
                       and row.get("id") == cover_id]
    cancel_commands = [row for row in events if row.get("event") == "command"
                       and row.get("command", {}).get("op") == "cancel"
                       and row.get("command", {}).get("id") == cover_id]
    cancel_received = cancel_commands[0].get("received_ns") if len(cancel_commands) == 1 else 0
    cover_terminal_ns = cover_terminals[0].get("terminal_ns") if len(cover_terminals) == 1 else 0
    release_verified_ns = (cover_terminals[0].get("release", {}).get("verified_ns")
                           if len(cover_terminals) == 1 else 0)
    checks["cancelled_cover_empty_release"] = bool(
        len(cover_terminals) == 1 and len(cancel_commands) == 1 and
        cover_terminals[0].get("status") == "cancelled" and
        cover_terminals[0].get("release", {}).get("verified") is True and
        cover_terminals[0].get("release", {}).get("keys_down") == [] and
        cover_terminals[0].get("release", {}).get("buttons_down") == [] and
        result.get("cover_cancellation", {}).get("release_verified") is True and
        result.get("cover_cancellation", {}).get("keys_down") == [] and
        result.get("cover_cancellation", {}).get("buttons_down") == [] and
        evaluated < cancel_received < release_verified_ns < cover_terminal_ns < terminal)
    score_rows = [row for row in events if row.get("event") == "post_control_score"]
    checks["episode_score_matches_retained_terminal"] = bool(
        len(score_rows) == 1 and result.get("episode_score") == {
            key: score_rows[0].get(key) for key in
            ("kill_count", "death_count", "map_exit", "player_dead")})
    checks["scope_remains_posthoc"] = bool(
        result.get("classification", "").startswith("posthoc") and
        result.get("live_allocations_added") == 0 and
        result.get("trigger_frame_visibility_verified") is True and
        result.get("visual_review", {}).get("independent_visual_review") is False and
        result.get("task_effect_or_survival_claim") is False and
        result.get("changed_runtime_source_paths") and
        result.get("historical_monitor_mode") == "authored_policy_guard")

    expected_margin_ms = round((terminal - evaluated) / 1e6, 6)
    expected_wait_ms = round((end - start) / 1e6, 6)
    checks["reported_timing_recomputed"] = bool(
        result.get("timing_ms", {}).get("evaluation_before_planner_terminal") ==
        expected_margin_ms and result.get("model_wait_ms") == expected_wait_ms and
        result.get("timing_ms", {}).get("capture_after_model_start") ==
        round((capture - start) / 1e6, 6) and
        result.get("timing_ms", {}).get("capture_to_monitor_received") ==
        round((monitor - capture) / 1e6, 6) and
        result.get("timing_ms", {}).get("typed_ready_to_monitor_received") ==
        round((monitor - observation.get("typed_ready_ns", 0)) / 1e6, 6) and
        result.get("previous_typed_observation", {}).get("ammo") ==
        prior.get("signals", {}).get("ammo", {}).get("value"))

    audit = {"schema": "issue59-v39-visible-threat-invalidation-posthoc-audit-v2",
             "checks": checks, "passed": sum(checks.values()),
             "total": len(checks),
             "disposition": "PASS" if all(checks.values()) else "AUDIT_FAILED"}
    output = args.output
    if output.exists():
        raise SystemExit("STOP_OUTPUT_EXISTS")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(audit, sort_keys=True, separators=(",", ":")) + "\n",
                      encoding="utf-8")
    print(json.dumps(audit, sort_keys=True))


if __name__ == "__main__":
    main()
