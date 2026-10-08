#!/usr/bin/env python3
"""Finite exact-rational estimability candidate for Issue #7379 T0."""
from fractions import Fraction
from itertools import combinations
from pathlib import Path
import hashlib, json, sys

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def features(config, columns):
    vals = {name: (1 if (config >> i) & 1 else -1)
            for i, name in enumerate(("A", "B", "C"))}
    vals.update({"1": 1, "AB": vals["A"] * vals["B"],
                 "AC": vals["A"] * vals["C"], "BC": vals["B"] * vals["C"],
                 "ABC": vals["A"] * vals["B"] * vals["C"]})
    return [vals[name] for name in columns]

def rref(matrix, width=None):
    a = [[Fraction(x) for x in row] for row in matrix]
    cols = width if width is not None else (len(a[0]) if a else 0)
    pivot_cols, pivot_row = [], 0
    for col in range(cols):
        found = next((r for r in range(pivot_row, len(a)) if a[r][col]), None)
        if found is None:
            continue
        a[pivot_row], a[found] = a[found], a[pivot_row]
        divisor = a[pivot_row][col]
        a[pivot_row] = [x / divisor for x in a[pivot_row]]
        for r in range(len(a)):
            if r != pivot_row and a[r][col]:
                scale = a[r][col]
                a[r] = [x - scale * y for x, y in zip(a[r], a[pivot_row])]
        pivot_cols.append(col)
        pivot_row += 1
        if pivot_row == len(a):
            break
    return a, pivot_cols

def row_witness(x, contrast):
    # Solve X^T alpha = contrast, setting free alpha coordinates to zero.
    equations = [[Fraction(x[i][j]) for i in range(len(x))] + [Fraction(contrast[j])]
                 for j in range(len(contrast))]
    reduced, pivots = rref(equations, len(x))
    for row in reduced:
        if not any(row[:len(x)]) and row[len(x)]:
            return None
    alpha = [Fraction(0) for _ in range(len(x))]
    for r, col in enumerate(pivots):
        if col < len(x):
            alpha[col] = reduced[r][len(x)]
    return alpha

def null_witness(x, contrast):
    reduced, pivots = rref(x, len(contrast))
    free = [j for j in range(len(contrast)) if j not in pivots]
    for free_col in free:
        v = [Fraction(0) for _ in contrast]
        v[free_col] = Fraction(1)
        for r, pivot in enumerate(pivots):
            v[pivot] = -reduced[r][free_col]
        if sum(Fraction(c) * z for c, z in zip(contrast, v)):
            return v
    raise AssertionError("non-estimable contrast has no null-space witness")

def encode(vector):
    return [str(Fraction(x)) for x in vector]

def evaluate(support, feasible, columns, contrast):
    x = [features(config, columns) for config in support]
    alpha = row_witness(x, contrast)
    if alpha is not None:
        status, witness = "ESTIMABLE", {"row_coefficients": encode(alpha)}
    else:
        status, witness = "NOT_ESTIMABLE", {"null_vector": encode(null_witness(x, contrast))}
    absent = sorted(set(feasible) - set(support))
    repair = None
    if status == "NOT_ESTIMABLE":
        for size in range(len(absent) + 1):
            repair = next((list(add) for add in combinations(absent, size)
                           if row_witness(x + [features(c, columns) for c in add], contrast) is not None), None)
            if repair is not None:
                break
    return {"status": status, "witness": witness, "minimum_safe_addition": repair}

def main(spec_path, raw_path, freeze_path):
    spec_bytes = Path(spec_path).read_bytes()
    spec = json.loads(spec_bytes)
    freeze = json.loads(Path(freeze_path).read_text())
    if hashlib.sha256(spec_bytes).hexdigest() != freeze["spec_sha256"]:
        raise SystemExit("frozen spec hash mismatch")
    if sha(__file__) != freeze["candidate_sha256"]:
        raise SystemExit("frozen candidate hash mismatch")
    profiles = spec["model_profiles"]
    contrasts = spec["contrasts"]
    rows = []
    for case, feasible in spec["feasibility_cases"].items():
        feasible = sorted(feasible)
        for mask in range(1 << len(feasible)):
            support = [config for i, config in enumerate(feasible) if (mask >> i) & 1]
            for contrast_name, terms in contrasts.items():
                models = {}
                states = []
                for model_name, columns in profiles.items():
                    vector = [terms.get(column, 0) for column in columns]
                    result = evaluate(support, feasible, columns, vector)
                    models[model_name] = result
                    states.append(result["status"])
                disposition = (states[0] if len(set(states)) == 1 else "UNRESOLVED_MODEL")
                rows.append({"case": case, "feasible": feasible, "support": support,
                             "contrast": contrast_name, "models": models,
                             "disposition": disposition})
    raw = {"schema": "feasibility-estimability-raw-v1",
           "spec_sha256": sha(spec_path), "candidate_sha256": sha(__file__),
           "source_commit": "f11ee9d051239094cf3679e19c80bd7deaed0564",
           "rows": rows}
    Path(raw_path).write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"rows": len(rows), "raw_sha256": sha(raw_path),
                      "dispositions": {k: sum(r["disposition"] == k for r in rows)
                                       for k in ("ESTIMABLE", "NOT_ESTIMABLE", "UNRESOLVED_MODEL")}}, sort_keys=True))

if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: candidate.py SPEC.json RAW.json FREEZE.json")
    main(sys.argv[1], sys.argv[2], sys.argv[3])
