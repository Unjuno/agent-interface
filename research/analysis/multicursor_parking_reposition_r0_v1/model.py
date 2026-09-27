from __future__ import annotations

def moves(seq):
    return [abs(b-a) for a,b in zip(seq,seq[1:])]

def single_cost(seq):
    return sum(moves(seq))

def aliased_parked_cost(seq,cursor_count):
    if cursor_count < 1:
        raise ValueError('cursor_count')
    physical=seq[0]
    total=0
    for target in seq[1:]:
        total += abs(target-physical)
        physical=target
    return total

def switch_cost(seq,s):
    if s < 0:
        raise ValueError('switch cost')
    return sum(min(m,s) for m in moves(seq))

def switch_gain_formula(seq,s):
    return sum(max(m-s,0) for m in moves(seq))
