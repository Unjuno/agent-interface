"""Candidate-side helpers for the frozen Issue #8493 finite fixture."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
FREEZE_PATH = PACKAGE / "FREEZE.json"
FIXTURE_PATH = PACKAGE / "fixture.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def uniform(seed: int, salt: str) -> float:
    raw = hashlib.sha256(f"{seed}|{salt}".encode("ascii")).digest()[:8]
    return int.from_bytes(raw, "big") / 2**64


def legal(trace: list[str], fixture: dict) -> bool:
    present = set(trace)
    allowed = set(fixture["base_trace"])
    if len(trace) != len(present) or not present <= allowed:
        return False
    if trace != [event for event in fixture["base_trace"] if event in present]:
        return False
    if not set(fixture["mandatory_events"]) <= present:
        return False
    return all(set(parents) <= present for event, parents in fixture["dependencies"].items() if event in present)


def response(trace: list[str], seed: int, window: dict, fixture: dict) -> dict:
    if not legal(trace, fixture):
        return {"fingerprint": "INVALID_AUTHORITY_OR_DEPENDENCY", "exit_code": fixture["same_exit_code"]}
    if "competing_fault" in trace and uniform(seed, fixture["competing_salt"]) < fixture["competing_rate"]:
        return {"fingerprint": fixture["competing_fingerprint"], "exit_code": fixture["same_exit_code"]}
    rate = window["base_rate"] if "warmup" in trace else window["reduced_rate"]
    if uniform(seed, fixture["target_salt"]) < rate:
        return {"fingerprint": fixture["target_fingerprint"], "exit_code": fixture["same_exit_code"]}
    return {"fingerprint": fixture["no_failure_fingerprint"], "exit_code": 0}


def paired_counts(rows: list[dict]) -> dict:
    gains = losses = base_successes = reduced_successes = 0
    competitors = 0
    for row in rows:
        base = row["base"]["fingerprint"] == "TARGET_STALE_GUARD"
        reduced = row["reduced"]["fingerprint"] == "TARGET_STALE_GUARD"
        base_successes += int(base)
        reduced_successes += int(reduced)
        gains += int(reduced and not base)
        losses += int(base and not reduced)
        competitors += int(row["base"]["fingerprint"] == "COMPETING_WIDGET_CRASH")
    return {"n": len(rows), "base_target": base_successes, "reduced_target": reduced_successes,
            "gains": gains, "losses": losses, "competitor_rows": competitors}


def cp_lower(k: int, n: int, alpha: float) -> float:
    if n <= 0 or k <= 0:
        return 0.0
    lo, hi = 0.0, k / n
    for _ in range(64):
        p = (lo + hi) / 2
        if _tail_ge(k, n, p) > alpha:
            hi = p
        else:
            lo = p
    return lo


def cp_upper(k: int, n: int, alpha: float) -> float:
    if n <= 0 or k >= n:
        return 1.0
    lo, hi = k / n, 1.0
    for _ in range(64):
        p = (lo + hi) / 2
        if _tail_le(k, n, p) > alpha:
            lo = p
        else:
            hi = p
    return hi


def _pmf(k: int, n: int, p: float) -> float:
    if p <= 0.0:
        return 1.0 if k == 0 else 0.0
    if p >= 1.0:
        return 1.0 if k == n else 0.0
    from math import comb
    return comb(n, k) * p**k * (1.0 - p)**(n-k)


def _tail_ge(k: int, n: int, p: float) -> float:
    if p <= 0.0:
        return 1.0 if k <= 0 else 0.0
    if p >= 1.0:
        return 1.0
    term = _pmf(k, n, p)
    total = term
    for j in range(k, n):
        term *= ((n-j)/(j+1)) * (p/(1.0-p))
        total += term
    return min(1.0, total)


def _tail_le(k: int, n: int, p: float) -> float:
    if p <= 0.0:
        return 1.0
    if p >= 1.0:
        return 1.0 if k >= n else 0.0
    term = _pmf(k, n, p)
    total = term
    for j in range(k, 0, -1):
        term *= (j/(n-j+1)) * ((1.0-p)/p)
        total += term
    return min(1.0, total)


def risk_difference_interval(counts: dict, alpha: float) -> dict:
    n = counts["n"]
    # For paired binary outcomes, delta = P(gain) - P(loss). Union bounds
    # over the two exact binomial intervals yield a conservative interval.
    lower = cp_lower(counts["gains"], n, alpha) - cp_upper(counts["losses"], n, alpha)
    upper = cp_upper(counts["gains"], n, alpha) - cp_lower(counts["losses"], n, alpha)
    return {"delta": (counts["reduced_target"] - counts["base_target"]) / n if n else None,
            "lower": lower, "upper": upper}


def decision(interval: dict, margin: float) -> str:
    if interval["lower"] >= -margin:
        return "PASS_NONINFERIOR"
    if interval["upper"] < -margin:
        return "FAIL_NONINFERIORITY"
    return "UNKNOWN_INTERVAL_OVERLAPS_MARGIN"


def alpha_tail(fixture: dict) -> float:
    # Two one-sided component bounds for each risk-difference interval, with
    # family-wise Bonferroni across pooled and every frozen temporal-block contrast.
    return fixture["familywise_alpha"] / (4 * fixture["familywise_contrasts"])
