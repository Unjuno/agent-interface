from __future__ import annotations
from pathlib import Path
import sys
from typing import Iterable, Sequence

_V1 = Path(__file__).resolve().parent.parent / 'useful_control_interval_contract_v1'
if str(_V1) not in sys.path:
    sys.path.insert(0, str(_V1))

from interval_contract import Actuation, EffectEvent, Interval, analyze


def classify_effects_temporal(
    events: Iterable[EffectEvent], actuations: Sequence[Actuation]
) -> dict[str, int]:
    by_id = {a.actuation_id: a for a in actuations}
    if len(by_id) != len(actuations):
        raise ValueError('duplicate actuation_id')
    out = {
        'useful_bound': 0,
        'useful_unbound': 0,
        'nonuseful_bound': 0,
        'unscored': 0,
        'invalid_temporal': 0,
    }
    for event in events:
        if event.t_ns < 0:
            out['invalid_temporal'] += 1
            continue
        if not event.independently_scored:
            out['unscored'] += 1
            continue
        actuation = by_id.get(event.actuation_id)
        if actuation is None:
            out['useful_unbound'] += int(event.useful)
            continue
        if event.t_ns < actuation.down_ns:
            out['invalid_temporal'] += 1
            continue
        out['useful_bound' if event.useful else 'nonuseful_bound'] += 1
    return out


def analyze_temporal(
    wait: Interval, actuations: Sequence[Actuation], events: Sequence[EffectEvent]
) -> dict:
    # Parent v1 remains the sole occupancy implementation. This successor changes
    # only effect temporal classification.
    out = analyze(wait, actuations, [])
    out['effects'] = classify_effects_temporal(events, actuations)
    return out
