#!/usr/bin/env python3
"""Finite authored route comparator for Issue #6109; no external I/O."""
import json
import sys
from pathlib import Path

HARD = ("target", "authority", "semantic", "effect", "release", "unknown")


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def events(case, side):
    paths = []
    for path in case[f"{side}_paths"]:
        row = []
        for raw in path:
            if raw["kind"] == "tau":
                continue
            if raw["kind"] == "diverge":
                row.append(("DIVERGE",))
                continue
            ids = raw.get("ids", {})
            maps = case.get("identity_maps", {}).get(side, {})
            norm_ids = {}
            for kind, opaque in ids.items():
                referents = maps.get(kind, {})
                if opaque not in referents:
                    raise ValueError("HOLD_IDENTITY")
                norm_ids[kind] = referents[opaque]
            for kind in ("target", "authority", "effect"):
                values = list(maps.get(kind, {}).values())
                if len(values) != len(set(values)):
                    raise ValueError("HOLD_IDENTITY")
            row.append({**raw, "norm_ids": norm_ids})
        paths.append(row)
    return paths


def hard_signature(e):
    if e == ("DIVERGE",):
        return e
    normalized_lineage = []
    effect_map = e.get("norm_ids", {}).get("effect")
    raw_lineage = tuple(e.get("lineage", []))
    if raw_lineage:
        normalized_lineage = [effect_map if token in e.get("ids", {}).get("effect", "") else token for token in raw_lineage]
    return (e["kind"], e.get("norm_ids", {}),
            e.get("generation"), e.get("fresh"), tuple(normalized_lineage),
            e.get("release_order"), e.get("semantic", "effect-confirmed"),
            e.get("release", "released-empty"), e.get("unknown", False))


def soft_equal(a, b, bounds, predicate=None, exact=False):
    fields = set(a) & set(b) & {"position", "latency", "appearance"}
    if fields != {"position", "latency", "appearance"}:
        raise ValueError("HOLD_BOUND")
    for field in fields:
        bound = bounds.get(field)
        if not bound:
            raise ValueError("HOLD_BOUND")
        if bound.get("unit") != ({"position": "px", "latency": "ms", "appearance": "score"}[field]):
            raise ValueError("HOLD_UNITS")
        if exact:
            if a[field] != b[field]:
                return False
        elif abs(a[field] - b[field]) > bound["epsilon"]:
            return False
    if predicate:
        field, threshold = predicate["field"], predicate["threshold"]
        eps = bounds[field]["epsilon"]
        # Each entire tolerance interval must remain strictly on one side.
        for value in (a[field], b[field]):
            if abs(value - threshold) <= eps:
                return False
        if (a[field] < threshold) != (b[field] < threshold):
            return False
    return True


def signature_match(a, b, bounds, predicate, exact):
    if hard_signature(a) != hard_signature(b):
        return False
    return soft_equal(a, b, bounds, predicate, exact)


def path_cover(left, right, bounds, predicate, exact):
    # Universal path-set comparison: every path on each side has a matching
    # complete path on the other side; pairwise events are checked in order.
    def covered(source, target):
        for path in source:
            if not any(len(path) == len(other) and all(
                signature_match(x, y, bounds, predicate, exact)
                for x, y in zip(path, other)) for other in target):
                return False
        return True
    return covered(left, right) and covered(right, left)


def classify(case, public):
    try:
        if case.get("unit_override"):
            raise ValueError("HOLD_UNITS")
        left, right = events(case, "left"), events(case, "right")
        bounds = case.get("bounds", public["bounds"])
        predicate = case.get("predicate", public["predicate"])
        exact = path_cover(left, right, bounds, predicate, exact=True)
        approx = path_cover(left, right, bounds, predicate, exact=False)
        if any((x != ("DIVERGE",) and y != ("DIVERGE",)
                and x.get("incarnation") != y.get("incarnation"))
               for lp, rp in zip(left, right) for x, y in zip(lp, rp)):
            return {"exact": exact, "approx": "HOLD_IDENTITY"}
        return {"exact": exact, "approx": "EQUIVALENT" if approx else "DISTINGUISHED"}
    except ValueError as exc:
        return {"exact": False, "approx": str(exc)}


def main():
    public = load(sys.argv[1])
    result = {c["id"]: classify(c, public) for c in public["cases"]}
    print(json.dumps({"schema": "6109.candidate.v2", "cases": result}, sort_keys=True))


if __name__ == "__main__":
    main()
