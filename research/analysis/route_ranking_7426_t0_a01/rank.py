import itertools
import json
from fractions import Fraction
from pathlib import Path

OUT = Path(__file__).parent
GRID = [(Fraction(a, 6), Fraction(b, 6), Fraction(c, 6))
        for a in range(7) for b in range(7-a) for c in [6-a-b]]

# Each row: per-stratum vector of three non-safety costs (latency, tokens, recovery).
FIXTURES = {
    "dominance": {"A": [[1, 2, 1], [2, 1, 2], [1, 1, 1]],
                  "B": [[2, 3, 2], [3, 2, 3], [2, 2, 2]]},
    "crossed_tradeoff": {"A": [[1, 4, 3], [4, 1, 3], [3, 3, 3]],
                         "B": [[3, 2, 3], [2, 3, 3], [3, 3, 3]]},
    "task_mix_reversal": {"A": [[1, 4, 3], [4, 1, 3], [3, 3, 3]],
                           "B": [[3, 2, 3], [2, 3, 3], [3, 3, 3]]},
    "value_weight_reversal": {"A": [[1, 4, 3], [1, 4, 3], [1, 4, 3]],
                              "B": [[3, 2, 3], [3, 2, 3], [3, 2, 3]]},
    "missing_stratum": {"A": [[1, 2, 1], [2, None, 2], [1, 1, 1]],
                        "B": [[2, 3, 2], [3, 2, 3], [2, 2, 2]]},
    "hard_gate": {"A": [[1, 1, 1], [1, 1, 1], [1, 1, 1]],
                  "B": [[2, 2, 2], [2, 2, 2], [2, 2, 2]]},
}
GATES = {"A": {"correct_effect": True, "safe_release": True, "evidence_integrity": True},
         "B": {"correct_effect": True, "safe_release": True, "evidence_integrity": True}}

def score(table, p, w):
    total = Fraction(0)
    for si, ps in enumerate(p):
        inner = Fraction(0)
        for ki, wk in enumerate(w):
            cell = table[si][ki]
            if cell is None and ps and wk:
                return None
            if cell is not None:
                inner += wk * cell
        total += ps * inner
    return total

def evaluate(fixture, mix_set=GRID, weight_set=GRID, gates=None):
    gates = gates or GATES
    eligible = [r for r in fixture if all(gates[r].values())]
    if len(eligible) < 2:
        return {"disposition": "HOLD_FEWER_THAN_TWO_ELIGIBLE_ROUTES", "eligible": eligible}
    pairs, missing = [], False
    for p, w in itertools.product(mix_set, weight_set):
        scores = {r: score(fixture[r], p, w) for r in eligible}
        if any(v is None for v in scores.values()):
            missing = True
            continue
        pairs.append({"mix": list(map(str, p)), "weights": list(map(str, w)),
                      "scores": {r: str(v) for r, v in scores.items()},
                      "winner": (min(scores, key=scores.get) if len(set(scores.values())) > 1 else "TIE")})
    if missing:
        return {"disposition": "HOLD_UNIDENTIFIED_OUTCOME", "eligible": eligible,
                "evaluated_pairs": len(pairs), "missing_pairs": len(mix_set)*len(weight_set)-len(pairs)}
    winners = {x["winner"] for x in pairs}
    disposition = "ROBUST_" + next(iter(winners)) if len(winners) == 1 and "TIE" not in winners else "MIXED_OR_TIED_REGION"
    return {"disposition": disposition, "eligible": eligible, "evaluated_pairs": len(pairs),
            "winner_counts": {x: sum(y["winner"] == x for y in pairs) for x in sorted(winners)},
            "fixed_equal_aggregate": next((x for x in pairs if x["mix"] == ["1/3", "1/3", "1/3"] and x["weights"] == ["1/3", "1/3", "1/3"]), None)}

if __name__ == "__main__":
    gates = json.loads(json.dumps(GATES))
    gates["A"]["safe_release"] = False
    results = {}
    for name, fixture in FIXTURES.items():
        if name == "task_mix_reversal":
            results[name] = evaluate(fixture, weight_set=[(Fraction(1),Fraction(0),Fraction(0))])
        elif name == "value_weight_reversal":
            results[name] = evaluate(fixture, mix_set=[(Fraction(1),Fraction(0),Fraction(0))])
        elif name == "hard_gate":
            results[name] = evaluate(fixture, gates=gates)
        else:
            results[name] = evaluate(fixture)
    (OUT / "candidate.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: {"disposition":v["disposition"], "evaluated_pairs":v.get("evaluated_pairs"),
                         "winner_counts":v.get("winner_counts"), "missing_pairs":v.get("missing_pairs"),
                         "eligible":v.get("eligible")} for k,v in results.items()}, indent=2))
