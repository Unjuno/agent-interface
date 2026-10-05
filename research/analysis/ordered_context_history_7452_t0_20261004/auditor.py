"""Independent raw-only denominator and mutation auditor."""
import itertools
import json
import sys
from pathlib import Path

CONTEXTS = set(itertools.product((0, 1), repeat=3))
EVENTS = ("OBSERVE", "REVOKE", "ACT", "RELEASE")


def legal(history):
    if not 1 <= len(history) <= 3 or any(x not in EVENTS for x in history):
        return False
    acts = releases = 0
    for x in history:
        if x == "ACT":
            if releases:
                return False
            acts += 1
        elif x == "RELEASE":
            if not acts or releases:
                return False
            releases += 1
    return True


PAIRS = {(a, b) for a in EVENTS for b in EVENTS if legal((a, b))}
CONTEXT_PAIRS = set(itertools.product((0, 1), repeat=2))
EXPECTED_MIXED = {(f, s, 0, a, b) for f, s in CONTEXT_PAIRS for a, b in PAIRS}


def audit(raw):
    errors = []
    rows = raw.get("rows")
    if not isinstance(rows, list):
        return ["rows-not-list"]
    parsed = {"mixed_occ": [], "separate_equal_budget": []}
    seen = set()
    for i, row in enumerate(rows):
        try:
            suite, c, h = row["suite"], tuple(row["context"]), tuple(row["history"])
        except (KeyError, TypeError):
            errors.append(f"row-{i}-malformed")
            continue
        if suite not in parsed or c not in CONTEXTS or not legal(h):
            errors.append(f"row-{i}-outside-independent-universe")
            continue
        key = (suite, c, h)
        if key in seen:
            errors.append(f"row-{i}-duplicate")
        seen.add(key)
        parsed[suite].append((c, h))
    mixed = {(c[0], c[1], c[2], h[0], h[1])
             for c, h in parsed["mixed_occ"] if len(h) == 2}
    if mixed != EXPECTED_MIXED:
        errors.append("mixed-denominator-mismatch")
    baseline = parsed["separate_equal_budget"]
    if len(baseline) != len(parsed["mixed_occ"]):
        errors.append("unequal-budget")
    predicates = {
        "joint": lambda c, h: c[0] == c[1] == 1 and h == ("REVOKE", "ACT"),
        "factor": lambda c, h: c[0] == 1 and h == ("OBSERVE", "OBSERVE"),
        "order": lambda c, h: h == ("REVOKE", "ACT"),
        "order_invariant": lambda c, h: c[1] == 1,
    }
    detects = {name: {suite: any(fn(c, h) for c, h in cases)
                      for suite, cases in parsed.items()}
               for name, fn in predicates.items()}
    return {
        "legal_pair_denominator": len(PAIRS),
        "mixed_expected_rows": len(EXPECTED_MIXED),
        "exhaustive_context_pair_rows": len(CONTEXTS) * len(PAIRS),
        "mixed_rows": len(parsed["mixed_occ"]),
        "separate_equal_budget_rows": len(baseline),
        "coverage_exact": mixed == EXPECTED_MIXED,
        "detects": detects,
        "errors": errors,
        "scope": "synthetic finite method only; not a GUI safety or reliability result",
    }


def main(src, dest):
    result = audit(json.loads(Path(src).read_text(encoding="utf-8")))
    Path(dest).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1], sys.argv[2]), indent=2))
