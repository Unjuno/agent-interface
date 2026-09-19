"""Readiness-driven command input with same-thread periodic scorer sampling.

This module is a construction primitive, not a MAP01 session integration.  It
keeps command dispatch and scorer sampling on the caller thread, so a future
adapter can keep all DoomGame access on the thread that owns that object.
Scorer payloads are delivered only to an explicit scorer sink callback; there is
no controller/event emitter in this module.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
import select
import time
from typing import Callable, Any


WaitReadable = Callable[[int, float], bool]
ClockNs = Callable[[], int]
ReadFn = Callable[[int, int], bytes]


def _wait_readable(fd: int, timeout_s: float) -> bool:
    ready, _, _ = select.select([fd], [], [], timeout_s)
    return bool(ready)


@dataclass(frozen=True)
class PollingStats:
    owner_thread_id: int
    samples: int
    commands: int
    missed_sample_periods: int
    eof: bool
    stopped_by_command: bool
    started_ns: int
    ended_ns: int


class MainThreadScorerPolling:
    """Schedule scorer reads without a background DoomGame polling thread.

    `sample_fn` and `command_handler` are always invoked synchronously by
    `run()`.  When the loop is late by multiple sample periods it emits exactly
    one current sample and records the skipped periods; it never fabricates
    catch-up samples with synthetic timestamps.
    """

    def __init__(
        self,
        *,
        sample_hz: float,
        clock_ns: ClockNs = time.perf_counter_ns,
        wait_readable: WaitReadable = _wait_readable,
        read_fn: ReadFn = os.read,
        max_buffer_bytes: int = 1 << 20,
    ) -> None:
        if not isinstance(sample_hz, (int, float)) or isinstance(sample_hz, bool) or sample_hz <= 0:
            raise ValueError("sample_hz must be positive")
        self.period_ns = max(1, round(1_000_000_000 / float(sample_hz)))
        if max_buffer_bytes < 1:
            raise ValueError("max_buffer_bytes must be positive")
        self.clock_ns = clock_ns
        self.wait_readable = wait_readable
        self.read_fn = read_fn
        self.max_buffer_bytes = int(max_buffer_bytes)

    def run(
        self,
        fd: int,
        *,
        sample_fn: Callable[[], Any],
        scorer_sink: Callable[[dict], None],
        command_handler: Callable[[str], bool | None],
        max_samples: int | None = None,
        read_size: int = 65536,
    ) -> PollingStats:
        if max_samples is not None and max_samples < 1:
            raise ValueError("max_samples must be >= 1")
        if read_size < 1:
            raise ValueError("read_size must be positive")

        import threading

        owner_thread_id = threading.get_ident()
        started_ns = self.clock_ns()
        next_sample_ns = started_ns
        buffer = bytearray()
        sample_count = 0
        command_count = 0
        missed_periods = 0
        eof = False
        stopped_by_command = False

        def sample_once(scheduled_ns: int, skipped: int) -> None:
            nonlocal sample_count
            sample_started_ns = self.clock_ns()
            payload = sample_fn()
            sample_finished_ns = self.clock_ns()
            scorer_sink({
                "scheduled_ns": scheduled_ns,
                "sample_started_ns": sample_started_ns,
                "sample_finished_ns": sample_finished_ns,
                "start_lateness_ns": max(0, sample_started_ns - scheduled_ns),
                "missed_periods_before": skipped,
                "payload": payload,
            })
            sample_count += 1

        while True:
            now = self.clock_ns()
            if now >= next_sample_ns:
                elapsed_periods = ((now - next_sample_ns) // self.period_ns) + 1
                skipped = max(0, elapsed_periods - 1)
                missed_periods += skipped
                scheduled_ns = next_sample_ns
                next_sample_ns += elapsed_periods * self.period_ns
                sample_once(scheduled_ns, skipped)
                if max_samples is not None and sample_count >= max_samples:
                    break
                continue

            timeout_s = (next_sample_ns - now) / 1_000_000_000
            if not self.wait_readable(fd, timeout_s):
                continue

            chunk = self.read_fn(fd, read_size)
            if chunk == b"":
                eof = True
                if buffer:
                    raise ValueError("unterminated command at EOF")
                break
            buffer.extend(chunk)
            if len(buffer) > self.max_buffer_bytes:
                raise ValueError("command buffer exceeded max_buffer_bytes")

            while True:
                newline = buffer.find(b"\n")
                if newline < 0:
                    break
                raw = bytes(buffer[:newline])
                del buffer[: newline + 1]
                if not raw:
                    continue
                line = raw.decode("utf-8", errors="strict")
                command_count += 1
                keep_running = command_handler(line)
                if keep_running is False:
                    stopped_by_command = True
                    break
            if stopped_by_command:
                break

        ended_ns = self.clock_ns()
        return PollingStats(
            owner_thread_id=owner_thread_id,
            samples=sample_count,
            commands=command_count,
            missed_sample_periods=missed_periods,
            eof=eof,
            stopped_by_command=stopped_by_command,
            started_ns=started_ns,
            ended_ns=ended_ns,
        )
