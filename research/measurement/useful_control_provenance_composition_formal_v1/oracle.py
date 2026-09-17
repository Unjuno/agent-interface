from __future__ import annotations
from typing import Any, Sequence
from composed_contract import EffectRecord
from interval_contract import Actuation, EffectEvent, Interval


def valid_id(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _points(start: int, end: int) -> set[int]:
    return set(range(start, end)) if end > start else set()


def _within(points: set[int], interval: Interval) -> set[int]:
    return {x for x in points if interval.start_ns <= x < interval.end_ns}


def oracle_analyze(wait: Interval, actuations: Sequence[Actuation], records: Sequence[EffectRecord]):
    # Gate 1, intentionally authored independently from candidate implementation.
    for a in actuations:
        if not valid_id(a.actuation_id):
            return ('error', 'invalid actuation_id')
    aids = [a.actuation_id for a in actuations]
    if len(aids) != len(set(aids)):
        return ('error', 'duplicate actuation_id')

    # Gate 2.
    for r in records:
        if not valid_id(r.effect_id):
            return ('error', 'invalid effect_id')
    eids = [r.effect_id for r in records]
    if len(eids) != len(set(eids)):
        return ('error', 'duplicate effect_id')

    wait_points = _points(wait.start_ns, wait.end_ns)
    physical_lower: set[int] = set()
    physical_upper: set[int] = set()
    auth_lower: set[int] = set()
    auth_upper: set[int] = set()
    per: dict[str, dict[str, int]] = {}

    for a in actuations:
        lower = _points(a.down_ns, a.release.lo_ns) & wait_points
        upper = _points(a.down_ns, a.release.hi_ns) & wait_points
        authority: set[int] = set()
        for interval in a.authority:
            authority |= _points(interval.start_ns, interval.end_ns)
        al = lower & authority
        au = upper & authority
        physical_lower |= lower
        physical_upper |= upper
        auth_lower |= al
        auth_upper |= au
        per[a.actuation_id] = {
            'lower_ns': len(lower),
            'upper_ns': len(upper),
            'authority_lower_ns': len(al),
            'authority_upper_ns': len(au),
        }

    effects = {
        'useful_bound': 0,
        'useful_unbound': 0,
        'nonuseful_bound': 0,
        'unscored': 0,
        'invalid_identity': 0,
        'invalid_temporal': 0,
    }
    by_id = {a.actuation_id: a for a in actuations}
    for r in records:
        e: EffectEvent = r.event
        if e.actuation_id is not None and not valid_id(e.actuation_id):
            effects['invalid_identity'] += 1
            continue
        if e.t_ns < 0:
            effects['invalid_temporal'] += 1
            continue
        if not e.independently_scored:
            effects['unscored'] += 1
            continue
        a = by_id.get(e.actuation_id)
        if a is None:
            if e.useful:
                effects['useful_unbound'] += 1
            continue
        if e.t_ns < a.down_ns:
            effects['invalid_temporal'] += 1
            continue
        if e.useful:
            effects['useful_bound'] += 1
        else:
            effects['nonuseful_bound'] += 1

    return ('ok', {
        'wait_ns': len(wait_points),
        'physical_occupancy_lower_ns': len(physical_lower),
        'physical_occupancy_upper_ns': len(physical_upper),
        'authorized_occupancy_lower_ns': len(auth_lower),
        'authorized_occupancy_upper_ns': len(auth_upper),
        'per_actuation': per,
        'effects': effects,
    })
