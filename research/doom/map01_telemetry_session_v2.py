"""MAP01 telemetry-session v2: explicit post-finish scorer closure.

V1 adds periodic same-thread independent scoring. V2 closes the finish boundary:
a successful ``finish`` command is followed by exactly one scorer-only sample on
the same caller thread. The sample is persisted separately and can be checked
strictly against the historical ``post_control_score`` payload. No scorer state
is emitted to the controller channel by this module.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import time
from typing import Callable

from main_thread_scorer_polling_v1 import MainThreadScorerPolling

FINAL_RECEIPT_SCHEMA = "map01-independent-scorer-final-v2"
SUMMARY_SCHEMA = "map01-telemetry-session-summary-v2"


@dataclass
class CommandStopState:
    reason: str | None = None


def make_v12_command_handler_v2(
    *,
    emit: Callable[[dict], None],
    executor,
    backend,
    on_finish: Callable[[], None],
    stop_state: CommandStopState,
    on_save_fixture: Callable[[], None] | None = None,
    clock_ns: Callable[[], int] = time.perf_counter_ns,
    recoverable_exceptions: tuple[type[BaseException], ...] = (ValueError, TypeError, KeyError),
) -> Callable[[str], bool]:
    """V12-compatible routing with an explicit reason for terminal loop stops."""

    def handle(line: str) -> bool:
        try:
            command = json.loads(line)
            emit({"event": "command", "command": command, "received_ns": clock_ns()})
            op = command["op"]
            if op == "submit":
                executor.submit(
                    command["id"], command["steps"],
                    command["expected_sequence"], command["valid_until_ns"],
                )
            elif op == "cancel":
                executor.cancel(command["id"])
            elif op == "clock":
                emit({"event": "clock", "runtime_ns": clock_ns(), "sequence": backend.sequence})
            elif op == "save_fixture":
                if on_save_fixture is None:
                    raise ValueError("save_fixture is unavailable in measured control")
                on_save_fixture()
                stop_state.reason = "save_fixture"
                return False
            elif op == "finish":
                on_finish()
                stop_state.reason = "finish"
                return False
            else:
                raise ValueError("unsupported command")
            return True
        except recoverable_exceptions as error:
            emit({"event": "rejected", "reason": str(error)})
            return True

    return handle


def validate_terminal_score_agreement(sample, score: dict) -> dict:
    """Fail closed unless the independent final sample equals post_control_score."""
    if not isinstance(score, dict):
        raise TypeError("score must be dict")
    expected = {
        "map_exit": sample.map_exit,
        "episode_finished": sample.episode_finished,
        "player_dead": sample.player_dead,
        "death_count": sample.death_count,
        "kill_count": sample.kill_count,
    }
    mismatches = {}
    for key, value in expected.items():
        if key not in score:
            mismatches[key] = {"expected": value, "actual": "<missing>"}
        elif type(score[key]) is not type(value) or score[key] != value:
            mismatches[key] = {"expected": value, "actual": score[key]}
    if mismatches:
        raise ValueError(
            "terminal scorer disagreement: " + json.dumps(mismatches, sort_keys=True)
        )
    return {"agreement": True, "fields": sorted(expected)}


def _sample_after_finish(*, scorer, clock_ns: Callable[[], int]) -> tuple[dict, object]:
    scheduled_ns = clock_ns()
    sample_started_ns = clock_ns()
    payload = scorer.sample()
    sample_finished_ns = clock_ns()
    receipt = {
        "scheduled_ns": scheduled_ns,
        "sample_started_ns": sample_started_ns,
        "sample_finished_ns": sample_finished_ns,
        "start_lateness_ns": max(0, sample_started_ns - scheduled_ns),
        "missed_periods_before": 0,
        "payload": payload,
    }
    scorer.sink(receipt)
    record = {
        "schema": FINAL_RECEIPT_SCHEMA,
        "controller_visible": False,
        "receipt_kind": "post_finish_final",
        "scheduled_ns": scheduled_ns,
        "sample_started_ns": sample_started_ns,
        "sample_finished_ns": sample_finished_ns,
        "sample": payload.as_dict(),
    }
    final_path = Path(scorer.out_dir) / "independent-scorer-final.json"
    final_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
    return record, payload


def run_telemetry_control_loop_v2(
    *,
    fd: int,
    scorer,
    command_handler: Callable[[str], bool],
    stop_state: CommandStopState,
    sample_hz: float = 35.0,
    max_samples: int | None = None,
    clock_ns: Callable[[], int] = time.perf_counter_ns,
    terminal_score_fn: Callable[[], dict] | None = None,
):
    """Run periodic scoring and close successful ``finish`` with one final sample."""
    polling = MainThreadScorerPolling(sample_hz=sample_hz, clock_ns=clock_ns)
    stats = polling.run(
        fd,
        sample_fn=scorer.sample,
        scorer_sink=scorer.sink,
        command_handler=command_handler,
        max_samples=max_samples,
    )
    final_record = None
    agreement = None
    if stats.stopped_by_command and stop_state.reason == "finish":
        final_record, payload = _sample_after_finish(scorer=scorer, clock_ns=clock_ns)
        if terminal_score_fn is not None:
            agreement = validate_terminal_score_agreement(payload, terminal_score_fn())

    base_summary = scorer.write_summary(stats)
    summary = dict(base_summary)
    summary.update({
        "schema": SUMMARY_SCHEMA,
        "stop_reason": stop_state.reason,
        "post_finish_final_sample": final_record is not None,
        "post_finish_sample_ns": None if final_record is None else final_record["sample"]["sample_ns"],
        "terminal_score_agreement": agreement,
    })
    scorer.summary_path.write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    return stats, summary, final_record
