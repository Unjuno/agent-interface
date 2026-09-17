from __future__ import annotations
from pathlib import Path
import sys
from typing import Any, Iterable, Sequence

_V1 = Path(__file__).resolve().parent.parent / 'useful_control_interval_contract_v1'
if str(_V1) not in sys.path:
    sys.path.insert(0, str(_V1))

from interval_contract import Actuation, EffectEvent, Interval, analyze


def is_valid_lineage_id(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_actuations(actuations: Sequence[Actuation]) -> None:
    for actuation in actuations:
        if not is_valid_lineage_id(actuation.actuation_id):
            raise ValueError('invalid actuation_id')
    ids = [a.actuation_id for a in actuations]
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate actuation_id')


def classify_effects_id_safe(
    events: Iterable[EffectEvent], known_actuation_ids: set[str]
) -> dict[str, int]:
    out = {
        'useful_bound': 0,
        'useful_unbound': 0,
        'nonuseful_bound': 0,
        'unscored': 0,
        'invalid_identity': 0,
    }
    for event in events:
        if event.actuation_id is not None and not is_valid_lineage_id(event.actuation_id):
            out['invalid_identity'] += 1
            continue
        if not event.independently_scored:
            out['unscored'] += 1
        elif event.actuation_id in known_actuation_ids:
            out['useful_bound' if event.useful else 'nonuseful_bound'] += 1
        else:
            out['useful_unbound'] += int(event.useful)
    return out


def analyze_id_safe(
    wait: Interval, actuations: Sequence[Actuation], events: Sequence[EffectEvent]
) -> dict:
    validate_actuations(actuations)
    out = analyze(wait, actuations, [])
    out['effects'] = classify_effects_id_safe(
        events, {a.actuation_id for a in actuations}
    )
    return out
