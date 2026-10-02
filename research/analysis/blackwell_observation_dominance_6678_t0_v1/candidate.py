"""Exact finite garbling-feasibility candidate for Issue #6678 T0."""

from fractions import Fraction
from itertools import combinations
import json
import sys


def q(pair):
    return Fraction(pair[0], pair[1])


def rank(matrix):
    a = [list(map(Fraction, row)) for row in matrix]
    r = 0
    for c in range(len(a[0]) if a else 0):
        pivot = next((i for i in range(r, len(a)) if a[i][c]), None)
        if pivot is None:
            continue
        a[r], a[pivot] = a[pivot], a[r]
        scale = a[r][c]
        a[r] = [v / scale for v in a[r]]
        for i in range(len(a)):
            if i != r and a[i][c]:
                factor = a[i][c]
                a[i] = [x - factor * y for x, y in zip(a[i], a[r])]
        r += 1
        if r == len(a):
            break
    return r


def solve_unique(matrix, rhs, variables):
    aug = [list(row) + [value] for row, value in zip(matrix, rhs)]
    pivot_cols = []
    row = 0
    for col in range(variables):
        pivot = next((i for i in range(row, len(aug)) if aug[i][col]), None)
        if pivot is None:
            continue
        aug[row], aug[pivot] = aug[pivot], aug[row]
        scale = aug[row][col]
        aug[row] = [x / scale for x in aug[row]]
        for i in range(len(aug)):
            if i != row and aug[i][col]:
                f = aug[i][col]
                aug[i] = [x - f * y for x, y in zip(aug[i], aug[row])]
        pivot_cols.append(col)
        row += 1
        if row == len(aug):
            break
    if any(not any(line[:variables]) and line[variables] for line in aug):
        return None
    if len(pivot_cols) != variables:
        return None
    solution = [Fraction(0)] * variables
    for i, col in enumerate(pivot_cols):
        solution[col] = aug[i][variables]
    return solution


def find_garbling(source, target):
    """Find exact K>=0 with K rows stochastic and source*K == target."""
    ns, nt = len(source[0]), len(target[0])
    variables = ns * nt
    equations, rhs = [], []
    for i in range(ns):
        row = [Fraction(int(k // nt == i)) for k in range(variables)]
        equations.append(row)
        rhs.append(Fraction(1))
    for state in range(len(source)):
        for j in range(nt):
            equations.append([
                source[state][i] if k % nt == j else Fraction(0)
                for k in range(variables) for i in [k // nt]
            ])
            rhs.append(target[state][j])

    # A bounded nonempty polytope has a basic feasible point. Enumerate supports
    # up to equality rank; solve each support exactly over Q and check all rows.
    eq_rank = rank(equations)
    for support_size in range(1, min(variables, eq_rank) + 1):
        for support in combinations(range(variables), support_size):
            reduced = [[row[k] for k in support] for row in equations]
            if rank(reduced) != support_size:
                continue
            values = solve_unique(reduced, rhs, support_size)
            if values is None or any(v < 0 for v in values):
                continue
            full = [Fraction(0)] * variables
            for k, value in zip(support, values):
                full[k] = value
            if all(sum(row[k] * full[k] for k in range(variables)) == b
                   for row, b in zip(equations, rhs)):
                return [full[i * nt:(i + 1) * nt] for i in range(ns)]
    return None


def matrix(channel):
    return [[q(cell) for cell in row] for row in channel["kernel"]]


def run(fixture):
    channels = fixture["channels"]
    relations = {}
    for source_name, source in channels.items():
        for target_name, target in channels.items():
            key = f"{source_name}>={target_name}"
            k = find_garbling(matrix(source), matrix(target))
            relations[key] = {
                "feasible": k is not None,
                "garbling": [[[v.numerator, v.denominator] for v in row] for row in k] if k else None,
            }
    return {"schema": "blackwell-candidate-v1", "relations": relations,
            "observations": [list(row["outputs"]) for row in channels.values()]}


if __name__ == "__main__":
    fixture = json.load(open(sys.argv[1], encoding="utf-8"))
    json.dump(run(fixture), open(sys.argv[2], "w", encoding="utf-8"), sort_keys=True, indent=2)
    print("candidate relations:", len(fixture["channels"]) ** 2)
