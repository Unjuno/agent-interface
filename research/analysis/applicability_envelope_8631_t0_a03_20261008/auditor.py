import itertools
import json
import sys
from pathlib import Path

f = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
candidate = json.loads(sys.argv[2])
rows = f["cases"]
train = [r for r in rows if r["split"] == "train"]
positives = [r for r in train if r["outcome"] == "success"]
negatives = [r for r in train if r["outcome"] == "failure"]

# Independently enumerate grammar predicates in reverse implementation order.
fields = [
    ("version", "v1"),
    ("route", "A"),
    ("age", "fresh"),
    ("target_current", True),
]
consistent = []
for width in range(1, len(fields) + 1):
    for selected in itertools.combinations(fields, width):
        def raw_match(r):
            return all(r[field] is value if isinstance(value, bool) else r[field] == value for field, value in selected)
        if all(raw_match(r) for r in positives) and not any(raw_match(r) for r in negatives):
            consistent.append((width, selected))
    if consistent:
        break
minimum = consistent[0][1] if consistent else None

def candidate_matches(r):
    return all(
        r["target_current"] is True if term == "target_current=true" else
        r["age"] == "fresh" if term == "age=fresh" else
        r["route"] == "A" if term == "route=A" else
        r["version"] == "v1" if term == "version=v1" else False
        for term in candidate["learned_conjunction"]
    )

expected_counterexamples = sorted(r["id"] for r in rows if r["split"] in {"falsifier", "heldout"} and candidate_matches(r) and r["outcome"] == "failure")
def stratum(route, age, current):
    group = [r for r in rows if r["route"] == route and r["age"] == age and r["target_current"] is current]
    return "UNKNOWN_SUPPORT" if not any(r["outcome"] == "failure" for r in group) else "OBSERVED_FAILURE"

train_admitted = [r for r in train if candidate_matches(r)]
checks = {
    "minimum_zero_training_error_conjunction": candidate["learned_conjunction"] == ["target_current=true"] and minimum is not None,
    "all_training_positives_covered": len([r for r in train_admitted if r["outcome"] == "success"]) == len(positives),
    "no_training_negative_admitted": not any(r["outcome"] == "failure" for r in train_admitted),
    "counterexamples_reconstructed": candidate["counterexamples"] == expected_counterexamples == ["A3F1", "A3R1"],
    "zero_failure_stale_stratum_unknown": stratum("A", "stale", True) == candidate["support"]["A|stale|1"]["status"] == "UNKNOWN_SUPPORT",
    "empty_route_c_stratum_unknown": stratum("C", "fresh", True) == candidate["support"]["C|fresh|1"]["status"] == "UNKNOWN_SUPPORT",
    "route_b_outcome_shift_exposed": sorted(r["outcome"] for r in rows if r["route"] == "B") == ["failure", "success"] and "A3R1" in expected_counterexamples,
    "irrelevant_noise_invariance": all(candidate_matches({**r, "noise": n}) == candidate_matches(r) for r in rows for n in f["declared_domain"]["noise"]) and candidate["noise_invariant"] is True,
    "diagnostic_only": candidate["authority_effect"] == "none",
    "training_denominator_matches": candidate["train_candidate_n"] == len(train_admitted) == 5,
}
mutations = {
    "omit_in_envelope_failure": not candidate["counterexamples"],
    "erase_unknown_stale": candidate["support"]["A|stale|1"]["status"] != "UNKNOWN_SUPPORT",
    "promote_authority": candidate["authority_effect"] != "none",
    "add_training_negative": any(r["outcome"] == "failure" for r in train_admitted),
}
print(json.dumps({"checks": checks, "controls_rejected": {k: not v for k,v in mutations.items()},
                  "raw_counterexamples": expected_counterexamples, "minimum_conjunction_width": len(minimum) if minimum else None,
                  "error_count": sum(not v for v in checks.values()), "control_error_count": sum(v for v in mutations.values())},
                 sort_keys=True, separators=(",", ":")))
