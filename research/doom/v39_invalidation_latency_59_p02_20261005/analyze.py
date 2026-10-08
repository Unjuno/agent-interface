#!/usr/bin/env python3
"""Read-only timing reconstruction from exact retained Git blobs."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FREEZE = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
OUT = ROOT / "RESULT.json"


def frozen_blob(path, receipt):
    raw = subprocess.check_output([
        "git", "show", f"{FREEZE['source_base_commit']}:{path}"
    ])
    if hashlib.sha256(raw).hexdigest() != receipt["sha256"]:
        raise SystemExit("STOP_SOURCE_HASH_MISMATCH:" + path)
    if subprocess.check_output(["git", "hash-object", "--stdin"], input=raw).decode().strip() != receipt["git_blob"]:
        raise SystemExit("STOP_SOURCE_BLOB_MISMATCH:" + path)
    return raw


def runtime_version(commit, path, expected_blob, expected_sha):
    raw = subprocess.check_output(["git", "show", f"{commit}:{path}"])
    blob_id = subprocess.check_output(["git", "hash-object", "--stdin"],
                                      input=raw).decode().strip()
    if blob_id != expected_blob or hashlib.sha256(raw).hexdigest() != expected_sha:
        raise SystemExit("STOP_RUNTIME_SOURCE_MISMATCH:" + path)
    return raw


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUT,
                        help="write-once result path; default is RESULT.json beside this script")
    args = parser.parse_args()
    output = args.output
    if output.exists():
        raise SystemExit("STOP_OUTPUT_EXISTS")
    if hashlib.sha256(Path(__file__).read_bytes()).hexdigest() != FREEZE["analysis_sha256"]:
        raise SystemExit("STOP_ANALYSIS_HASH_MISMATCH")
    try:
        subprocess.check_call([
            "git", "merge-base", "--is-ancestor", FREEZE["source_base_commit"],
            FREEZE["observed_main_recheck_commit"],
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        raise SystemExit("STOP_RUN_SOURCE_NOT_ANCESTOR_OF_RECHECKED_MAIN")
    documents = {
        path: frozen_blob(path, receipt)
        for path, receipt in FREEZE["source_blobs"].items()
    }
    report_path, events_path = list(FREEZE["source_blobs"])[:2]
    report = json.loads(documents[report_path])
    events = [json.loads(line) for line in documents[events_path].splitlines() if line]
    runtime_comparison = {}
    for path, ids in FREEZE["runtime_source_comparison"].items():
        run_raw = runtime_version(FREEZE["source_base_commit"], path,
                                  ids["run_blob"], ids["run_sha256"])
        main_raw = runtime_version(FREEZE["observed_main_recheck_commit"], path,
                                   ids["current_main_blob"], ids["current_main_sha256"])
        runtime_comparison[path] = {
            "run_blob": ids["run_blob"], "current_main_blob": ids["current_main_blob"],
            "same_source": run_raw == main_raw,
        }
    chosen = [row for row in report["decisions"]
              if row.get("iteration") == FREEZE["selection"]["decision_iteration"]]
    if len(chosen) != 1:
        raise SystemExit("STOP_DECISION_NOT_UNIQUE")
    decision = chosen[0]
    selection = FREEZE["selection"]
    cover_actions = [item.get("action") for item in (decision.get("cover_policy") or [])]
    invalidation = decision.get("final_action_admission", {}).get("policy_invalidation") or {}
    outcome = invalidation.get("outcome") or {}
    if selection["required_cover_action"] not in cover_actions:
        raise SystemExit("STOP_REQUIRED_COVER_MISSING")
    if (outcome.get("status") != selection["required_invalidation"] or
            outcome.get("signal_id") != selection["required_signal_id"]):
        raise SystemExit("STOP_REQUIRED_INVALIDATION_MISSING")

    sequence = selection["typed_observation_sequence"]
    typed = [row for row in events
             if row.get("event") == "typed_observation" and row.get("sequence") == sequence]
    if len(typed) != 1:
        raise SystemExit("STOP_TRIGGER_OBSERVATION_NOT_UNIQUE")
    observation = typed[0]
    model_start = decision["controller_model_started_ns"]
    model_end = decision["controller_model_ended_ns"]
    planner_terminal = decision["planner_terminal_observed_ns"]
    capture = observation["capture_ns"]
    typed_ready = observation["typed_ready_ns"]
    monitor_received = invalidation["monitor_received_ns"]
    signal_extracted = invalidation["signal_extracted_ns"]
    outcome_evaluated = invalidation["outcome_evaluated_ns"]
    in_wait = [row for row in events
               if row.get("event") == "typed_observation" and
               model_start <= row.get("capture_ns", -1) <= capture]
    prior = [row for row in in_wait if row.get("capture_ns", 0) < capture]
    if not prior:
        raise SystemExit("STOP_PRIOR_OBSERVATION_MISSING")
    prior = max(prior, key=lambda row: row["capture_ns"])
    prior_health = prior.get("signals", {}).get("health", {})
    if (prior_health.get("status") != "observed" or
            type(prior_health.get("value")) is not int or
            prior_health["value"] < outcome.get("hard_minimum")):
        raise SystemExit("STOP_PRIOR_HEALTH_NOT_AT_OR_ABOVE_FLOOR")
    earlier_observed = [row for row in in_wait if row.get("capture_ns", 0) < capture
                        if row.get("signals", {}).get("health", {}).get("status") == "observed"
                        and type(row.get("signals", {}).get("health", {}).get("value")) is int]
    if any(row["signals"]["health"]["value"] < outcome.get("hard_minimum")
           for row in earlier_observed):
        raise SystemExit("STOP_EARLIER_BELOW_FLOOR_SAMPLE")

    visual_frames = []
    for visual_sequence in selection["reviewed_observation_sequences"]:
        typed_rows = [row for row in events
                      if row.get("event") == "typed_observation" and
                      row.get("sequence") == visual_sequence]
        full_rows = [row for row in events
                     if row.get("event") == "observation" and
                     row.get("sequence") == visual_sequence]
        suffix = f"runtime/{visual_sequence:03}.png"
        image_path = next((path for path in FREEZE["source_blobs"]
                           if path.endswith(suffix)), None)
        if len(typed_rows) != 1 or len(full_rows) != 1 or image_path is None:
            raise SystemExit("STOP_VISUAL_FRAME_BINDING_MISSING")
        typed_row, full_row = typed_rows[0], full_rows[0]
        if (full_row.get("exact") is not True or
                typed_row.get("frame_rgb_sha256") != full_row.get("frame_rgb_sha256") or
                not full_row.get("image", "").endswith(suffix)):
            raise SystemExit("STOP_VISUAL_FRAME_EPOCH_MISMATCH")
        visual_frames.append({
            "sequence": visual_sequence,
            "capture_ns": typed_row.get("capture_ns"),
            "image_git_blob": FREEZE["source_blobs"][image_path]["git_blob"],
            "image_sha256": FREEZE["source_blobs"][image_path]["sha256"],
            "full_observation_exact": full_row.get("exact"),
            "typed_full_rgb_hash_match": True,
            "health": typed_row.get("signals", {}).get("health", {}).get("value"),
            "ammo": typed_row.get("signals", {}).get("ammo", {}).get("value"),
            "in_model_wait": model_start <= typed_row.get("capture_ns", 0) <= model_end,
            "capture_after_model_start_ms": round(
                (typed_row.get("capture_ns", 0) - model_start) / 1e6, 6)
                if typed_row.get("capture_ns", 0) >= model_start else None,
        })

    if not (model_start <= capture <= typed_ready <= monitor_received <=
            signal_extracted <= outcome_evaluated < planner_terminal <= model_end):
        raise SystemExit("STOP_EVENT_ORDER_MISMATCH")
    if decision.get("planner_turn_status") != "interrupted":
        raise SystemExit("STOP_PLANNER_NOT_INTERRUPTED")
    if decision.get("planner_answer_eligible") is not False:
        raise SystemExit("STOP_PLANNER_ANSWER_ELIGIBLE")
    if decision.get("planner_cancellation_requested") is not True:
        raise SystemExit("STOP_PLANNER_CANCELLATION_MISSING")
    if decision.get("cover_terminal_before_plan") is not True:
        raise SystemExit("STOP_COVER_TERMINAL_ORDER_MISSING")

    health = observation.get("signals", {}).get("health", {})
    ammo = observation.get("signals", {}).get("ammo", {})
    if health.get("value") != outcome.get("current_value"):
        raise SystemExit("STOP_HEALTH_VALUE_MISMATCH")
    cover_id = selection["cover_program_id"]
    terminal_rows = [row for row in events
                     if row.get("event") == "terminal" and row.get("id") == cover_id]
    cancel_rows = [row for row in events
                   if row.get("event") == "command" and
                   row.get("command", {}).get("op") == "cancel" and
                   row.get("command", {}).get("id") == cover_id]
    if len(terminal_rows) != 1 or len(cancel_rows) != 1:
        raise SystemExit("STOP_COVER_CANCEL_TERMINAL_NOT_UNIQUE")
    cover_terminal = terminal_rows[0]
    release = cover_terminal.get("release", {})
    if (cover_terminal.get("status") != "cancelled" or
            release.get("verified") is not True or release.get("keys_down") != [] or
            release.get("buttons_down") != []):
        raise SystemExit("STOP_EMPTY_RELEASE_NOT_VERIFIED")
    scores = [row for row in events if row.get("event") == "post_control_score"]
    result = {
        "schema": "issue59-v39-visible-threat-invalidation-posthoc-result-v2",
        "classification": "posthoc single-run mechanism observation; not preregistered",
        "source_base_commit": FREEZE["source_base_commit"],
        "source_hashes_verified": True,
        "live_allocations_added": 0,
        "source_runtime_code_matches_current_main": runtime_comparison,
        "changed_runtime_source_paths": sorted(
            path for path, row in runtime_comparison.items() if not row["same_source"]),
        "historical_monitor_mode": decision.get("cover_validity_admission", {}).get(
            "monitor_mode"),
        "current_main_paired_fire_cover_guard_present": all(
            marker in subprocess.check_output([
                "git", "show", f"{FREEZE['observed_main_recheck_commit']}:research/doom/map01_overlap_controller_v39.py"
            ]).decode("utf-8") for marker in
            ("class DoomCoverSignalPairMonitor", "def cover_requires_ammo", "requires_ammo=cover_requires_ammo")),
        "decision_iteration": decision["iteration"],
        "cover_actions": cover_actions,
        "model_wait_ns": model_end - model_start,
        "model_wait_ms": round((model_end - model_start) / 1e6, 6),
        "source_health": outcome.get("source_value"),
        "hard_minimum": outcome.get("hard_minimum"),
        "trigger_observation": {
            "sequence": sequence,
            "capture_ns": capture,
            "typed_ready_ns": typed_ready,
            "artifact_published": observation.get("artifact_published"),
            "frame_rgb_sha256": observation.get("frame_rgb_sha256"),
            "health": health.get("value"),
            "ammo": ammo.get("value"),
        },
        "previous_typed_observation": {
            "sequence": prior.get("sequence"),
            "capture_ns": prior.get("capture_ns"),
            "health": prior_health.get("value"),
            "ammo": prior.get("signals", {}).get("ammo", {}).get("value"),
        },
        "invalidation": {
            "status": outcome.get("status"),
            "reason": outcome.get("reason"),
            "monitor_received_ns": monitor_received,
            "signal_extracted_ns": signal_extracted,
            "outcome_evaluated_ns": outcome_evaluated,
        },
        "planner_terminal": {
            "status": decision.get("planner_turn_status"),
            "answer_eligible": decision.get("planner_answer_eligible"),
            "cancellation_requested": decision.get("planner_cancellation_requested"),
            "terminal_observed_ns": planner_terminal,
        },
        "cover_terminal_before_plan": decision.get("cover_terminal_before_plan"),
        "cover_cancellation": {
            "program_id": cover_id,
            "cancel_command_received_ns": cancel_rows[0].get("received_ns"),
            "terminal_ns": cover_terminal.get("terminal_ns"),
            "release_verified_ns": release.get("verified_ns"),
            "release_verified": release.get("verified"),
            "keys_down": release.get("keys_down"),
            "buttons_down": release.get("buttons_down"),
            "planner_terminal_observed_ns": planner_terminal,
        },
        "episode_score": ({key: scores[0].get(key) for key in
                            ("kill_count", "death_count", "map_exit", "player_dead")}
                           if len(scores) == 1 else None),
        "visual_frame_bindings": visual_frames,
        "visual_review": {
            "method": "single-analyst visual inspection of pinned full observation PNGs",
            "visible_hostile_by_sequence": {"166": False, "200": True,
                                             "217": True, "218": True},
            "threat_appears_in_view_during_wait": True,
            "independent_visual_review": False,
        },
        "timing_ms": {
            "capture_after_model_start": round((capture - model_start) / 1e6, 6),
            "last_at_or_above_floor_to_below_floor_capture_interval": round(
                (capture - prior["capture_ns"]) / 1e6, 6),
            "capture_to_monitor_received": round((monitor_received - capture) / 1e6, 6),
            "typed_ready_to_monitor_received": round((monitor_received - typed_ready) / 1e6, 6),
            "monitor_received_to_evaluation": round((outcome_evaluated - monitor_received) / 1e6, 6),
            "evaluation_before_planner_terminal": round((planner_terminal - outcome_evaluated) / 1e6, 6),
            "planner_terminal_before_model_wait_end": round((model_end - planner_terminal) / 1e6, 6),
        },
        "trigger_frame_visibility_verified": True,
        "task_effect_or_survival_claim": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
