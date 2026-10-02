#!/usr/bin/env python3
"""Independent continuation-set auditor. Does not import candidate.py."""
import json
import sys
from pathlib import Path


def read(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def expand(case, side):
    result = []
    side_maps = case.get("identity_maps", {}).get(side, {})
    for raw_path in case[side + "_paths"]:
        path = []
        for event in raw_path:
            if event["kind"] == "tau":
                continue
            if event["kind"] == "diverge":
                path.append(("possible-divergence",))
                continue
            ids = {}
            for field, token in event.get("ids", {}).items():
                table = side_maps.get(field, {})
                if token not in table:
                    raise LookupError("HOLD_IDENTITY")
                ids[field] = table[token]
            for table in side_maps.values():
                refs = list(table.values())
                if len(set(refs)) != len(refs):
                    raise LookupError("HOLD_IDENTITY")
            path.append((event, ids))
        result.append(path)
    return result


def event_pair(x, y, eps, unit_override, predicate, strict):
    if x == ("possible-divergence",) or y == ("possible-divergence",):
        return x == y
    a, ai = x
    b, bi = y
    hard_names = ("kind", "incarnation", "generation", "fresh", "release_order", "semantic", "release", "unknown")
    for name in hard_names:
        default = {"semantic": "effect-confirmed", "release": "released-empty", "unknown": False}
        if a.get(name, default.get(name)) != b.get(name, default.get(name)):
            return False
    if ai != bi:
        return False
    lineage_a = [ai.get("effect") if token in a.get("ids", {}).get("effect", "") else token for token in a.get("lineage", [])]
    lineage_b = [bi.get("effect") if token in b.get("ids", {}).get("effect", "") else token for token in b.get("lineage", [])]
    if lineage_a != lineage_b:
        return False
    for field in ("position", "latency", "appearance"):
        if field not in a or field not in b or field not in eps:
            raise LookupError("HOLD_BOUND")
        unit = eps[field]["unit"]
        expected = {"position": "px", "latency": "ms", "appearance": "score"}[field]
        if unit_override.get(field, expected) != expected or unit != expected:
            raise LookupError("HOLD_UNITS")
        delta = abs(a[field] - b[field])
        if strict and delta != 0:
            return False
        if not strict and delta > eps[field]["epsilon"]:
            return False
    if predicate:
        f, t = predicate["field"], predicate["threshold"]
        margin = eps[f]["epsilon"]
        for value in (a[f], b[f]):
            if abs(value - t) <= margin:
                return False
        if (a[f] < t) != (b[f] < t):
            return False
    return True


def continuation_relation(a, b, eps, units, pred, strict):
    # Recursively compare every outgoing choice using existential matches in
    # each direction (finite may/must path-set equivalence, not sampling).
    if not a and not b:
        return True
    if not a or not b:
        return False
    head_a, tail_a = a[0], a[1:]
    head_b, tail_b = b[0], b[1:]
    return event_pair(head_a, head_b, eps, units, pred, strict) and continuation_relation(tail_a, tail_b, eps, units, pred, strict)


def compare(paths_a, paths_b, eps, units, pred, strict):
    def all_covered(src, dst):
        return all(any(continuation_relation(p, q, eps, units, pred, strict) for q in dst) for p in src)
    return all_covered(paths_a, paths_b) and all_covered(paths_b, paths_a)


def main():
    public = read(sys.argv[1])
    out = {}
    for case in public["cases"]:
        units = case.get("unit_override", {})
        eps = case.get("bounds", public["bounds"])
        pred = case.get("predicate", public["predicate"])
        try:
            if units:
                raise LookupError("HOLD_UNITS")
            a, b = expand(case, "left"), expand(case, "right")
            if any(x[0][0].get("incarnation") != y[0][0].get("incarnation")
                   for x, y in zip(a, b) if x and y and x[0] != ("possible-divergence",) and y[0] != ("possible-divergence",)):
                raise LookupError("HOLD_IDENTITY")
            exact = compare(a, b, eps, units, None, True)
            approx = compare(a, b, eps, units, pred, False)
            out[case["id"]] = {"exact": exact, "approx": "EQUIVALENT" if approx else "DISTINGUISHED"}
        except LookupError as exc:
            out[case["id"]] = {"exact": False, "approx": str(exc)}
    print(json.dumps({"schema": "6109.independent-audit.v2", "cases": out}, sort_keys=True))


if __name__ == "__main__":
    main()
