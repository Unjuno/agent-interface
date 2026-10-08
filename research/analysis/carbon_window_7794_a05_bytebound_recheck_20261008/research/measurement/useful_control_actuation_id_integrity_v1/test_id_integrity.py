from __future__ import annotations
import random
from id_integrity import *
from interval_contract import ReleaseReceipt

wait = Interval(0, 1000)
receipt = ReleaseReceipt(200, 220, False)
authority = [Interval(0, 1000)]

# Predecessor fail-open reproductions.
for bad in [None, '', '   ', 0, 1.0, False, b'a']:
    act = Actuation(100, receipt, authority, bad)  # type: ignore[arg-type]
    evt = EffectEvent(150, bad, True, True)  # type: ignore[arg-type]
    out = analyze(wait, [act], [evt])
    assert out['effects']['useful_bound'] == 1, (bad, out)

# Candidate malformed actuation IDs reject.
for bad in [None, '', '   ', '\t\n', 0, 1.0, False, b'a']:
    act = Actuation(100, receipt, authority, bad)  # type: ignore[arg-type]
    try:
        analyze_id_safe(wait, [act], [])
    except ValueError as exc:
        assert str(exc) == 'invalid actuation_id'
    else:
        raise AssertionError(('actuation accepted', repr(bad)))

# Valid IDs remain distinct; no canonicalization.
valid = ['a', ' a ', '0', 'é', '🚀', 'A\tB']
for aid in valid:
    act = Actuation(100, receipt, authority, aid)
    out = analyze_id_safe(wait, [act], [EffectEvent(150, aid, True, True)])
    assert out['effects']['useful_bound'] == 1
    assert out['effects']['invalid_identity'] == 0

# None remains exclusively unbound on the effect side.
act = Actuation(100, receipt, authority, 'a')
out = analyze_id_safe(wait, [act], [EffectEvent(150, None, True, True)])
assert out['effects']['useful_unbound'] == 1
assert out['effects']['useful_bound'] == 0

# Malformed effect IDs never bind.
for bad in ['', '   ', 0, 1.0, False, b'a']:
    for scored in [False, True]:
        out = analyze_id_safe(
            wait, [act], [EffectEvent(150, bad, scored, True)]  # type: ignore[arg-type]
        )
        assert out['effects']['invalid_identity'] == 1
        assert sum(out['effects'].values()) == 1


def valid_id(value):
    return isinstance(value, str) and bool(value.strip())


def oracle_effect(evt, known):
    if evt.actuation_id is not None and not valid_id(evt.actuation_id):
        return 'invalid_identity'
    if not evt.independently_scored:
        return 'unscored'
    if evt.actuation_id in known:
        return 'useful_bound' if evt.useful else 'nonuseful_bound'
    return 'useful_unbound' if evt.useful else None


rng = random.Random(95320260917)
valid_pool = ['a', 'b', ' a ', '0', 'é', '🚀', 'A\tB']
invalid_pool = [None, '', '   ', 0, 1.0, False, b'a', (), []]
for case in range(100_000):
    raw_id = rng.choice(valid_pool + invalid_pool)
    act = Actuation(100, receipt, authority, raw_id)  # type: ignore[arg-type]
    if not valid_id(raw_id):
        try:
            analyze_id_safe(wait, [act], [])
        except ValueError:
            pass
        else:
            raise AssertionError((case, 'invalid actuation accepted', raw_id))
        continue
    event_id = rng.choice(valid_pool + invalid_pool)
    evt = EffectEvent(
        150, event_id, bool(rng.getrandbits(1)), bool(rng.getrandbits(1))
    )  # type: ignore[arg-type]
    got = analyze_id_safe(wait, [act], [evt])['effects']
    expected = oracle_effect(evt, {raw_id})
    if expected is None:
        assert sum(got.values()) == 0, (case, evt, got)
    else:
        assert got[expected] == 1 and sum(got.values()) == 1, (
            case, evt, got, expected
        )

# 50k valid traces preserve predecessor outputs except the added zero bucket.
rng = random.Random(95320260918)
for case in range(50_000):
    ws = rng.randrange(0, 30)
    we = rng.randrange(ws + 1, 80)
    case_wait = Interval(ws, we)
    actuations = []
    for j in range(rng.randrange(0, 6)):
        down = rng.randrange(0, 70)
        lo = down + rng.randrange(0, 8)
        hi = lo + rng.randrange(0, 8)
        auth = []
        for _ in range(rng.randrange(0, 4)):
            start = rng.randrange(0, 70)
            auth.append(Interval(start, rng.randrange(start + 1, 81)))
        actuations.append(
            Actuation(down, ReleaseReceipt(lo, hi, False), auth, f'id-{j}')
        )
    ids = [a.actuation_id for a in actuations]
    events = []
    for _ in range(rng.randrange(0, 6)):
        eid = rng.choice([None, 'missing'] + ids) if ids else rng.choice([None, 'missing'])
        events.append(
            EffectEvent(
                rng.randrange(0, 90), eid,
                bool(rng.getrandbits(1)), bool(rng.getrandbits(1)),
            )
        )
    base = analyze(case_wait, actuations, events)
    candidate = analyze_id_safe(case_wait, actuations, events)
    for key in [
        'wait_ns', 'physical_occupancy_lower_ns', 'physical_occupancy_upper_ns',
        'authorized_occupancy_lower_ns', 'authorized_occupancy_upper_ns',
        'per_actuation',
    ]:
        assert base[key] == candidate[key], (case, key, base[key], candidate[key])
    assert candidate['effects']['invalid_identity'] == 0
    for key in ['useful_bound', 'useful_unbound', 'nonuseful_bound', 'unscored']:
        assert base['effects'][key] == candidate['effects'][key], (
            case, key, base['effects'], candidate['effects']
        )

print('PASS identity_fuzz=100000 valid_traces=50000')
