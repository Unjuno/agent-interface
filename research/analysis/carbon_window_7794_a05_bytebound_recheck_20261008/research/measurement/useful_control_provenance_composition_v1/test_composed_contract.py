from __future__ import annotations
import hashlib, json, random
from composed_contract import *
from interval_contract import ReleaseReceipt

# Fixed cross-gate controls.
w = Interval(0, 1000)
a = Actuation(100, ReleaseReceipt(200, 220, False), [Interval(0, 1000)], 'a')
assert analyze_composed(w, [a], [EffectRecord('e1', EffectEvent(100, 'a', True, True))])['effects']['useful_bound'] == 1
assert analyze_composed(w, [a], [EffectRecord('e1', EffectEvent(99, 'a', True, True))])['effects']['invalid_temporal'] == 1
assert analyze_composed(w, [a], [EffectRecord('e1', EffectEvent(120, 0, True, True))])['effects']['invalid_identity'] == 1
assert analyze_composed(w, [a], [EffectRecord('e1', EffectEvent(120, None, True, True))])['effects']['useful_unbound'] == 1
x = EffectEvent(120, 'a', True, True)
assert analyze_composed(w, [a], [EffectRecord('e1', x), EffectRecord('e2', x)])['effects']['useful_bound'] == 2
for records, expected in [
    ([EffectRecord('e1', x), EffectRecord('e1', x)], 'duplicate effect_id'),
    ([EffectRecord('', x)], 'invalid effect_id'),
]:
    try:
        analyze_composed(w, [a], records)
    except ValueError as exc:
        assert str(exc) == expected
    else:
        raise AssertionError(expected)
for acts, expected in [
    ([Actuation(100, ReleaseReceipt(200, 220, False), [], None)], 'invalid actuation_id'),
    ([a, a], 'duplicate actuation_id'),
]:
    try:
        analyze_composed(w, acts, [])
    except ValueError as exc:
        assert str(exc) == expected
    else:
        raise AssertionError(expected)

# Independent discrete occupancy + separately authored effect oracle.
rng = random.Random(95920260917)
digest = hashlib.sha256()
for case in range(120_000):
    ws = rng.randrange(0, 40)
    we = rng.randrange(ws + 1, 100)
    wait = Interval(ws, we)
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
    known = {a.actuation_id: a for a in actuations}
    records = []
    for k in range(rng.randrange(0, 8)):
        aid = rng.choice([None, 'missing', 0, '   '] + list(known))
        records.append(EffectRecord(
            f'e{k}',
            EffectEvent(rng.randrange(-5, 120), aid, bool(rng.getrandbits(1)), bool(rng.getrandbits(1))),
        ))
    got = analyze_composed(wait, actuations, records)

    def discrete(upper: bool, authorized: bool) -> int:
        covered = set()
        for act in actuations:
            end = act.release.hi_ns if upper else act.release.lo_ns
            for t in range(max(wait.start_ns, act.down_ns), min(wait.end_ns, end)):
                if not authorized or any(iv.start_ns <= t < iv.end_ns for iv in act.authority):
                    covered.add(t)
        return len(covered)

    expected_occupancy = (
        discrete(False, False), discrete(True, False),
        discrete(False, True), discrete(True, True),
    )
    got_occupancy = (
        got['physical_occupancy_lower_ns'], got['physical_occupancy_upper_ns'],
        got['authorized_occupancy_lower_ns'], got['authorized_occupancy_upper_ns'],
    )
    assert got_occupancy == expected_occupancy, (case, got_occupancy, expected_occupancy)

    expected = {
        'useful_bound': 0, 'useful_unbound': 0, 'nonuseful_bound': 0,
        'unscored': 0, 'invalid_identity': 0, 'invalid_temporal': 0,
    }
    for record in records:
        event = record.event
        if event.actuation_id is not None and not (isinstance(event.actuation_id, str) and bool(event.actuation_id.strip())):
            expected['invalid_identity'] += 1
        elif event.t_ns < 0:
            expected['invalid_temporal'] += 1
        elif not event.independently_scored:
            expected['unscored'] += 1
        elif event.actuation_id not in known:
            expected['useful_unbound'] += int(event.useful)
        elif event.t_ns < known[event.actuation_id].down_ns:
            expected['invalid_temporal'] += 1
        else:
            expected['useful_bound' if event.useful else 'nonuseful_bound'] += 1
    assert got['effects'] == expected, (case, got['effects'], expected)
    digest.update(json.dumps([case, got_occupancy, expected], sort_keys=True).encode())

assert digest.hexdigest() == '40080361b1d62bba8ce1dd2a8329ef0b27f835c0a72094780f975bf676199d14'

# Dataset-level malformed controls.
rng = random.Random(95920260918)
for case in range(30_000):
    kind = rng.randrange(4)
    if kind == 0:
        bad = Actuation(1, ReleaseReceipt(2, 3, False), [], rng.choice([None, '', '   ', 0, False, b'x']))
        args = ([bad], [])
        expected = 'invalid actuation_id'
    elif kind == 1:
        good = Actuation(1, ReleaseReceipt(2, 3, False), [], 'a')
        args = ([good], [EffectRecord('dup', EffectEvent(2, 'a', True, True)), EffectRecord('dup', EffectEvent(2, 'a', True, True))])
        expected = 'duplicate effect_id'
    elif kind == 2:
        good = Actuation(1, ReleaseReceipt(2, 3, False), [], 'a')
        args = ([good], [EffectRecord(rng.choice([None, '', '   ', 0, False, b'e']), EffectEvent(2, 'a', True, True))])
        expected = 'invalid effect_id'
    else:
        a1 = Actuation(1, ReleaseReceipt(2, 3, False), [], 'a')
        a2 = Actuation(1, ReleaseReceipt(2, 3, False), [], 'a')
        args = ([a1, a2], [])
        expected = 'duplicate actuation_id'
    try:
        analyze_composed(Interval(0, 5), *args)
    except ValueError as exc:
        assert str(exc) == expected, (case, str(exc), expected)
    else:
        raise AssertionError((case, expected))

print('PASS composition=120000 malformed=30000 digest=40080361b1d62bba8ce1dd2a8329ef0b27f835c0a72094780f975bf676199d14')
