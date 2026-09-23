from __future__ import annotations
from typing import Sequence
from interval_contract import Actuation, EffectEvent, Interval, analyze


def _valid_lineage_id(value, *, allow_none: bool) -> bool:
    if value is None:
        return allow_none
    return isinstance(value, str) and len(value) > 0


def validate_lineage(actuations: Sequence[Actuation], events: Sequence[EffectEvent]) -> None:
    for actuation in actuations:
        if not _valid_lineage_id(actuation.actuation_id, allow_none=False):
            raise ValueError('invalid actuation_id')
    for event in events:
        if not _valid_lineage_id(event.actuation_id, allow_none=True):
            raise ValueError('invalid effect actuation_id')


def analyze_validated(wait: Interval, actuations: Sequence[Actuation], events: Sequence[EffectEvent]) -> dict:
    validate_lineage(actuations, events)
    return analyze(wait, actuations, events)
