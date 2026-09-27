from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any, Sequence

_PARENT = Path(__file__).resolve().parent.parent / 'useful_control_interval_contract_v1'
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from interval_contract import Actuation, EffectEvent, Interval, analyze


def valid_id(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


@dataclass(frozen=True)
class EffectRecord:
    effect_id: str
    event: EffectEvent


def analyze_composed(
    wait: Interval,
    actuations: Sequence[Actuation],
    records: Sequence[EffectRecord],
) -> dict:
    # Gate 1: actuation lineage integrity and uniqueness.
    for actuation in actuations:
        if not valid_id(actuation.actuation_id):
            raise ValueError('invalid actuation_id')
    actuation_ids = [a.actuation_id for a in actuations]
    if len(actuation_ids) != len(set(actuation_ids)):
        raise ValueError('duplicate actuation_id')

    # Gate 2: effect-record exactly-once identity.
    effect_ids: list[str] = []
    for record in records:
        if not valid_id(record.effect_id):
            raise ValueError('invalid effect_id')
        effect_ids.append(record.effect_id)
    if len(effect_ids) != len(set(effect_ids)):
        raise ValueError('duplicate effect_id')

    # Parent #941 remains the sole occupancy implementation.
    out = analyze(wait, actuations, [])
    by_id = {a.actuation_id: a for a in actuations}
    effects = {
        'useful_bound': 0,
        'useful_unbound': 0,
        'nonuseful_bound': 0,
        'unscored': 0,
        'invalid_identity': 0,
        'invalid_temporal': 0,
    }

    for record in records:
        event = record.event
        # Event-lineage identity precedes time because malformed lineage cannot
        # identify the causal down edge against which time would be checked.
        if event.actuation_id is not None and not valid_id(event.actuation_id):
            effects['invalid_identity'] += 1
            continue
        if event.t_ns < 0:
            effects['invalid_temporal'] += 1
            continue
        if not event.independently_scored:
            effects['unscored'] += 1
            continue
        actuation = by_id.get(event.actuation_id)
        if actuation is None:
            effects['useful_unbound'] += int(event.useful)
            continue
        if event.t_ns < actuation.down_ns:
            effects['invalid_temporal'] += 1
            continue
        effects['useful_bound' if event.useful else 'nonuseful_bound'] += 1

    out['effects'] = effects
    return out
