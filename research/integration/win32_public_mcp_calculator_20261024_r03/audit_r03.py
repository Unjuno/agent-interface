"""Reconcile the immutable R03 MCP and follow-up receipts; no UI actions."""
from __future__ import annotations
import hashlib, json
from pathlib import Path

PACKET = Path(__file__).resolve().parent
RUN = PACKET / "run"
FOLLOW = RUN / "post-observation-followup"
def read(path):
    return json.loads(path.read_text(encoding="utf-8"))
res = read(RUN / "result.json")
pre = read(RUN / "preflight.json")
paused = read(RUN / "paused-before-dispatch.json")
obs = paused["steps"][0]["parsed"]["receipt"]["source"]["raw_report"]
validation = read(RUN / "validation-0.json")["parsed"]
dispatch = read(RUN / "dispatch-0.json")["parsed"]
final = read(RUN / "results-4.json")["parsed"]
action = final["action"]
custody = action["completion_custody"]
program = read(RUN / "program.json")["program"]
post = read(FOLLOW / "observation.json")
postraw = post["parsed"]["receipt"]["source"]["raw_report"]
close = read(RUN / "close-0.json")["parsed"]
post_image = Path(postraw["observation"]["artifact"]["path"])
checks = {
    "frozen_conditions_hash_matches_preflight": pre["conditions_sha256"] == hashlib.sha256((PACKET / "conditions.json").read_bytes()).hexdigest(),
    "attempt_and_source_match": res["attempt_id"] == pre["attempt_id"] and res["source_commit"] == pre["source_commit"],
    "pre_observation_generation_matched": obs["target_generation_consistency"] == "matched" and obs["observation"]["native_window_id"] == 55117672,
    "static_validation_passed": validation["status"] == "valid" and validation["static_valid"] is True,
    "one_dispatch_call_bound": dispatch["status"] == "pending" and res["call_id"] == dispatch["call_id"],
    "retained_action_completed": action["status"] == "completed" and action["operation_id"] == custody["operation_id"],
    "neutral_release_receipt_verified": action["release_confirmed"] is True and custody["completion_release_receipt"]["verified"] is True and custody["completion_readback"]["neutral"] is True and all(not custody["completion_release_receipt"][k] for k in ("keys_down", "keys_unknown", "buttons_down", "buttons_unknown")),
    "producer_exit_precedes_readback": custody["producer_exit_code"] == 0 and custody["completion_readback"]["producer_exit_confirmed_ns"] <= custody["completion_readback"]["observed_monotonic_ns"],
    "generation_matches_action_and_followup": action["target_generation"] == obs["target_generation"] == postraw["target_generation"] and postraw["target_generation_consistency"] == "matched",
    "followup_public_observation_is_read_only": not post["isError"] and postraw["input_dispatched"] is False and postraw["side_effect_authority"] is False and postraw["observation"]["frame"] == "screen_physical_px" and postraw["observation"]["region"] == [40, 32, 336, 541] and postraw["observation"]["native_window_id"] == 55117672,
    "followup_dimensions_and_raw_image_hash_match": (postraw["observation"]["width"], postraw["observation"]["height"]) == (336, 541) and hashlib.sha256(post_image.read_bytes()).hexdigest() == postraw["observation"]["artifact"]["sha256"],
    "followup_within_frozen_90s_from_pre_dispatch_clock": 0 <= postraw["observation"]["capture_started_ns"] - read(RUN / "clock-0.json")["parsed"]["monotonic_ns"] <= 90_000_000_000,
    "followup_is_late_beyond_frozen_90s_bound": postraw["observation"]["capture_started_ns"] - read(RUN / "clock-0.json")["parsed"]["monotonic_ns"] > 90_000_000_000,
    "server_closed_without_unresolved_calls": close["status"] == "closed" and close["session"]["unresolved_call_ids"] == [],
    "runtime_task_success_remains_null": action.get("task_success") is None and final.get("task_success") is None,
    "strict_runner_status_preserved_as_fail_or_unknown": res["status"] == "FAIL_OR_UNKNOWN" and "generation, or release evidence incomplete" in res.get("stop_reason", ""),
    "runner_skipped_in_session_post_action_observation": not any(s.get("name") == "post_action_observation" for s in res["steps"]),
    "program_id_matches_attempt": program["program_id"].startswith("win32-public-mcp-calculator-20261024-r03"),
    "conditions_record_r02_to_r03_harness_change": "changed_factor_from_r02" in read(PACKET / "conditions.json"),
}
report = {
    "schema": "win32-public-mcp-calculator-r03-reconciliation-v1",
    "attempt_id": res["attempt_id"],
    "checks": checks,
    "passed": sum(bool(v) for v in checks.values()),
    "total": len(checks),
    "strict_runner_status": res["status"],
    "scoped_disposition": "normal completion release confirmed; strict integrated attempt remains FAIL_OR_UNKNOWN because the planned post-action observation was skipped and the later follow-up exceeded the frozen 90-second bound",
    "visual_assessment": "Manual inspection of the hash-bound late follow-up screenshot shows Calculator Standard mode, expression 314 + 728 =, and display 1,042. It was captured 93.094 seconds after the pre-dispatch clock, 3.094 seconds beyond the frozen 90-second limit. It does not qualify as R03 task-effect evidence and does not set task_success.",
    "task_success": None,
    "timing_ns": {
        "action_start": action["result"]["execution"]["started_ns"],
        "pre_dispatch_clock": read(RUN / "clock-0.json")["parsed"]["monotonic_ns"],
        "neutral_completion_readback": custody["completion_readback"]["observed_monotonic_ns"],
        "followup_capture_start": postraw["observation"]["capture_started_ns"],
        "action_start_to_followup": postraw["observation"]["capture_started_ns"] - custody["completion_release_receipt"]["monotonic_ns"],
        "neutral_readback_to_followup": postraw["observation"]["capture_started_ns"] - custody["completion_readback"]["observed_monotonic_ns"],
        "pre_dispatch_clock_to_followup": postraw["observation"]["capture_started_ns"] - read(RUN / "clock-0.json")["parsed"]["monotonic_ns"],
        "late_by_ns": postraw["observation"]["capture_started_ns"] - read(RUN / "clock-0.json")["parsed"]["monotonic_ns"] - 90_000_000_000,
    },
    "known_harness_defects": [
        "interface_results nests target_generation under action.target_generation; runner searched the top-level object and skipped its planned same-session observation.",
        "The frozen program_id incorrectly retains an R01 label.",
    ],
    "protocol_deviation": "A separate read-only sky screenshot was viewed before the public-MCP follow-up. It is not used by these checks or as the formal visual artifact.",
}
(RUN / "audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"passed": report["passed"], "total": report["total"], "failed": [k for k,v in checks.items() if not v], "action_status": action["status"], "release_confirmed": action["release_confirmed"], "task_success": report["task_success"]}, ensure_ascii=False))
