from __future__ import annotations
import random
from temporal_lower_bound import (
    Actuation, EffectEvent, Interval, analyze, analyze_temporal,
    classify_effects_temporal,
)
from interval_contract import ReleaseReceipt


def event(t, aid, scored, useful):
    return EffectEvent(t, aid, scored, useful)


def oracle(evt, by_id):
    if evt.t_ns < 0:
        return 'invalid_temporal'
    if not evt.independently_scored:
        return 'unscored'
    actuation = by_id.get(evt.actuation_id)
    if actuation is None:
        return 'useful_unbound' if evt.useful else None
    if evt.t_ns < actuation.down_ns:
        return 'invalid_temporal'
    return 'useful_bound' if evt.useful else 'nonuseful_bound'


wait = Interval(100, 1000)
a = Actuation(200, ReleaseReceipt(400, 450, False), [Interval(100, 1000)], 'a')

# Mandatory predecessor-defect reproduction.
assert analyze(wait, [a], [event(150, 'a', True, True)])['effects']['useful_bound'] == 1
assert analyze(wait, [a], [event(-1, 'a', True, True)])['effects']['useful_bound'] == 1

controls = [
    (event(150, 'a', True, True), 'invalid_temporal'),
    (event(150, 'a', True, False), 'invalid_temporal'),
    (event(-1, 'a', True, True), 'invalid_temporal'),
    (event(200, 'a', True, True), 'useful_bound'),
    (event(300, 'a', True, False), 'nonuseful_bound'),
    (event(900, 'a', True, True), 'useful_bound'),
    (event(300, None, True, True), 'useful_unbound'),
    (event(300, 'a', False, True), 'unscored'),
    (event(-1, 'a', False, True), 'invalid_temporal'),
]
for evt, bucket in controls:
    got = analyze_temporal(wait, [a], [evt])['effects']
    assert got[bucket] == 1 and sum(got.values()) == 1, (evt, bucket, got)

rng = random.Random(95020260917)
for case in range(100_000):
    down = rng.randrange(0, 101)
    act = Actuation(
        down,
        ReleaseReceipt(down + rng.randrange(0, 30), down + 30 + rng.randrange(0, 30), False),
        [Interval(0, 200)],
        'a',
    )
    evt = EffectEvent(
        rng.randrange(-10, 151),
        rng.choice(['a', 'missing', None]),
        bool(rng.getrandbits(1)),
        bool(rng.getrandbits(1)),
    )
    got = classify_effects_temporal([evt], [act])
    expected = oracle(evt, {'a': act})
    if expected is None:
        assert sum(got.values()) == 0, (case, evt, got)
    else:
        assert got[expected] == 1 and sum(got.values()) == 1, (case, evt, got, expected)

rng = random.Random(95020260918)
occupancy_keys = [
    'wait_ns', 'physical_occupancy_lower_ns', 'physical_occupancy_upper_ns',
    'authorized_occupancy_lower_ns', 'authorized_occupancy_upper_ns', 'per_actuation',
]
for case in range(50_000):
    ws = rng.randrange(0, 40)
    we = rng.randrange(ws + 1, 100)
    case_wait = Interval(ws, we)
    actuations = []
    for j in range(rng.randrange(0, 6)):
        down = rng.randrange(0, 90)
        lo = down + rng.randrange(0, 10)
        hi = lo + rng.randrange(0, 10)
        authority = []
        for _ in range(rng.randrange(0, 4)):
            start = rng.randrange(0, 90)
            authority.append(Interval(start, rng.randrange(start + 1, 101)))
        actuations.append(Actuation(down, ReleaseReceipt(lo, hi, False), authority, f'a{j}'))
    ids = [a.actuation_id for a in actuations]
    events = []
    for _ in range(rng.randrange(0, 6)):
        aid = rng.choice([None, 'missing'] + ids) if ids else rng.choice([None, 'missing'])
        events.append(EffectEvent(
            rng.randrange(-5, 120), aid,
            bool(rng.getrandbits(1)), bool(rng.getrandbits(1)),
        ))
    base = analyze(case_wait, actuations, events)
    candidate = analyze_temporal(case_wait, actuations, events)
    for key in occupancy_keys:
        assert base[key] == candidate[key], (case, key, base[key], candidate[key])
    by_id = {a.actuation_id: a for a in actuations}
    invalid = sum(
        1 for evt in events
        if evt.t_ns < 0 or (
            evt.independently_scored and evt.actuation_id in by_id
            and evt.t_ns < by_id[evt.actuation_id].down_ns
        )
    )
    assert candidate['effects']['invalid_temporal'] == invalid, (
        case, events, candidate['effects'], invalid
    )

print('PASS fixed_controls=9 event_fuzz=100000 mixed_traces=50000')
