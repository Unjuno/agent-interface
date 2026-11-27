"""Bounded high-frequency key-state sampling around a lease deadline.

Windows Python may implement monotonic_ns with a coarse tick clock. Keep that
clock for the lease comparison, and use QueryPerformanceCounter via
perf_counter_ns for ordering and elapsed sampling intervals.
"""
from __future__ import annotations

import threading
import time


class KeyStateSampler:
    """Sample one injected key-state reader on a dedicated bounded thread."""

    def __init__(self, read_down, *, interval_ns=2_000_000, max_samples=5000,
                 clock_ns=time.perf_counter_ns,
                 lease_clock_ns=time.monotonic_ns):
        if not callable(read_down):
            raise ValueError("key-state reader required")
        if type(interval_ns) is not int or not 0 < interval_ns <= 20_000_000:
            raise ValueError("sample interval must be in 1..20 ms")
        if type(max_samples) is not int or not 2 <= max_samples <= 100_000:
            raise ValueError("sample limit must be in 2..100000")
        if not callable(clock_ns) or not callable(lease_clock_ns):
            raise ValueError("high-resolution and lease clocks required")
        self._reader = read_down
        self._interval_ns = interval_ns
        self._max_samples = max_samples
        self._clock_ns = clock_ns
        self._lease_clock_ns = lease_clock_ns
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._samples = []
        self._error = None
        self._limit_reached = False
        self._thread = None

    def start(self):
        if self._thread is not None:
            raise RuntimeError("key-state sampler already started")
        self._thread = threading.Thread(target=self._run,
            name="win32-key-state-sampler", daemon=True)
        self._thread.start()
        return self

    def _run(self):
        next_sample_ns = self._clock_ns()
        while not self._stop.is_set():
            now_ns = self._clock_ns()
            if now_ns < next_sample_ns:
                # A short busy wait avoids Windows' coarse default wait timer.
                continue
            lease_before_ns = self._lease_clock_ns()
            sample_start_ns = self._clock_ns()
            try:
                down = self._reader()
                if type(down) is not bool:
                    raise ValueError("key-state reader must return bool")
                error_code = None
            except Exception as error:
                down = None
                error_code = type(error).__name__[:64]
                self._error = error_code
            sample_end_ns = self._clock_ns()
            lease_after_ns = self._lease_clock_ns()
            with self._lock:
                if len(self._samples) >= self._max_samples:
                    self._limit_reached = True
                    self._stop.set()
                    return
                self._samples.append({
                    "monotonic_before_ns": lease_before_ns,
                    "monotonic_after_ns": lease_after_ns,
                    "perf_counter_start_ns": sample_start_ns,
                    "perf_counter_end_ns": sample_end_ns,
                    "w_key_down": down,
                    "error_type": error_code})
            if error_code is not None:
                return
            next_sample_ns += self._interval_ns
            if next_sample_ns <= sample_end_ns:
                next_sample_ns = sample_end_ns + self._interval_ns

    def stop(self, *, join_timeout_s=1.0):
        if self._thread is None:
            raise RuntimeError("key-state sampler was not started")
        if type(join_timeout_s) not in (int, float) or not 0 < join_timeout_s <= 5:
            raise ValueError("join timeout must be in (0, 5] seconds")
        self._stop.set()
        self._thread.join(join_timeout_s)
        if self._thread.is_alive():
            raise TimeoutError("key-state sampler did not stop within bound")
        with self._lock:
            samples = [dict(row) for row in self._samples]
        gaps = [b["perf_counter_start_ns"] - a["perf_counter_start_ns"]
            for a, b in zip(samples, samples[1:])]
        return {"clock": "time.perf_counter_ns",
            "lease_clock": "time.monotonic_ns",
            "requested_interval_ns": self._interval_ns,
            "sample_count": len(samples),
            "max_observed_gap_ns": max(gaps, default=None),
            "sample_limit_reached": self._limit_reached,
            "read_error_type": self._error, "samples": samples}


def audit_expiry_key_release(samples, deadline_ns, *, max_bracket_ns=20_000_000):
    """Require a conservative QPC bracket around pre-down/post-up reads."""
    if type(deadline_ns) is not int or deadline_ns <= 0:
        raise ValueError("lease deadline must be a positive monotonic timestamp")
    if type(max_bracket_ns) is not int or not 0 < max_bracket_ns <= 100_000_000:
        raise ValueError("boundary bracket must be in 1..100 ms")
    if not isinstance(samples, (list, tuple)):
        raise ValueError("samples must be a sequence")
    valid = []
    previous_start_ns = 0
    previous_lease_end_ns = 0
    malformed = False
    for row in samples:
        if type(row) is not dict:
            malformed = True
            continue
        lease_before = row.get("monotonic_before_ns")
        lease_after = row.get("monotonic_after_ns")
        precise_start = row.get("perf_counter_start_ns")
        precise_end = row.get("perf_counter_end_ns")
        value = row.get("w_key_down")
        if (type(lease_before) is not int or type(lease_after) is not int
                or lease_before > lease_after or lease_before < previous_lease_end_ns
                or type(precise_start) is not int or type(precise_end) is not int
                or precise_start <= previous_start_ns or precise_end < precise_start
                or (value is not None and type(value) is not bool)):
            malformed = True
            continue
        previous_start_ns = precise_start
        previous_lease_end_ns = lease_after
        valid.append(row)
    before = [row for row in valid
        if row["monotonic_after_ns"] < deadline_ns]
    # Equality does not prove the read began after expiry. Coarse monotonic
    # clocks can report the deadline for a read that straddles the boundary.
    after = [row for row in valid
        if row["monotonic_before_ns"] > deadline_ns]
    last_before = before[-1] if before else None
    first_after = after[0] if after else None
    post_deadline_up = [row for row in after
        if row.get("w_key_down") is False]
    first_up = post_deadline_up[0] if post_deadline_up else None
    bracket_gap = (first_up["perf_counter_start_ns"]
        - last_before["perf_counter_end_ns"]
        if last_before is not None and first_up is not None else None)
    # GetAsyncKeyState's observation instant is only known to be inside
    # each timed read. The inner gap excludes that uncertainty and cannot
    # establish the upper bound on the down-to-up transition interval.
    bracket_outer = (first_up["perf_counter_end_ns"]
        - last_before["perf_counter_start_ns"]
        if last_before is not None and first_up is not None else None)
    error_between = any(row.get("error_type") is not None for row in valid
        if last_before is not None and first_up is not None
        and last_before["perf_counter_start_ns"]
        <= row["perf_counter_start_ns"]
        <= first_up["perf_counter_start_ns"])
    unknown_between = any(row.get("w_key_down") is None for row in valid
        if last_before is not None and first_up is not None
        and last_before["perf_counter_start_ns"]
        <= row["perf_counter_start_ns"]
        <= first_up["perf_counter_start_ns"])
    verified = (not malformed and not error_between
        and not unknown_between
        and last_before is not None and first_after is not None
        and first_up is not None
        and last_before.get("w_key_down") is True
        and 0 <= bracket_gap
        and 0 <= bracket_outer <= max_bracket_ns)
    return {"status": "verified" if verified else "not_verified",
        "deadline_monotonic_ns": deadline_ns,
        "last_down_read_fully_before_deadline": last_before,
        "first_sample_fully_after_deadline": first_after,
        "first_up_read_fully_after_deadline": first_up,
        "qpc_bracket_gap_ns": bracket_gap,
        "qpc_bracket_outer_ns": bracket_outer,
        "post_deadline_down_duration_ns": (
            first_up["perf_counter_start_ns"]
            - first_after["perf_counter_start_ns"]
            if first_after is not None and first_up is not None else None),
        "max_bracket_ns": max_bracket_ns,
        "malformed_samples": malformed,
        "read_error_between": error_between,
        "unknown_state_between": unknown_between}
