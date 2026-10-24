"""Additive, post-hoc endpoint calculations for the frozen R44 packet."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def ms(start: int, end: int) -> float:
    return (end - start) / 1_000_000


raw = load(ROOT / "raw.json")
task = load(ROOT / "task_raw.json")
events = [json.loads(line) for line in (ROOT / "run" / "cancellation_call_trace.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
verify = load(ROOT / "run" / "phase2_task" / "verify-task-0.json")
oracle_ns = verify["task_effect"]["receipt"]["observed_monotonic_ns"]
server_report = load(ROOT / "run" / "phase2_task" / "server-receipts" / task["call_id"] / "report.json")
execution = server_report["supervision"]["action"]["result"]["execution"]

cancel_return = raw["public_cancel_attempt"]["returned_monotonic_ns"]
q_up_return = next(
    event["monotonic_ns"] for event in events
    if event.get("event") == "sendinput_return" and event.get("input_type") == 1
    and event.get("vk") == 81 and event.get("key_up") is True
)
hook = raw["hook_trace_after_recovery"]
capture = raw["public_observation"]["raw_report"]["observation"]
observation_started = raw["public_observation"]["started_monotonic_ns"]
observation_returned = raw["public_observation"]["returned_monotonic_ns"]
artifact_timing = capture["artifact"]["timing_ns"]

metrics = {
    "observation_call_ms": ms(observation_started, observation_returned),
    "capture_ms": ms(capture["capture_started_ns"], capture["capture_ended_ns"]),
    "capture_start_to_observation_return_ms": ms(capture["capture_started_ns"], observation_returned),
    "artifact_pipeline_ms": ms(artifact_timing["started"], artifact_timing["written"]),
    "cancel_call_ms": ms(raw["public_cancel_attempt"]["started_monotonic_ns"], cancel_return),
    "cancel_response_to_recovery_q_up_sendinput_return_ms": ms(cancel_return, q_up_return),
    "callback_hold_after_cancel_response_ms": ms(cancel_return, hook["callback_return_ns"]),
    "phase2_execution_ms": ms(execution["started_ns"], execution["ended_ns"]),
    "phase2_execution_end_to_oracle_observation_ms": ms(execution["ended_ns"], oracle_ns),
    "phase2_execution_start_to_oracle_observation_ms": ms(execution["started_ns"], oracle_ns),
}

print(json.dumps({"schema": "r44-posthoc-timing-v1", "source_commit": raw["source_commit"], "clock": raw["clock"]["clock"], "metrics_ms": metrics}, indent=2))
