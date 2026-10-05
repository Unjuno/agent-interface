"""Finite synthetic split-conformal recovery-deadline construction (Issue #8024)."""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil


@dataclass(frozen=True)
class Episode:
    episode_id: str
    split: str
    kind: str
    duration: int | None
    censor_at: int | None = None
    hard_event: bool = False
    stratum: str = "nominal"


def conformal_deadline(calibration: list[Episode], alpha: float) -> int | None:
    """Return the finite-sample upper order statistic, or None if uncertified."""
    if not 0 < alpha < 1 or not calibration:
        return None
    if len({e.stratum for e in calibration}) != 1 or any(
           e.split != "calibration" or e.kind != "recoverable" or
           e.duration is None or e.censor_at is not None or e.hard_event
           for e in calibration):
        return None
    rank = ceil((len(calibration) + 1) * (1 - alpha))
    if rank > len(calibration):
        return None
    return sorted(e.duration for e in calibration)[rank - 1]


def decide(episode: Episode, deadline: int | None) -> str:
    """Independent hard-stop bypass; unresolved cases yield at deadline."""
    if episode.hard_event or episode.kind in {"identity_loss", "focus_loss", "lease_loss"}:
        return "immediate_yield"
    if episode.stratum != "nominal":
        return "uncertified_yield"
    if deadline is None:
        return "uncertified_yield"
    if episode.kind == "recoverable" and episode.duration is not None:
        return "recovered" if episode.duration <= deadline else "deadline_yield"
    if episode.kind in {"diverging", "right_censored"}:
        elapsed = episode.censor_at if episode.censor_at is not None else deadline
        return "deadline_yield" if elapsed >= deadline else "pending"
    return "invalid_episode_yield"


def freeze_fixture() -> tuple[list[Episode], list[Episode]]:
    calibration = [Episode(f"c{i}", "calibration", "recoverable", d)
                   for i, d in enumerate((1, 2, 3, 4, 5, 6, 7, 8, 9, 10))]
    evaluation = [Episode(f"e{i}", "evaluation", "recoverable", d)
                  for i, d in enumerate((1, 3, 5, 7, 9, 2, 4, 6, 8))]
    evaluation += [
        Episode("diverge-0", "evaluation", "diverging", None, censor_at=20),
        Episode("censored-0", "evaluation", "right_censored", None, censor_at=20),
        Episode("hard-identity", "evaluation", "identity_loss", None, hard_event=True),
        Episode("hard-focus", "evaluation", "focus_loss", None, hard_event=True),
        Episode("hard-lease", "evaluation", "lease_loss", None, hard_event=True),
    ]
    evaluation += [Episode(f"shift{i}", "evaluation", "recoverable", d,
                           stratum="shift")
                   for i, d in enumerate((11, 12, 13, 14, 15))]
    return calibration, evaluation


def audit(calibration: list[Episode], evaluation: list[Episode], alpha: float) -> dict:
    deadline = conformal_deadline(calibration, alpha)
    decisions = {e.episode_id: decide(e, deadline) for e in evaluation}
    recovered = [e for e in evaluation if e.kind == "recoverable" and
                 e.stratum == "nominal"]
    covered = sum(decisions[e.episode_id] == "recovered" for e in recovered)
    immediate_retained = 0
    fixed_timeout_retained = sum(e.duration <= 9 for e in recovered)
    hysteresis_retained = sum(e.duration <= 2 for e in recovered)
    hard = [e for e in evaluation if e.hard_event]
    return {
        "deadline": deadline,
        "rank": ceil((len(calibration) + 1) * (1 - alpha)),
        "calibration_n": len(calibration),
        "recoverable_evaluation_n": len(recovered),
        "coverage": covered / len(recovered) if recovered else None,
        "nominal_coverage": 1 - alpha,
        "coverage_pass": bool(recovered) and covered / len(recovered) >= 1 - alpha,
        "recoverable_retained": covered,
        "immediate_latch_retained": immediate_retained,
        "fixed_timeout_9_retained": fixed_timeout_retained,
        "hysteresis_2_retained": hysteresis_retained,
        "hard_delayed": [e.episode_id for e in hard
                         if decisions[e.episode_id] != "immediate_yield"],
        "decisions": decisions,
    }
