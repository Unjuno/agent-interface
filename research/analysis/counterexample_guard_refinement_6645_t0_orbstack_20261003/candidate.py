"""Finite candidate for Issue #6645; intentionally no runtime integration."""
from itertools import combinations


def minimal_refinements(fixture):
    training = [row for row in fixture["cases"] if row.get("training")]
    if (len(training) != 1 or training[0]["classification"] != "REAL_GUARD_MISS"
            or not training[0]["replay_authenticated"] or not training[0]["coverage_complete"]):
        raise ValueError("training counterexample lacks authenticated in-envelope lineage")
    ce = training[0]
    vocabulary = fixture["predicate_vocabulary"]
    rejected = [p for p in vocabulary if ce["features"][p] is False]
    # Preserve every equally small observable refinement; never consult hidden
    # oracle labels or choose a tie using fixture truth.
    options = [list(group) for size in range(1, len(vocabulary) + 1)
               for group in combinations(vocabulary, size)
               if any(p in rejected for p in group)]
    minimum = min(map(len, options))
    return [option for option in options if len(option) == minimum]


def run(fixture):
    alternatives = minimal_refinements(fixture)
    changed = sorted({p for option in alternatives for p in option})
    rows = []
    for case in fixture["cases"]:
        f = case["features"]
        original_ok = all(f[p] for p in fixture["original_guard"])
        if not original_ok:
            decision = "REFUSE_ORIGINAL_GUARD"
        elif not case["coverage_complete"]:
            decision = "UNKNOWN_FALLBACK" if case["fallback_available"] else "STOP_NO_FALLBACK"
        elif all(all(f[p] for p in option) for option in alternatives):
            decision = "ADMIT"
        else:
            decision = "UNKNOWN_FALLBACK" if case["fallback_available"] else "STOP_NO_FALLBACK"
        rows.append({"id": case["id"], "decision": decision,
                     "task_input_replayed": False,
                     "new_authority": False})
    dependencies = fixture["dependencies"]
    invalidated = {name: bool(set(predicates) & set(changed))
                   for name, predicates in dependencies.items()}
    return {"schema": "unjuno.counterexample-guard-refinement.raw.v1",
            "allocation_id": "CGREF-6645-T0-ORB-20261003-01",
            "refinement_alternatives": alternatives,
            "changed_predicates": changed,
            "rows": rows,
            "cache_invalidation": invalidated,
            "task_input_replayed": False,
            "new_authority": False}
