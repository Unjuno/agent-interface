from __future__ import annotations

from dataclasses import dataclass
from scenario import ACTION_TIMES_MS, SUPERVISOR_TIMES_MS, VALID, HARD, AMBIG, Scenario

EFFECT = "EFFECT"
REFUSE = "REFUSE"
YIELD = "YIELD"
INACTIVE = "CACHE_INVALIDATED"


@dataclass(frozen=True)
class ActionDecision:
    t_ms: int
    disposition: str
    sampled_regime: str | None = None


def _candidate_regime(s: Scenario, t_ms: int) -> str:
    if s.transient_hard_start_ms <= t_ms < s.transient_hard_end_ms:
        return HARD
    if t_ms >= s.persistent_hard_start_ms:
        return HARD
    if s.ambiguous_start_ms <= t_ms < s.ambiguous_end_ms:
        return AMBIG
    return VALID


def _last_supervisor_sample(t_ms: int) -> int:
    return max(t for t in SUPERVISOR_TIMES_MS if t <= t_ms)


def run_redecide_every_cycle(s: Scenario) -> dict:
    decisions = []
    for t in ACTION_TIMES_MS:
        regime = _candidate_regime(s, t)
        if regime == VALID:
            disposition = EFFECT
        elif regime == AMBIG:
            disposition = YIELD
        else:
            disposition = REFUSE
        decisions.append(ActionDecision(t, disposition))
    return {"semantic_decisions": len(ACTION_TIMES_MS), "decisions": decisions}


def run_cached_supervisor_only(s: Scenario) -> dict:
    decisions = []
    active = True
    for t in ACTION_TIMES_MS:
        sampled = _candidate_regime(s, _last_supervisor_sample(t))
        if not active:
            disposition = INACTIVE
        elif sampled == HARD:
            active = False
            disposition = INACTIVE
        elif sampled == AMBIG:
            disposition = YIELD
        else:
            disposition = EFFECT
        decisions.append(ActionDecision(t, disposition, sampled))
    return {"semantic_decisions": 1, "decisions": decisions}


def run_cached_action_guard(s: Scenario, mutation: str | None = None) -> dict:
    decisions = []
    active = True
    for t in ACTION_TIMES_MS:
        sampled = _candidate_regime(s, _last_supervisor_sample(t))
        if not active:
            disposition = INACTIVE
        elif mutation != "ignore_generation" and s.cache_generation != s.current_generation:
            active = False
            disposition = INACTIVE
        elif sampled == HARD:
            active = False
            disposition = INACTIVE
        else:
            if mutation in {"remove_guard", "stale_sample_as_current"}:
                current = sampled
            else:
                current = _candidate_regime(s, t)
            if current == HARD:
                active = False
                disposition = INACTIVE
            elif current == AMBIG:
                disposition = EFFECT if mutation == "ambiguous_is_valid" else YIELD
            else:
                disposition = EFFECT
        decisions.append(ActionDecision(t, disposition, sampled))
    return {"semantic_decisions": 1, "decisions": decisions}
