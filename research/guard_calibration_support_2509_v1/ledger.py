from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

REQUIRED = {
    "stale_refusal",
    "fresh_refusal",
    "stale_action_recovery",
    "fresh_success",
    "right_censored",
}

@dataclass(frozen=True)
class Episode:
    episode_id: str
    population: str
    status: str
    selector: str
    outcome: str
    clock: str
    historical: bool = False

def validate(rows: Iterable[Episode]) -> tuple[bool, list[str]]:
    rows = list(rows)
    errors: list[str] = []
    ids = [r.episode_id for r in rows]
    if len(ids) != len(set(ids)):
        errors.append("DUPLICATE_EPISODE_ID")
    if any(r.historical for r in rows):
        errors.append("HISTORICAL_ROW_POOLED")
    populations = {r.population for r in rows}
    clocks = {r.clock for r in rows}
    if len(populations) != 1:
        errors.append("POPULATION_MIXED")
    if len(clocks) != 1:
        errors.append("CLOCK_MIXED")
    observed = {r.status for r in rows}
    missing = sorted(REQUIRED - observed)
    if missing:
        errors.append("MISSING_SUPPORT:" + ",".join(missing))
    return not errors, errors
