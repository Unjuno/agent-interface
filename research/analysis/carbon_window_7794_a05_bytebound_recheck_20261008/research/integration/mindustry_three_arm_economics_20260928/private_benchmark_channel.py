"""Host-side file channel for private Mindustry score/reset coordination.

The directory must be private to the benchmark runner and is never sent over
the controller socket. This module has no game or model dependency.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import time

from private_reset_audit import (geometry_receipt, reset_failure_receipt,
                                 reset_witness_receipt, score_receipt,
                                 verify_reset_witness)


TASKS = ("A1", "A2", "A3", "B1", "B2", "B3")


class PrivateProtocolStop(RuntimeError):
    """Fail-closed terminal result for a private lifecycle transport issue."""


class PrivateBenchmarkChannel:
    def __init__(self, directory: Path, timeout_s: float = 30.0,
                 poll_s: float = 0.02):
        self.root = Path(directory).resolve(strict=True)
        if not self.root.is_dir() or Path(directory).is_symlink():
            raise ValueError("private benchmark control directory required")
        if type(timeout_s) not in (int, float) or timeout_s <= 0:
            raise ValueError("positive private protocol timeout required")
        if type(poll_s) not in (int, float) or poll_s <= 0:
            raise ValueError("positive private protocol poll interval required")
        if any(self.root.iterdir()):
            raise ValueError("private benchmark directory must be fresh and empty")
        self.timeout_s = float(timeout_s)
        self.poll_s = float(poll_s)
        self.epoch = 0
        self.phase = "spawn"
        self._before: dict | None = None
        self._after: dict | None = None
        self._task_started_ns: dict[int, int] = {}
        self._score_times_by_task: dict[str, int] = {}
        self._reset_request_ns: int | None = None
        self._reset_events: dict[str, dict] = {}
        self._transition_events: list[dict] = []
        self._last_event_ns = 0

    def _event_time_ns(self) -> int:
        """Return a strictly increasing host monotonic event timestamp."""
        now = time.monotonic_ns()
        self._last_event_ns = max(now, self._last_event_ns + 1)
        return self._last_event_ns

    def _path(self, filename: str) -> Path:
        if not filename or Path(filename).name != filename:
            raise ValueError("private protocol marker must be a basename")
        return self.root / filename

    def _write_once(self, filename: str, content: str) -> None:
        path = self._path(filename)
        try:
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError as error:
            raise PrivateProtocolStop("private marker already exists: " + filename) from error
        try:
            os.write(descriptor, content.encode("utf-8"))
        finally:
            os.close(descriptor)

    def _wait_file(self, filename: str, error_filename: str | None = None) -> Path:
        deadline = time.monotonic() + self.timeout_s
        path = self._path(filename)
        error_path = self._path(error_filename) if error_filename else None
        while time.monotonic() < deadline:
            if error_path is not None and error_path.exists():
                detail = error_path.read_text(encoding="utf-8", errors="replace")
                self.phase = "stopped"
                raise PrivateProtocolStop("private mod refused: " + detail)
            if path.is_file():
                return path
            time.sleep(min(self.poll_s, max(0.0, deadline - time.monotonic())))
        self.phase = "stopped"
        raise PrivateProtocolStop("private protocol timeout waiting for " + filename)

    def _snapshot(self, filename: str) -> dict:
        try:
            value = json.loads(self._path(filename).read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            self.phase = "stopped"
            raise PrivateProtocolStop("invalid private snapshot: " + filename) from error
        if type(value) is not dict:
            self.phase = "stopped"
            raise PrivateProtocolStop("private snapshot must be an object: " + filename)
        return value

    def await_initial_ready(self) -> dict:
        if self.phase != "spawn" or self.epoch != 0:
            raise PrivateProtocolStop("initial readiness can be consumed once")
        self._wait_file("ready-1.ack", "ready-1.error")
        self._before = self._snapshot("before-1.json")
        self._task_started_ns[1] = self._event_time_ns()
        self.epoch, self.phase = 1, "ready"
        return self._before

    def request_checkpoint(self) -> dict:
        if self.phase != "ready" or self.epoch < 1:
            raise PrivateProtocolStop("checkpoint requires the current ready task")
        self._write_once(f"checkpoint-{self.epoch}.request", "checkpoint\n")
        self._wait_file(f"checkpoint-{self.epoch}.ack",
                        f"checkpoint-{self.epoch}.error")
        self._after = self._snapshot(f"after-{self.epoch}.json")
        self.phase = "checkpointed"
        return self._after

    def complete_task(self, task_id: str, evaluation: dict) -> dict | None:
        if self.phase != "checkpointed" or self.epoch < 1:
            raise PrivateProtocolStop("task completion requires one checkpoint")
        if task_id != TASKS[self.epoch - 1]:
            raise PrivateProtocolStop("task id differs from private protocol epoch")
        score_checked_ns = self._event_time_ns()
        try:
            score = score_receipt(task_id, evaluation)
        except ValueError as error:
            self._write_once(f"score-fail-{self.epoch}.receipt",
                             f"independent score failed for {task_id}\n")
            self.phase = "stopped"
            raise PrivateProtocolStop("negative or incomplete task score; reset forbidden") from error

        self._write_once(score["filename"], score["content"])
        self._score_times_by_task[task_id] = score_checked_ns
        self._reset_request_ns = self._event_time_ns()
        self._write_once(f"reset-{self.epoch}.request", "reset\n")
        self._wait_file(f"reset-{self.epoch}.ack", f"reset-{self.epoch}.error")
        reset = self._snapshot(f"reset-{self.epoch}.json")
        audit = verify_reset_witness(self._before, reset)
        if audit["verified"]:
            witness = reset_witness_receipt(task_id, audit)
            self._write_once(witness["filename"], witness["content"])
        else:
            failure = reset_failure_receipt(task_id, audit)
            self._write_once(failure["filename"], failure["content"])
            self.phase = "stopped"
            raise PrivateProtocolStop("reset audit failed; next task forbidden")

        witness_ns = self._event_time_ns()
        self._reset_events[task_id] = {
            "request_ns": self._reset_request_ns,
            "witness_ns": witness_ns,
            "receipt_id": witness["filename"],
            "before": self._before,
            "after": reset,
        }

        if self.epoch == 3:
            self._wait_file("geometry-4.request", "geometry-4.error")
            self.phase = "await_geometry"
            self._before = reset
            return reset
        if self.epoch == 6:
            self.phase = "complete"
            self._before = reset
            return reset
        next_epoch = self.epoch + 1
        self._wait_file(f"ready-{next_epoch}.ack", f"ready-{next_epoch}.error")
        self._task_started_ns[next_epoch] = self._event_time_ns()
        self.epoch, self.phase, self._before = next_epoch, "ready", reset
        return reset

    def release_geometry_transition(self, before_binding: dict,
                                    after_binding: dict) -> None:
        if self.phase != "await_geometry" or self.epoch != 3:
            raise PrivateProtocolStop("A-to-B layout release requires A3 reset audit")
        try:
            receipt = geometry_receipt(before_binding, after_binding)
        except ValueError as error:
            self._write_once("geometry-4.error", str(error) + "\n")
            self.phase = "stopped"
            raise PrivateProtocolStop("A-to-B geometry witness failed") from error
        transition_ns = self._event_time_ns()
        self._transition_events.append({
            "arm": None,
            "after_task": "A3",
            "before_task": "B1",
            "from_layout": "A",
            "to_layout": "B",
            "at_ns": transition_ns,
            "before_binding": before_binding,
            "after_binding": after_binding,
        })
        self._write_once(receipt["filename"], receipt["content"])
        self._wait_file("ready-4.ack", "ready-4.error")
        self._task_started_ns[4] = self._event_time_ns()
        self.epoch, self.phase = 4, "ready"

    def raw_lifecycle_events(self, arm: str) -> dict:
        """Return immutable-schema private reset and A3→B1 event rows.

        These rows are runner-side audit material; callers must keep them out
        of the controller socket and merge each reset event into its matching
        task's raw record before v2 audit.
        """
        if arm not in {"plain", "ephemeral", "persistent"}:
            raise ValueError("unknown preregistered arm")
        resets = {}
        for task_id, event in self._reset_events.items():
            resets[task_id] = {**event}
        transitions = [{**event, "arm": arm} for event in self._transition_events]
        return {"task_started_ns": dict(self._task_started_ns),
                "score_checked_ns": dict(self._score_times_by_task),
                "reset_events": resets,
                "transition_events": transitions}
