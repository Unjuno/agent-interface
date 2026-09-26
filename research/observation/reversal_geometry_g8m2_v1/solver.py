"""Exact three-observation model compatibility; proposals only, no input API."""
from fractions import Fraction as F
import math

V = F(73)
E = F(1)


def parse(records):
    if not isinstance(records, list) or len(records) != 3:
        raise ValueError('record count')
    if any(not isinstance(r, dict) for r in records):
        raise ValueError('record type')
    if any(type(r.get('source_ns')) is not int for r in records):
        raise ValueError('timestamp type')
    if any(type(r.get('epoch')) is not str or not r['epoch'] for r in records):
        raise ValueError('epoch type')
    if len({r['epoch'] for r in records}) != 1:
        raise ValueError('epoch mismatch')
    ts = [r['source_ns'] for r in records]
    if not ts[0] > ts[1] > ts[2]:
        raise ValueError('timestamp order')
    if any(type(r.get('x')) not in (int, float) or not math.isfinite(r['x']) for r in records):
        raise ValueError('position type')
    return [F(t-ts[0], 10**9) for t in ts], [F(r['x']) for r in records]


def compatible(records):
    try:
        t, y = parse(records)
    except (ValueError, KeyError, TypeError, OverflowError):
        return {'directions': [], 'decision': 0, 'reason': 'INVALID', 'witnesses': {}, 'authority': 'none'}
    found = {}
    for d in (-1, 1):
        # Constant motion covers reversals before the earliest observation.
        lo = max(z-E-d*V*s for s, z in zip(t, y))
        hi = min(z+E-d*V*s for s, z in zip(t, y))
        if lo <= hi:
            found[str(d)] = {'kind': 'constant', 'offset': str((lo+hi)/2)}
            continue
        for left, right in ((t[2], t[1]), (t[1], t[0])):
            mid = (left+right)/2
            signs = [1 if s >= mid else -1 for s in t]
            a = [-d*V*s for s in signs]
            b = [d*V*s*ti for s, ti in zip(signs, t)]
            lower, upper = left, right
            possible = True
            # Eliminate the common unknown offset: every lower <= every upper.
            for i in range(3):
                for j in range(3):
                    coef = a[j]-a[i]
                    rhs = y[j]-y[i]+2*E+b[i]-b[j]
                    if coef > 0:
                        upper = min(upper, rhs/coef)
                    elif coef < 0:
                        lower = max(lower, rhs/coef)
                    elif rhs < 0:
                        possible = False
            if possible and lower <= upper:
                tau = (lower+upper)/2
                c_lo = max(y[i]-E-a[i]*tau-b[i] for i in range(3))
                c_hi = min(y[i]+E-a[i]*tau-b[i] for i in range(3))
                c = (c_lo+c_hi)/2
                if not all(abs(c+d*V*abs(ti-tau)-zi) <= E for ti, zi in zip(t, y)):
                    raise ArithmeticError('invalid witness')
                found[str(d)] = {'kind': 'reversal', 'tau': str(tau), 'offset': str(c)}
                break
    ds = sorted(map(int, found))
    return {'directions': ds, 'decision': ds[0] if len(ds) == 1 else 0,
            'reason': 'SINGLETON' if len(ds) == 1 else 'AMBIGUOUS' if ds else 'INFEASIBLE',
            'witnesses': found, 'authority': 'none'}


def exact_heuristic(records):
    t, y = parse(records)
    signs = []
    for i in (0, 1):
        delta = y[i]-y[i+1]
        expected = V*(t[i]-t[i+1])
        pos, neg = abs(delta-expected) <= 2*E, abs(delta+expected) <= 2*E
        signs.append(None if pos == neg else 1 if pos else -1)
    new, old = signs
    if new is not None:
        return 0 if old == new else new
    return -old if old is not None else 0
