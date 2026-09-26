"""Exact affine-clock deadline certificates. Pure calculation; never actuates.

The input clock bounds are assumptions, not a calibration algorithm. Fractions
are parsed from canonical integer/rational strings, never from binary floats.
"""
from __future__ import annotations
from fractions import Fraction as F
from functools import lru_cache
from itertools import combinations
from typing import Any

class Invalid(ValueError):
    pass

def rat(value: Any) -> F:
    if not isinstance(value, str) or not (1 <= len(value) <= 128):
        raise Invalid('rational_string_required')
    try:
        result = F(value)
    except (ValueError, ZeroDivisionError):
        raise Invalid('rational_string_required') from None
    if str(result) != value:
        raise Invalid('noncanonical_rational')
    return result

def pair(value: Any) -> tuple[F, F]:
    if not isinstance(value, list) or len(value) != 2:
        raise Invalid('pair_required')
    return rat(value[0]), rat(value[1])

def parse(doc: dict[str, Any]):
    if not isinstance(doc, dict):
        raise Invalid('object_required')
    if doc.get('scope') != doc.get('expected_scope'):
        raise Invalid('scope_mismatch')
    scope = doc.get('scope')
    if not isinstance(scope, dict) or set(scope) != {'from', 'to', 'epoch'} or any(
        not isinstance(x, str) or not x for x in scope.values()
    ):
        raise Invalid('invalid_scope')
    try:
        a0, a1 = pair(doc['rate'])
        b0, b1 = pair(doc['offset'])
        h0, h1 = pair(doc['valid_s'])
        left, right = pair(doc['release'])
        deadline = rat(doc['deadline'])
        samples = doc['samples']
    except KeyError as e:
        raise Invalid('missing_' + str(e.args[0])) from None
    if not 0 < a0 <= a1:
        raise Invalid('invalid_positive_rate')
    if b0 > b1 or h0 > h1:
        raise Invalid('invalid_bound')
    if left >= right:
        raise Invalid('empty_or_reversed_release')
    if not h0 <= left < right <= h1:
        raise Invalid('outside_clock_horizon')
    if not isinstance(samples, list) or not 1 <= len(samples) <= 32:
        raise Invalid('calibration_missing_or_excessive')
    cal = []
    for sample in samples:
        if not isinstance(sample, dict) or set(sample) != {'s', 'lo', 'hi'}:
            raise Invalid('invalid_sample')
        s, lo, hi = (rat(sample[k]) for k in ('s', 'lo', 'hi'))
        if not h0 <= s <= h1 or lo > hi:
            raise Invalid('invalid_sample_bound')
        cal.append((s, lo, hi))
    return a0, a1, b0, b1, tuple(cal), left, right, deadline

@lru_cache(maxsize=4096)
def eliminate(a0: F, a1: F, b0: F, b1: F, samples: tuple):
    # Lower/upper affine envelopes for offset b, as functions of rate a.
    lows = ((F(0), b0),) + tuple((-s, lo) for s, lo, hi in samples)
    highs = ((F(0), b1),) + tuple((-s, hi) for s, lo, hi in samples)
    j0, j1 = a0, a1
    for ml, cl in lows:
        for mu, cu in highs:
            k, v = ml - mu, cu - cl
            if k > 0:
                j1 = min(j1, v/k)
            elif k < 0:
                j0 = max(j0, v/k)
            elif v < 0:
                return None
    if j0 > j1:
        return None
    return j0, j1, lows, highs

def extremum(j0: F, j1: F, lines: tuple, s: F, lower: bool):
    # A piecewise-linear envelope can change slope only at line crossings.
    candidates = {j0, j1}
    for (m, c), (n, d) in combinations(lines, 2):
        if m != n:
            x = (d-c)/(m-n)
            if j0 <= x <= j1:
                candidates.add(x)
    choices = []
    for a in candidates:
        b = (max if lower else min)(m*a+c for m, c in lines)
        choices.append((s*a+b, a, b))
    value = (min if lower else max)(v for v, a, b in choices)
    return min(item for item in choices if item[0] == value)

def certificate(lo: F, hi: F, deadline: F) -> str:
    # Lower bound is OPEN, upper bound CLOSED. Equality at lower implies late.
    if hi <= deadline:
        return 'ON_TIME'
    if lo >= deadline:
        return 'LATE'
    return 'UNRESOLVED'

def outcome(doc: dict[str, Any]) -> dict[str, Any]:
    base = {'grants_input_authority': False, 'task_success': None}
    try:
        a0, a1, b0, b1, samples, left, right, deadline = parse(doc)
    except Invalid as e:
        return dict(base, status='UNKNOWN_INVALID', reason=str(e))
    reduced = eliminate(a0, a1, b0, b1, samples)
    if reduced is None:
        return dict(base, status='UNKNOWN_INCONSISTENT', reason='empty_clock_set')
    j0, j1, lows, highs = reduced
    lower, la, lb = extremum(j0, j1, lows, left, True)
    upper, ua, ub = extremum(j0, j1, highs, right, False)
    # Comparators use the SAME feasible calibration, without any task authority.
    amin = (j0+j1)/2
    bn = (max(m*amin+c for m,c in lows) + min(m*amin+c for m,c in highs))/2
    nominal = (amin*left+bn, amin*right+bn)
    bm = extremum(j0, j1, lows, F(0), True)[0]
    bM = extremum(j0, j1, highs, F(0), False)[0]
    marginal = (min(j0*left, j1*left)+bm, max(j0*right, j1*right)+bM)
    return dict(base, status=certificate(lower, upper, deadline),
        interval=[str(lower), str(upper)], lower_open=True, upper_closed=True,
        feasible_rate=[str(j0), str(j1)],
        extremizers={'lower':[str(la), str(lb)], 'upper':[str(ua), str(ub)]},
        nominal={'clock':[str(amin),str(bn)], 'interval':list(map(str, nominal)),
                 'status':certificate(*nominal,deadline)},
        marginal={'interval':list(map(str,marginal)),
                  'status':certificate(*marginal,deadline)})
