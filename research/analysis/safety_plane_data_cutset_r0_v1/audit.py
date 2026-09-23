from __future__ import annotations

import argparse
import base64
import copy
import gzip
import itertools
import json
from pathlib import Path

VERTICES = ("s", "d0", "d1", "a0", "a1", "r")
DATA = ("d0", "d1")
FORWARD_EDGES = tuple(
    (VERTICES[i], VERTICES[j])
    for i in range(len(VERTICES))
    for j in range(i + 1, len(VERTICES))
)
GRAPH_COUNT = 1 << len(FORWARD_EDGES)
PASS_DECISION = "PASS_SAFETY_PLANE_DATA_CUTSET_THEOREM_SCOPED"


def decode_rows(path: Path) -> list[dict[str, object]]:
    b64 = path.read_bytes().strip()
    raw = gzip.decompress(base64.b64decode(b64, validate=True))
    return json.loads(raw)


def edges(mask: int):
    return tuple(edge for i, edge in enumerate(FORWARD_EDGES) if mask & (1 << i))


def reaches(mask: int, failed: frozenset[str]) -> bool:
    es = edges(mask)
    frontier = ["s"]
    seen = {"s"}
    while frontier:
        node = frontier.pop(0)
        if node == "r":
            return True
        for a, b in es:
            if a == node and a not in failed and b not in failed and b not in seen:
                seen.add(b)
                frontier.append(b)
    return "r" in seen


def subsets(max_size=None):
    for n in range(3):
        if max_size is not None and n > max_size:
            continue
        for c in itertools.combinations(DATA, n):
            yield frozenset(c)


def expected_row(mask: int):
    cut = None
    for f in subsets():
        if not reaches(mask, f):
            cut = len(f)
            break
    arbitrary = all(reaches(mask, f) for f in subsets())
    out = {
        "mask": mask,
        "base_reachable": reaches(mask, frozenset()),
        "min_data_cut": cut,
        "arbitrary_oracle": arbitrary,
        "arbitrary_theorem": reaches(mask, frozenset(DATA)),
    }
    for k in (0, 1, 2):
        oracle = all(reaches(mask, f) for f in subsets(k))
        out[f"k{k}_oracle"] = oracle
        out[f"k{k}_theorem"] = (cut is None) or cut > k
    return out


def control_expectations():
    return {
        "COUPLED_SINGLE_DATA": {"min_data_cut": 1, "arbitrary": False, "k0": True, "k1": False, "k2": False},
        "DIRECT_SAFETY_PATH": {"min_data_cut": None, "arbitrary": True, "k0": True, "k1": True, "k2": True},
        "TWO_DATA_ROUTES": {"min_data_cut": 2, "arbitrary": False, "k0": True, "k1": True, "k2": False},
    }


def audit(rows, result):
    errors = []
    masks = [r.get("mask") for r in rows]
    if len(rows) != GRAPH_COUNT:
        errors.append(f"row_count:{len(rows)}")
    if masks != list(range(GRAPH_COUNT)):
        errors.append("mask_coverage_or_order")
    row_mismatch = 0
    for i, r in enumerate(rows):
        if i >= GRAPH_COUNT:
            row_mismatch += 1
            continue
        if r != expected_row(i):
            row_mismatch += 1
    if row_mismatch:
        errors.append(f"row_mismatch:{row_mismatch}")

    if result.get("decision") != PASS_DECISION:
        errors.append("decision")
    if result.get("arbitrary_mismatch") != 0:
        errors.append("reported_arbitrary_mismatch")
    if result.get("k_mismatch") != {"0": 0, "1": 0, "2": 0}:
        errors.append("reported_k_mismatch")
    controls = {c.get("name"): c for c in result.get("controls", [])}
    expected_controls = control_expectations()
    if set(controls) != set(expected_controls):
        errors.append("control_names")
    else:
        for name, expected in expected_controls.items():
            c = controls[name]
            if c.get("expected") != expected or c.get("observed") != expected or c.get("pass") is not True:
                errors.append(f"control:{name}")
    return errors


def mutation_controls(rows, result):
    outcomes = {}

    x = copy.deepcopy(rows)
    x[0]["arbitrary_theorem"] = not x[0]["arbitrary_theorem"]
    outcomes["flip_reachability"] = bool(audit(x, result))

    x = copy.deepcopy(rows)
    x[-1]["min_data_cut"] = 0 if x[-1]["min_data_cut"] is None else None
    outcomes["alter_min_cut"] = bool(audit(x, result))

    x = copy.deepcopy(rows[:-1])
    outcomes["drop_row"] = bool(audit(x, result))

    y = copy.deepcopy(result)
    for c in y["controls"]:
        if c["name"] == "TWO_DATA_ROUTES":
            c["observed"]["k1"] = False
            break
    outcomes["alter_control"] = bool(audit(rows, y))
    return outcomes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", required=True)
    ap.add_argument("--result", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rows = decode_rows(Path(a.rows))
    result = json.loads(Path(a.result).read_text())
    errors = audit(rows, result)
    mutations = mutation_controls(rows, result)
    out = {
        "decision": "PASS" if not errors and all(mutations.values()) else "FAIL",
        "errors": errors,
        "mutation_controls": mutations,
        "mutation_controls_detected": sum(mutations.values()),
        "mutation_controls_expected": len(mutations),
        "rows": len(rows),
    }
    Path(a.out).write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    if out["decision"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
