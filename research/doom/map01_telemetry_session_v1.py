"""Versioned MAP01 telemetry-only control-loop integration candidate.

This module composes the retained same-thread polling primitive with the
terminal-locked independent progress clock. It deliberately has no controller
scorer callback: privileged scorer state is persisted only to scorer-owned files.
It does not grant input authority and does not alter Executor semantics.
"""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Callable, Iterable

from independent_progress_clock_v2 import ProgressClock, ProgressSample, append_jsonl
from main_thread_scorer_polling_v1 import MainThreadScorerPolling, PollingStats

SAMPLE_RECEIPT_SCHEMA = "map01-independent-scorer-receipt-v1"
SUMMARY_SCHEMA = "map01-telemetry-session-summary-v1"


class Map01IndependentScorer:
    """Read game outcome state on one owner thread and persist it off-channel."""

    def __init__(
        self,
        *,
        game,
        kill_variable,
        death_variable,
        out_dir: Path,
        control_started_ns: int,
        timeout_seconds: int,
        clock_ns: Callable[[], int] = time.perf_counter_ns,
        progress_clock: ProgressClock | None = None,
    ) -> None:
        if type(control_started_ns) is not int or control_started_ns < 0:
            raise ValueError("control_started_ns must be a non-negative integer")
        if type(timeout_seconds) is not int or timeout_seconds <= 5:
            raise ValueError("timeout_seconds must be an integer > 5")
        self.game = game
        self.kill_variable = kill_variable
        self.death_variable = death_variable
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.sample_path = self.out_dir / "independent-scorer-samples.jsonl"
        self.event_path = self.out_dir / "independent-scorer-events.jsonl"
        self.summary_path = self.out_dir / "independent-scorer-summary.json"
        self.control_started_ns = control_started_ns
        self.timeout_seconds = timeout_seconds
        self.clock_ns = clock_ns
        self.progress = progress_clock or ProgressClock()
        self.owner_thread_id = threading.get_ident()
        self.sample_count = 0
        self.event_count = 0

    def _require_owner_thread(self) -> None:
        if threading.get_ident() != self.owner_thread_id:
            raise RuntimeError("DoomGame scorer access moved off owner thread")

    def sample(self) -> ProgressSample:
        self._require_owner_thread()
        finished = bool(self.game.is_episode_finished())
        dead = bool(self.game.is_player_dead())
        deaths = int(self.game.get_game_variable(self.death_variable))
        kills = int(self.game.get_game_variable(self.kill_variable))
        observed_ns = self.clock_ns()
        wall_ns = observed_ns - self.control_started_ns
        map_exit = bool(
            finished
            and not dead
            and wall_ns < (self.timeout_seconds - 5) * 1_000_000_000
        )
        return ProgressSample(
            sample_ns=observed_ns,
            kill_count=kills,
            death_count=deaths,
            episode_finished=finished,
            player_dead=dead,
            map_exit=map_exit,
        )

    def sink(self, receipt: dict) -> None:
        self._require_owner_thread()
        sample = receipt.get("payload")
        if not isinstance(sample, ProgressSample):
            raise TypeError("scorer payload must be ProgressSample")
        record = {
            "schema": SAMPLE_RECEIPT_SCHEMA,
            "scheduled_ns": receipt["scheduled_ns"],
            "sample_started_ns": receipt["sample_started_ns"],
            "sample_finished_ns": receipt["sample_finished_ns"],
            "start_lateness_ns": receipt["start_lateness_ns"],
            "missed_periods_before": receipt["missed_periods_before"],
            "controller_visible": False,
            "sample": sample.as_dict(),
        }
        with self.sample_path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(record, sort_keys=True) + "\n")
        self.sample_count += 1
        events = self.progress.ingest(sample)
        self.event_count += append_jsonl(self.event_path, events)

    def write_summary(self, stats: PollingStats) -> dict:
        self._require_owner_thread()
        summary = {
            "schema": SUMMARY_SCHEMA,
            "owner_thread_id": self.owner_thread_id,
            "polling_owner_thread_id": stats.owner_thread_id,
            "samples": stats.samples,
            "commands": stats.commands,
            "missed_sample_periods": stats.missed_sample_periods,
            "eof": stats.eof,
            "stopped_by_command": stats.stopped_by_command,
            "started_ns": stats.started_ns,
            "ended_ns": stats.ended_ns,
            "scorer_sample_records": self.sample_count,
            "scorer_events": self.event_count,
            "controller_visible": False,
        }
        if summary["owner_thread_id"] != summary["polling_owner_thread_id"]:
            raise RuntimeError("polling and scorer owner thread diverged")
        self.summary_path.write_text(
            json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="\n"
        )
        return summary


def make_v12_command_handler(
    *,
    emit: Callable[[dict], None],
    executor,
    backend,
    on_finish: Callable[[], None],
    on_save_fixture: Callable[[], None] | None = None,
    clock_ns: Callable[[], int] = time.perf_counter_ns,
    recoverable_exceptions: tuple[type[BaseException], ...] = (ValueError, TypeError, KeyError),
) -> Callable[[str], bool]:
    """Preserve the v12 command routing while making line input pollable.

    `finish` and a configured `save_fixture` are terminal loop commands and return
    False to the polling primitive. Rejected commands stay non-terminal, matching
    the historical blocking loop.
    """

    def handle(line: str) -> bool:
        try:
            command = json.loads(line)
            emit({"event": "command", "command": command, "received_ns": clock_ns()})
            op = command["op"]
            if op == "submit":
                executor.submit(
                    command["id"], command["steps"],
                    command["expected_sequence"], command["valid_until_ns"]
                )
            elif op == "cancel":
                executor.cancel(command["id"])
            elif op == "clock":
                emit({"event": "clock", "runtime_ns": clock_ns(), "sequence": backend.sequence})
            elif op == "save_fixture":
                if on_save_fixture is None:
                    raise ValueError("save_fixture is unavailable in measured control")
                on_save_fixture()
                return False
            elif op == "finish":
                on_finish()
                return False
            else:
                raise ValueError("unsupported command")
            return True
        except recoverable_exceptions as error:
            emit({"event": "rejected", "reason": str(error)})
            return True

    return handle


def run_telemetry_control_loop(
    *,
    fd: int,
    scorer: Map01IndependentScorer,
    command_handler: Callable[[str], bool],
    sample_hz: float = 35.0,
    max_samples: int | None = None,
    clock_ns: Callable[[], int] = time.perf_counter_ns,
) -> tuple[PollingStats, dict]:
    polling = MainThreadScorerPolling(sample_hz=sample_hz, clock_ns=clock_ns)
    stats = polling.run(
        fd,
        sample_fn=scorer.sample,
        scorer_sink=scorer.sink,
        command_handler=command_handler,
        max_samples=max_samples,
    )
    summary = scorer.write_summary(stats)
    return stats, summary
