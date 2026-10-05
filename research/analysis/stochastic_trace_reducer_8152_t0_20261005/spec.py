"""Frozen finite event model for Issue #8152 T0; no GUI, model, or network."""
from __future__ import annotations

SCHEMA = "unjuno.issue8152.stochastic-trace-t0.v1"
TARGET = "TARGET_STALE_GUARD"
COMPETING = "COMPETING_WIDGET_CRASH"
EXIT_CODE = 17  # Deliberately shared by TARGET and COMPETING.
MARGIN = 0.20
ALPHA_FAMILY = 0.05
INSTANCES = 12
BASELINE_N = 64
FIXED_N = 64
SEQUENTIAL_MIN_N = 8
SEQUENTIAL_STEP = 8
SEQUENTIAL_MAX_N = 64
CONFIRM_N_PER_STRATUM = 512
SEARCH_SEED_START = 100_000
CONFIRM_SEED_START = 10_000_000
STRATUM_WARM_RATE = (0.94, 0.86, 0.78, 0.70)
STRATUM_COLD_RATE = (0.57, 0.49, 0.41, 0.33)
COMPETING_RATE = 0.08

MANDATORY = ("reset", "lease", "release")
DEPENDENCIES = {
    "lease": ("reset",),
    "observation": ("lease",),
    "commit": ("observation",),
    "timing_guard": ("commit",),
    "warmup": ("reset",),
    "telemetry": ("reset",),
    "poll_a": ("reset",),
    "poll_b": ("reset",),
    "repaint": ("reset",),
    "context_note": ("reset",),
    "competing_fault": ("lease",),
    "release": ("lease",),
}
BASE_TRACE = (
    "reset", "lease", "observation", "commit", "timing_guard", "warmup",
    "telemetry", "poll_a", "poll_b", "repaint", "context_note",
    "competing_fault", "release",
)
# Each removed set is causally closed: no retained event depends on a removed one.
REMOVAL_GROUPS = (
    ("telemetry", ("telemetry",)),
    ("poll_pair", ("poll_a", "poll_b")),
    ("repaint", ("repaint",)),
    ("context_note", ("context_note",)),
    ("competing_fault", ("competing_fault",)),
    ("warmup", ("warmup",)),
    ("commit_bundle", ("commit", "timing_guard")),
    ("observation_bundle", ("observation", "commit", "timing_guard")),
)


def strata_for_instance(instance: int) -> tuple[int, ...]:
    # Three independently seeded cases in each preregistered environment stratum.
    return (instance // 3,)


def seed_for(instance: int, index: int, phase: str) -> int:
    if phase == "search_baseline":
        return SEARCH_SEED_START + instance * 100_000 + index
    if phase == "search_candidate":
        return SEARCH_SEED_START + 2_000_000 + instance * 100_000 + index
    if phase == "confirm":
        return CONFIRM_SEED_START + instance * 10_000 + index
    raise ValueError("unknown_seed_phase")


def exact_spec() -> dict:
    return {
        "schema": SCHEMA,
        "target_fingerprint": TARGET,
        "competing_fingerprint": COMPETING,
        "same_exit_code": EXIT_CODE,
        "mandatory_events": list(MANDATORY),
        "dependencies": {k: list(v) for k, v in DEPENDENCIES.items()},
        "base_trace": list(BASE_TRACE),
        "removal_groups": [[n, list(g)] for n, g in REMOVAL_GROUPS],
        "noninferiority_margin": MARGIN,
        "familywise_alpha": ALPHA_FAMILY,
        "instances": INSTANCES,
        "baseline_repetitions": BASELINE_N,
        "fixed_repetitions_per_candidate": FIXED_N,
        "sequential_minimum": SEQUENTIAL_MIN_N,
        "sequential_increment": SEQUENTIAL_STEP,
        "sequential_maximum": SEQUENTIAL_MAX_N,
        "confirmation_repetitions_per_stratum": CONFIRM_N_PER_STRATUM,
        "search_seed_start": SEARCH_SEED_START,
        "confirmation_seed_start": CONFIRM_SEED_START,
        "warm_target_rates_by_stratum": list(STRATUM_WARM_RATE),
        "cold_target_rates_by_stratum": list(STRATUM_COLD_RATE),
        "competing_failure_rate": COMPETING_RATE,
    }
