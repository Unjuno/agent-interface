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


def _windows_api():
    """Load the small Win32 handle API surface used for redirected stdin."""
    import ctypes
    import ctypes.wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    wintypes = ctypes.wintypes
    kernel32.GetFileType.argtypes = [wintypes.HANDLE]
    kernel32.GetFileType.restype = wintypes.DWORD
    kernel32.PeekNamedPipe.argtypes = [
        wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p,
        ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p,
    ]
    kernel32.PeekNamedPipe.restype = wintypes.BOOL
    kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel32.WaitForSingleObject.restype = wintypes.DWORD
    kernel32.SetLastError.argtypes = [wintypes.DWORD]
    kernel32.GetLastError.restype = wintypes.DWORD
    return kernel32, wintypes


def _wait_windows_readable(fd: int, timeout_s: float) -> bool:
    """Wait for CRT stdin handles without passing pipes to Winsock select()."""
    import ctypes
    import msvcrt
    import time

    kernel32, wintypes = _windows_api()
    handle = wintypes.HANDLE(msvcrt.get_osfhandle(fd))
    kernel32.SetLastError(0)
    file_type = int(kernel32.GetFileType(handle))

    if file_type == 0:  # FILE_TYPE_UNKNOWN
        error = int(kernel32.GetLastError())
        if error:
            raise OSError(error, "GetFileType failed")
        raise OSError("stdin handle has an unknown Windows file type")

    if file_type == 1:  # FILE_TYPE_DISK
        return True

    if file_type == 2:  # FILE_TYPE_CHAR, commonly a console input handle
        milliseconds = max(0, min(0xFFFFFFFE, int(timeout_s * 1000 + 0.999)))
        result = int(kernel32.WaitForSingleObject(handle, milliseconds))
        if result == 0:  # WAIT_OBJECT_0
            return True
        if result == 0x102:  # WAIT_TIMEOUT
            return False
        if result == 0xFFFFFFFF:  # WAIT_FAILED
            error = int(kernel32.GetLastError())
            raise OSError(error, "WaitForSingleObject failed")
        raise OSError(f"unexpected WaitForSingleObject result: {result}")

    if file_type == 3:  # FILE_TYPE_PIPE, including CRT anonymous stdin pipes
        deadline = time.monotonic() + max(0.0, timeout_s)
        while True:
            available = wintypes.DWORD()
            ok = kernel32.PeekNamedPipe(
                handle, None, 0, None, ctypes.byref(available), None)
            if ok:
                if available.value:
                    return True
            else:
                error = int(kernel32.GetLastError())
                if error == 109:  # ERROR_BROKEN_PIPE: let os.read() observe EOF
                    return True
                raise OSError(error, "PeekNamedPipe failed")

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return False
            time.sleep(min(0.001, remaining))

    raise OSError(f"unsupported Windows stdin handle type: {file_type}")


def _wait_readable(fd: int, timeout_s: float) -> bool:
    if os.name == "nt":
        return _wait_windows_readable(fd, timeout_s)
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

            # Service ready input between samples, including sustained overrun.
            now = self.clock_ns()
            timeout_s = max(0, (next_sample_ns - now) / 1_000_000_000)
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
        # Include skips a next due sample would account, without emitting it.
        # Keep the current due slot, as the ordinary elapsed-period rule does.
        missed_periods += max(0, (ended_ns - next_sample_ns) // self.period_ns)
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
