from fractions import Fraction
from itertools import product
import json

CLASSES = ("RECENT", "LONG", "EVENT", "REVERSAL")
CLASS_ONLY = (4, 2, 8, 6)
CLASS_ANCHOR = (4, 2, 2, 2)
UNIVERSAL = 11
DENOMINATOR = 40

def priors():
    for a in range(DENOMINATOR + 1):
        for b in range(DENOMINATOR - a + 1):
            for c in range(DENOMINATOR - a - b + 1):
                yield (a, b, c, DENOMINATOR - a - b - c)

def mean(budget, p):
    return sum(Fraction(x * w, DENOMINATOR) for x, w in zip(budget, p))

def run():
    rows = list(priors())
    assert len(rows) == 12341
    class_means = [mean(CLASS_ONLY, p) for p in rows]
    anchor_means = [mean(CLASS_ANCHOR, p) for p in rows]
    anchor_savings = [c - a for c, a in zip(class_means, anchor_means)]
    equal = (10, 10, 10, 10)
    result = {
        "formal_invocations": 1,
        "prior_count": len(rows),
        "class_only_extrema": [str(min(class_means)), str(max(class_means))],
        "class_anchor_extrema": [str(min(anchor_means)), str(max(anchor_means))],
        "anchor_saving_zero_iff_event_reversal_zero": all(
            (s == 0) == (p[2] == 0 and p[3] == 0)
            for p, s in zip(rows, anchor_savings)
        ),
        "equal_prior": {
            "class_only_vs_universal": str(Fraction(11) - mean(CLASS_ONLY, equal)),
            "anchor_vs_class_only": str(mean(CLASS_ONLY, equal) - mean(CLASS_ANCHOR, equal)),
            "anchor_vs_universal": str(Fraction(11) - mean(CLASS_ANCHOR, equal)),
        },
        "all_affine_identities": all(
            mean(CLASS_ONLY, p) == Fraction(4*p[0] + 2*p[1] + 8*p[2] + 6*p[3], DENOMINATOR)
            and mean(CLASS_ANCHOR, p) == Fraction(4*p[0] + 2*p[1] + 2*p[2] + 2*p[3], DENOMINATOR)
            for p in rows
        ),
    }
    result["pass"] = (
        result["prior_count"] == 12341
        and result["class_only_extrema"] == ["2", "8"]
        and result["class_anchor_extrema"] == ["2", "4"]
        and result["anchor_saving_zero_iff_event_reversal_zero"]
        and result["equal_prior"] == {
            "class_only_vs_universal": "6",
            "anchor_vs_class_only": "5/2",
            "anchor_vs_universal": "17/2",
        }
        and result["all_affine_identities"]
    )
    return result

if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
