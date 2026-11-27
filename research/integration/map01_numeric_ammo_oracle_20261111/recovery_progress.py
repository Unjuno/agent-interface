"""Bounded wait for the post-recovery producer progress receipt.

The public action can become terminal as soon as release recovery is confirmed,
while the dispatch worker is still persisting its best-effort producer action
counter. Callers that need this diagnostic must poll for it separately and
must keep a missing counter distinct from zero.
"""

from __future__ import annotations

import time
from typing import Callable


def _sleep_ns(duration_ns: int) -> None:
    time.sleep(duration_ns / 1_000_000_000)


def wait_for_recovery_progress(poll: Callable[[], dict], *,
                               timeout_ns: int = 1_500_000_000,
                               interval_ns: int = 50_000_000,
                               clock_ns: Callable[[], int] = time.monotonic_ns,
                               sleep_ns: Callable[[int], None] = _sleep_ns):
    """Return the latest terminal action and whether its counter was retained.

    A confirmed recovery without a counter remains a valid recovery receipt;
    the status is ``missing`` after the bounded wait, never inferred as zero.
    """
    if type(timeout_ns) is not int or timeout_ns < 0:
        raise ValueError("timeout_ns must be a nonnegative integer")
    if type(interval_ns) is not int or interval_ns <= 0:
        raise ValueError("interval_ns must be a positive integer")
    if not callable(poll) or not callable(clock_ns) or not callable(sleep_ns):
        raise ValueError("poll, clock_ns, and sleep_ns must be callable")

    deadline_ns = clock_ns() + timeout_ns
    latest = None
    history = []
    while True:
        latest = poll()
        action = latest.get("action") if type(latest) is dict else None
        now_ns = clock_ns()
        if type(action) is dict:
            status = action.get("status")
            count = action.get("program_actions_lower_bound")
            history.append({"observed_monotonic_ns": now_ns,
                            "action_status": status,
                            "program_actions_lower_bound": count
                            if type(count) is int and count >= 0 else None})
            if status == "recovered":
                if type(count) is int and count >= 0:
                    return latest, "observed", history
            elif status in ("completed", "unknown"):
                return latest, "not_applicable", history

        if now_ns >= deadline_ns:
            terminal = (type(action) is dict and action.get("status") == "recovered")
            return latest, "missing" if terminal else "not_terminal", history
        sleep_ns(min(interval_ns, deadline_ns - now_ns))
