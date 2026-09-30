"""Deterministic covering designs for the synthetic Issue #5330 T0 fixture."""
from itertools import combinations, product

FACTORS = ("freshness", "lease", "responsibility", "delivery")
LEVELS = (0, 1)
ALL_ROWS = tuple(product(LEVELS, repeat=len(FACTORS)))


def coverage(row, strength):
    return {
        (indices, tuple(row[i] for i in indices))
        for indices in combinations(range(len(FACTORS)), strength)
    }


def covering_design(strength):
    uncovered = set().union(*(coverage(row, strength) for row in ALL_ROWS))
    selected = []
    while uncovered:
        best = max(ALL_ROWS, key=lambda row: (len(coverage(row, strength) & uncovered), tuple(-v for v in row)))
        gain = coverage(best, strength) & uncovered
        if not gain:
            raise RuntimeError("covering design stalled")
        selected.append(best)
        uncovered.difference_update(gain)
    return tuple(selected)


OFAT = (ALL_ROWS[0],) + tuple(tuple(int(i == j) for i in range(4)) for j in range(4))
PAIRWISE = covering_design(2)
THREE_WAY = covering_design(3)
EXHAUSTIVE = ALL_ROWS


def pair_hazard(row):
    return row[0] == 1 and row[1] == 1


def triple_hazard(row):
    return row[0] == 1 and row[2] == 1 and row[3] == 1


def result(rows):
    return {
        "rows": [list(row) for row in rows],
        "case_count": len(rows),
        "pair_coverage": len(set().union(*(coverage(row, 2) for row in rows))),
        "triple_coverage": len(set().union(*(coverage(row, 3) for row in rows))),
        "pair_hazard_detected": any(pair_hazard(row) for row in rows),
        "triple_hazard_detected": any(triple_hazard(row) for row in rows),
    }
