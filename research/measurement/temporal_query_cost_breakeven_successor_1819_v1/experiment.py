from fractions import Fraction
from itertools import product

CLASSES = ("RECENT", "LONG", "EVENT", "REVERSAL")
UNIVERSAL = (11, 11, 11, 11)
CLASS_ONLY = (4, 2, 8, 6)
CLASS_ANCHOR = (4, 2, 2, 2)

def simplex(n=40):
    for a in range(n + 1):
        for b in range(n - a + 1):
            for c in range(n - a - b + 1):
                yield (a, b, c, n - a - b - c)

def mean(v, budget):
    return sum((Fraction(p, 40) * x for p, x in zip(v, budget)), Fraction())

def candidate():
    rows = []
    for v in simplex():
        u, c, a = mean(v, UNIVERSAL), mean(v, CLASS_ONLY), mean(v, CLASS_ANCHOR)
        rows.append({"prior": v, "u": u, "class": c, "anchor": a,
                     "anchor_saving": c-a, "class_saving": u-c,
                     "anchor_total_saving": u-a})
    assert len(rows) == 12341
    assert min(r["class"] for r in rows) == 2
    assert max(r["class"] for r in rows) == 8
    assert min(r["anchor"] for r in rows) == 2
    assert max(r["anchor"] for r in rows) == 4
    assert all(r["anchor_saving"] == Fraction(6*r["prior"][2]+4*r["prior"][3],40) for r in rows)
    assert all((r["anchor_saving"] == 0) == (r["prior"][2] == 0 and r["prior"][3] == 0) for r in rows)
    eq = next(r for r in rows if r["prior"] == (10,10,10,10))
    return rows, eq

def auditor():
    count = 0
    extrema = {"class": [None, None], "anchor": [None, None]}
    zero_equiv = True
    for v in simplex():
        count += 1
        c = sum(Fraction(p, 40)*b for p,b in zip(v, (4,2,8,6)))
        a = sum(Fraction(p, 40)*b for p,b in zip(v, (4,2,2,2)))
        extrema["class"][0] = c if extrema["class"][0] is None else min(extrema["class"][0], c)
        extrema["class"][1] = c if extrema["class"][1] is None else max(extrema["class"][1], c)
        extrema["anchor"][0] = a if extrema["anchor"][0] is None else min(extrema["anchor"][0], a)
        extrema["anchor"][1] = a if extrema["anchor"][1] is None else max(extrema["anchor"][1], a)
        zero_equiv &= ((c-a == 0) == (v[2] == 0 and v[3] == 0))
    return count, extrema, zero_equiv

def main():
    rows, eq = candidate()
    count, extrema, zero_equiv = auditor()
    controls = {}
    controls["budget"] = any(mean(v, (4,2,8,7)) != mean(v, CLASS_ONLY) for v in simplex())
    controls["normalization"] = sum(Fraction(x, 40) for x in (10,10,10,11)) != 1
    controls["event_coefficient"] = all(r["anchor_saving"] != Fraction(4*r["prior"][2]+4*r["prior"][3],40) for r in rows if r["prior"][2])
    controls["reversal_coefficient"] = all(r["anchor_saving"] != Fraction(6*r["prior"][2]+6*r["prior"][3],40) for r in rows if r["prior"][3])
    controls["inequality_direction"] = not (eq["class_saving"] < 6)
    assert all(controls.values())
    assert extrema == {"class": [Fraction(2), Fraction(8)], "anchor": [Fraction(2), Fraction(4)]}
    assert zero_equiv
    print({"rows": len(rows), "extrema": extrema, "equal_prior": eq,
           "thresholds": {"class_only_vs_universal": 6,
                          "anchor_increment": Fraction(5,2),
                          "anchor_vs_universal": Fraction(17,2)},
           "controls": controls, "formal_invocations": 1, "audit_invocations": 1})

if __name__ == "__main__":
    main()
