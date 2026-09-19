from __future__ import annotations
import random
from effect_exactly_once import *
from interval_contract import EffectEvent, classify_effects

known = {'a', 'b'}
event = EffectEvent(100, 'a', True, True)

# Predecessor duplicate delivery double-counts.
assert classify_effects([event, event], known)['useful_bound'] == 2

# Same effect ID duplicates fail closed.
try:
    classify_effect_records([
        EffectRecord('e1', event), EffectRecord('e1', event)
    ], known)
except ValueError as exc:
    assert str(exc) == 'duplicate effect_id'
else:
    raise AssertionError('duplicate effect_id accepted')

# Same payload with distinct IDs remains two records.
assert classify_effect_records([
    EffectRecord('e1', event), EffectRecord('e2', event)
], known)['useful_bound'] == 2

# Malformed IDs fail closed.
for bad in [None, '', '   ', 0, 1.0, False, b'e']:
    try:
        classify_effect_records([EffectRecord(bad, event)], known)  # type: ignore[arg-type]
    except ValueError as exc:
        assert str(exc) == 'invalid effect_id'
    else:
        raise AssertionError(('invalid effect ID accepted', repr(bad)))

base_events = [
    EffectEvent(1, 'a', True, True),
    EffectEvent(2, 'a', True, False),
    EffectEvent(3, None, True, True),
    EffectEvent(4, 'missing', True, True),
    EffectEvent(5, 'b', False, True),
]
records = [EffectRecord(f'e{i}', evt) for i, evt in enumerate(base_events)]
assert classify_effect_records(records, known) == classify_effects(base_events, known)

valid_ids = ['e0', ' e ', 'é', '🚀', '0', 'A\tB']
invalid_ids = [None, '', '   ', 0, 1.0, False, b'e']


def disposition(ids):
    if any(not (isinstance(x, str) and bool(x.strip())) for x in ids):
        return 'invalid'
    if len(ids) != len(set(ids)):
        return 'duplicate'
    return 'valid'


rng = random.Random(95520260917)
for case in range(100_000):
    n = rng.randrange(0, 9)
    ids = []
    events = []
    for _ in range(n):
        if ids and rng.random() < 0.20:
            rid = rng.choice(ids)
        else:
            rid = rng.choice(valid_ids + invalid_ids)
        ids.append(rid)
        events.append(EffectEvent(
            rng.randrange(0, 100),
            rng.choice(['a', 'b', 'missing', None]),
            bool(rng.getrandbits(1)), bool(rng.getrandbits(1)),
        ))
    records = [
        EffectRecord(rid, evt) for rid, evt in zip(ids, events)
    ]  # type: ignore[arg-type]
    disp = disposition(ids)
    if disp != 'valid':
        try:
            classify_effect_records(records, known)
        except ValueError as exc:
            expected = 'invalid effect_id' if disp == 'invalid' else 'duplicate effect_id'
            assert str(exc) == expected, (case, ids, str(exc), expected)
        else:
            raise AssertionError((case, disp, ids))
    else:
        assert classify_effect_records(records, known) == classify_effects(events, known), (
            case, ids
        )

# All-unique traces preserve predecessor counts exactly.
rng = random.Random(95520260918)
for case in range(50_000):
    n = rng.randrange(0, 10)
    events = []
    records = []
    for i in range(n):
        evt = EffectEvent(
            rng.randrange(0, 100),
            rng.choice(['a', 'b', 'missing', None]),
            bool(rng.getrandbits(1)), bool(rng.getrandbits(1)),
        )
        events.append(evt)
        records.append(EffectRecord(f'case{case}-event{i}', evt))
    assert classify_effect_records(records, known) == classify_effects(events, known), (
        case, events
    )

print('PASS delivery_fuzz=100000 unique_traces=50000')
