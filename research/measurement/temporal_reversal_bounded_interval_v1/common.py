from __future__ import annotations
import hashlib

TASK_SEED = "TEMPORAL-REVERSAL-BOUNDED-INTERVAL-R1-20260918-006|JITTER-V1"
FORMAL_AGES_MS = (25, 50, 75, 100, 150, 200)
IDENT_CEILING = {25:0.25, 50:0.50, 75:0.75, 100:1.0, 150:1.0, 200:1.0}
PERIOD_US = 100_000
HORIZON_US = 500_000
FULL_DISP = 100_000
POSITION_JITTER_BOUND = 1_000
DISP_ERROR_BOUND = 2_000
UNKNOWN = 0


def position_exact_u(t_us: int, reversal_age_ms: int, post_dir: int) -> int:
    r_us = -reversal_age_ms * 1000
    pre_dir = -post_dir
    if t_us <= r_us:
        return pre_dir * (t_us - r_us)
    return post_dir * (t_us - r_us)


def jitter_u(traj_id: str, t_us: int) -> int:
    msg = f"{TASK_SEED}|{traj_id}|{t_us}".encode("utf-8")
    n = int.from_bytes(hashlib.sha256(msg).digest()[:8], "big")
    return (n % 2001) - 1000


def sample_times_us(phase_us: int) -> list[int]:
    newest = -phase_us
    out = []
    t = newest
    while t >= -HORIZON_US:
        out.append(t)
        t -= PERIOD_US
    return out


def full_sign_exact(d: int):
    if d == FULL_DISP:
        return 1
    if d == -FULL_DISP:
        return -1
    return None


def full_sign_bounded(d: int):
    pos = abs(d - FULL_DISP) <= DISP_ERROR_BOUND
    neg = abs(d + FULL_DISP) <= DISP_ERROR_BOUND
    if pos == neg:
        return None
    return 1 if pos else -1


def strict_exact_estimator(samples: list[int]) -> tuple[int, int]:
    # #1291 behavior generalized to integer micro-units.
    d_new = samples[0] - samples[1]
    d_prev = samples[1] - samples[2]
    s_new = full_sign_exact(d_new)
    if s_new is not None:
        return s_new, 4
    s_prev = full_sign_exact(d_prev)
    if s_prev is not None:
        return -s_prev, 6
    return UNKNOWN, 6


def bounded_interval_estimator(samples: list[int]) -> tuple[int, int]:
    d_new = samples[0] - samples[1]
    d_prev = samples[1] - samples[2]
    s_new = full_sign_bounded(d_new)
    s_prev = full_sign_bounded(d_prev)
    if s_new is not None:
        if s_prev == s_new:
            return UNKNOWN, 8
        return s_new, 8
    if s_prev is not None:
        return -s_prev, 8
    return UNKNOWN, 8
