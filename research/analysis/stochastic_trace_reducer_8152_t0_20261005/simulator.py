"""Candidate-side finite stochastic replay simulator."""
from __future__ import annotations

import hashlib
import math
from spec import (
    BASE_TRACE, COMPETING_RATE, DEPENDENCIES, EXIT_CODE, MANDATORY,
    STRATUM_COLD_RATE, STRATUM_WARM_RATE, TARGET,
)


def legal(events: tuple[str, ...] | list[str]) -> bool:
    present = set(events)
    if len(present) != len(events) or not present <= set(BASE_TRACE):
        return False
    if tuple(events) != tuple(e for e in BASE_TRACE if e in present):
        return False
    if not set(MANDATORY) <= present:
        return False
    return all(set(parents) <= present for event, parents in DEPENDENCIES.items() if event in present)


def _u(seed: int, salt: str) -> float:
    raw = hashlib.sha256(f"{seed}|{salt}".encode()).digest()[:8]
    return int.from_bytes(raw, "big") / 2**64


def replay(events: tuple[str, ...] | list[str], seed: int, stratum: int) -> dict:
    ordered = tuple(events)
    if not legal(ordered):
        return {"fingerprint": "INVALID_AUTHORITY_OR_DEPENDENCY", "exit_code": 17}
    if "competing_fault" in ordered and _u(seed, "competitor") < COMPETING_RATE:
        return {"fingerprint": "COMPETING_WIDGET_CRASH", "exit_code": EXIT_CODE}
    core = {"observation", "commit", "timing_guard"} <= set(ordered)
    if core:
        rates = STRATUM_WARM_RATE if "warmup" in ordered else STRATUM_COLD_RATE
        if _u(seed, "target") < rates[stratum]:
            return {"fingerprint": TARGET, "exit_code": EXIT_CODE}
    return {"fingerprint": "NO_FAILURE", "exit_code": 0}


def one_sided_lower(successes: int, n: int, alpha: float) -> float:
    """Clopper-Pearson lower bound by binomial-tail inversion."""
    if n <= 0 or successes <= 0:
        return 0.0

    def tail(p: float) -> float:
        return sum(math.comb(n, j) * p**j * (1-p)**(n-j) for j in range(successes, n+1))

    lo, hi = 0.0, successes / n
    for _ in range(64):
        mid = (lo + hi) / 2
        if tail(mid) > alpha:
            hi = mid
        else:
            lo = mid
    return lo


def one_sided_upper(successes: int, n: int, alpha: float) -> float:
    """Clopper-Pearson upper bound by binomial lower-tail inversion."""
    if n <= 0 or successes >= n:
        return 1.0

    def tail(p: float) -> float:
        return sum(math.comb(n, j) * p**j * (1-p)**(n-j) for j in range(0, successes+1))

    lo, hi = successes / n, 1.0
    for _ in range(64):
        mid = (lo + hi) / 2
        if tail(mid) > alpha:
            lo = mid
        else:
            hi = mid
    return hi


def trial(events: tuple[str, ...], seed: int, stratum: int) -> dict:
    outcome = replay(events, seed, stratum)
    return {"seed": seed, "stratum": stratum, "events": list(events), **outcome}


def reduced(events: tuple[str, ...], group: tuple[str, ...]) -> tuple[str, ...]:
    remove = set(group)
    return tuple(e for e in events if e not in remove)
