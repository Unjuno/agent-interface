#!/usr/bin/env python3
"""Small exact-count bivariate Williams–Beer I_min PID candidate."""
import json
import hashlib
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def mi(joint, left, right):
    n = sum(joint.values())
    ml, mr = Counter(), Counter()
    for pair, count in joint.items():
        ml[pair[0]] += count
        mr[pair[1]] += count
    value = 0.0
    for (a, b), count in joint.items():
        p = count / n
        value += p * math.log2((count * n) / (ml[a] * mr[b]))
    return value


def pid(case):
    table = Counter()
    for row in case["counts"]:
        if type(row.get("count")) is not int or row["count"] <= 0:
            raise ValueError("counts must be positive exact integers")
        if any(type(row.get(k)) is not int for k in ("x1", "x2", "y")):
            raise ValueError("variables must be exact integers")
        table[(row["x1"], row["x2"], row["y"])] += row["count"]
    n = sum(table.values())
    x1y = Counter(); x2y = Counter(); xy = Counter(); x1 = Counter(); x2 = Counter(); yy = Counter()
    for (a, b, y), count in table.items():
        x1y[(a, y)] += count
        x2y[(b, y)] += count
        xy[((a, b), y)] += count
        x1[a] += count; x2[b] += count; yy[y] += count
    mi1 = mi(x1y, "x", "y")
    mi2 = mi(x2y, "x", "y")
    mij = mi(xy, "x", "y")
    red = 0.0
    for y, ny in yy.items():
        p_y = ny / n
        specifics = []
        for values, marginal in ((x1y, x1), (x2y, x2)):
            specific = 0.0
            for (x, target), count in values.items():
                if target == y:
                    p_x_given_y = count / ny
                    p_x = marginal[x] / n
                    specific += p_x_given_y * math.log2(p_x_given_y / p_x)
            specifics.append(specific)
        red += p_y * min(specifics)
    u1 = mi1 - red
    u2 = mi2 - red
    syn = mij - red - u1 - u2
    return {"redundancy": red, "unique_x1": u1, "unique_x2": u2, "synergy": syn, "joint_mi": mij}


def main():
    fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
    if fixture["sources"] != ["x1", "x2"] or fixture["target"] != "y":
        raise ValueError("frozen source/target identity mismatch")
    rows = [{"id": case["id"], "counts": case["counts"], "atoms": pid(case)} for case in fixture["cases"]]
    output = {
        "schema": "issue7712_pid_t0_result_v1",
        "sources": fixture["sources"],
        "target": fixture["target"],
        "fixture_sha256": hashlib.sha256((ROOT / "fixture.json").read_bytes()).hexdigest(),
        "candidate_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "rows": rows,
    }
    (ROOT / "raw.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"case_count": len(rows), "result": "candidate_complete"}))


if __name__ == "__main__":
    main()
