from __future__ import annotations

from scenario import ACTION_TIMES_MS, VALID, HARD, AMBIG, Scenario
from candidate import EFFECT, REFUSE, YIELD, INACTIVE


def _oracle_regime(s: Scenario, t_ms: int) -> str:
    # Intentionally separate from candidate._candidate_regime.
    hard = (
        (t_ms >= s.persistent_hard_start_ms)
        or (s.transient_hard_start_ms <= t_ms and t_ms < s.transient_hard_end_ms)
    )
    ambiguous = s.ambiguous_start_ms <= t_ms and t_ms < s.ambiguous_end_ms
    if hard:
        return HARD
    if ambiguous:
        return AMBIG
    return VALID


def exact_reference(s: Scenario) -> list[str]:
    out = []
    for t in ACTION_TIMES_MS:
        r = _oracle_regime(s, t)
        out.append(EFFECT if r == VALID else (YIELD if r == AMBIG else REFUSE))
    return out


def guarded_cache_reference(s: Scenario) -> list[str]:
    out = []
    active = True
    for t in ACTION_TIMES_MS:
        if not active:
            out.append(INACTIVE)
            continue
        if s.cache_generation != s.current_generation:
            active = False
            out.append(INACTIVE)
            continue
        r = _oracle_regime(s, t)
        if r == HARD:
            active = False
            out.append(INACTIVE)
        elif r == AMBIG:
            out.append(YIELD)
        else:
            out.append(EFFECT)
    return out


def regime_at(s: Scenario, t_ms: int) -> str:
    return _oracle_regime(s, t_ms)
