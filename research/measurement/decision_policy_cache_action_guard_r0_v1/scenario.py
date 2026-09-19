from __future__ import annotations

from dataclasses import dataclass
import random

HORIZON_MS = 100
ACTION_TIMES_MS = tuple(range(5, HORIZON_MS, 5))
SUPERVISOR_TIMES_MS = tuple(range(0, HORIZON_MS + 1, 20))
VALID = "VALID_CONTINUATION"
HARD = "HARD_INVALIDATION"
AMBIG = "AMBIGUOUS_BOUNDARY"


@dataclass(frozen=True)
class Scenario:
    scenario_id: int
    ambiguous_start_ms: int
    ambiguous_end_ms: int
    transient_hard_start_ms: int
    transient_hard_end_ms: int
    persistent_hard_start_ms: int
    cache_generation: int = 7
    current_generation: int = 7


def _window_around_action(rng: random.Random, segment_start: int) -> tuple[int, int]:
    slots = (segment_start + 5, segment_start + 10, segment_start + 15)
    slot = rng.choice(slots)
    left = rng.randint(1, 3)
    right = rng.randint(1, 3)
    start = max(segment_start + 1, slot - left)
    end = min(segment_start + 19, slot + right + 1)
    if not (start <= slot < end):
        raise AssertionError("window must contain selected action slot")
    return start, end


def generate_scenarios(count: int, seed: int):
    rng = random.Random(seed)
    for sid in range(count):
        ambiguous_segment = rng.choice((0, 20))
        hard_segment = rng.choice((40, 60))
        a0, a1 = _window_around_action(rng, ambiguous_segment)
        h0, h1 = _window_around_action(rng, hard_segment)
        # Persistent invalidation deliberately begins after the 80 ms supervisor sample,
        # so sampled supervision alone cannot rely on a lucky coincident sample.
        persistent = rng.choice((83, 87, 91))
        yield Scenario(
            scenario_id=sid,
            ambiguous_start_ms=a0,
            ambiguous_end_ms=a1,
            transient_hard_start_ms=h0,
            transient_hard_end_ms=h1,
            persistent_hard_start_ms=persistent,
        )


def scenario_to_dict(s: Scenario) -> dict:
    return {
        "scenario_id": s.scenario_id,
        "ambiguous": [s.ambiguous_start_ms, s.ambiguous_end_ms],
        "transient_hard": [s.transient_hard_start_ms, s.transient_hard_end_ms],
        "persistent_hard_start_ms": s.persistent_hard_start_ms,
        "cache_generation": s.cache_generation,
        "current_generation": s.current_generation,
    }
