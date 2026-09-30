"""Exact possible maxima under one shared affine parameter; no action API."""
from fractions import Fraction
import re


def rational(value):
    """Accept exact integers or rational strings, never binary floats/bools."""
    if type(value) is int:
        return Fraction(value)
    if type(value) is str and re.fullmatch(r'-?\d+(?:/[1-9]\d*)?', value):
        return Fraction(value)
    raise ValueError('expected an exact integer or rational string')


def validate(case):
    if type(case) is not dict or set(case) != {'id', 'a', 'b', 'e', 'domain'}:
        raise ValueError('case fields')
    if type(case['id']) is not str:
        raise ValueError('case identity')
    vectors = [case[key] for key in ('a', 'b', 'e')]
    if any(type(v) is not list for v in vectors):
        raise ValueError('vectors must be lists')
    n = len(vectors[0])
    if not 1 <= n <= 8 or any(len(v) != n for v in vectors):
        raise ValueError('candidate count')
    a, b, e = [[rational(x) for x in v] for v in vectors]
    domain = case['domain']
    if type(domain) is not list or len(domain) != 2:
        raise ValueError('domain')
    lo, hi = map(rational, domain)
    if lo > hi or any(x < 0 for x in e):
        raise ValueError('empty domain or negative radius')
    return a, b, e, lo, hi


def evaluate(case):
    a, b, e, low, high = validate(case)
    n = len(a)
    lower = [min(a[i] + b[i]*low, a[i] + b[i]*high) - e[i] for i in range(n)]
    upper = [max(a[i] + b[i]*low, a[i] + b[i]*high) + e[i] for i in range(n)]
    box = [i for i in range(n) if upper[i] >= max(lower)]
    pairwise, joint, intervals = [], [], []
    for i in range(n):
        lo, hi, possible, pairs = low, high, True, True
        for j in range(n):
            if i == j:
                continue
            constant = a[i] - a[j] + e[i] + e[j]
            slope = b[i] - b[j]
            if max(constant + slope*low, constant + slope*high) < 0:
                pairs = False
            if slope > 0:
                lo = max(lo, -constant/slope)
            elif slope < 0:
                hi = min(hi, -constant/slope)
            elif constant < 0:
                possible = False
        if pairs:
            pairwise.append(i)
        if possible and lo <= hi:
            joint.append(i)
            intervals.append([str(lo), str(hi)])
        else:
            intervals.append(None)
    return {'box': box, 'pairwise': pairwise, 'joint': joint,
            'intervals': intervals, 'action_authority': False, 'task_success': None}
