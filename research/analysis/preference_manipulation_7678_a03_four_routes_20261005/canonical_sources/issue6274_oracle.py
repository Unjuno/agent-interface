"""Independent exhaustive oracle for the preference-explicit choice fixture."""
import itertools
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results" / "formal-01"


def all_weak_rankings(options):
    """Generate canonical rank maps from bounded rank vectors, independently of candidate recursion."""
    options = tuple(sorted(options))
    if not options:
        return [{}]
    generated = {}
    for vector in itertools.product(range(len(options)), repeat=len(options)):
        levels = {value: ix for ix, value in enumerate(sorted(set(vector)))}
        mapping = {option: levels[vector[ix]] for ix, option in enumerate(options)}
        generated[tuple(mapping[option] for option in options)] = mapping
    return list(generated.values())


def project(raw, options):
    allowed = set(options)
    return {kind: [(a, b) for a, b in raw[kind] if a in allowed and b in allowed]
            for kind in ("strict", "ties")}


def compatible(rank, relations):
    return (all(rank[a] < rank[b] for a, b in relations["strict"])
            and all(rank[a] == rank[b] for a, b in relations["ties"]))


def audit_profile(fixture, case, eligible):
    actors = fixture["principals"]
    completions = []
    for actor in actors:
        rel = project(case["preferences"][actor], eligible)
        rows = [rank for rank in all_weak_rankings(eligible) if compatible(rank, rel)]
        if not rows:
            raise AssertionError(f"no valid completion for {actor}")
        completions.append(rows)
    joint = list(itertools.product(*completions))
    frontiers = []
    for ranking in joint:
        kept = []
        for x in eligible:
            if not any(y != x and all(actor[y] <= actor[x] for actor in ranking)
                       and any(actor[y] < actor[x] for actor in ranking) for y in eligible):
                kept.append(x)
        frontiers.append(tuple(kept))
    possible = sorted(set(item for f in frontiers for item in f))
    certain = sorted(set(eligible).intersection(*(set(f) for f in frontiers))) if frontiers else []
    dominators = {}
    verified = []
    unresolved = []
    for x in eligible:
        by = []
        for y in eligible:
            if x == y:
                continue
            always_weak = all(all(a[y] <= a[x] for a in joint_row) for joint_row in joint)
            always_strict_for_some = any(
                all(combo[ix][y] < combo[ix][x] for combo in joint)
                for ix in range(len(actors)))
            if always_weak and always_strict_for_some:
                by.append(y)
        if by:
            dominators[x] = by
        elif all(x in f for f in frontiers):
            verified.append(x)
        else:
            unresolved.append(x)
    return {
        "extension_counts_by_principal": dict(zip(actors, map(len, completions), strict=True)),
        "completion_count": len(joint),
        "possible_frontier": possible,
        "certain_frontier": certain,
        "verified_dominated_by": dominators,
        "verified_undominated": sorted(verified),
        "unresolved": sorted(unresolved),
        "all_completion_frontiers": [list(f) for f in sorted(set(frontiers))],
    }


def evaluate(fixture, name):
    case = fixture["cases"][name]
    eligible, excluded = [], {}
    for route, details in fixture["routes"].items():
        why = []
        if details["effect_id"] != fixture["task_effect_id"]:
            why.append("requester_effect_mismatch")
        why.extend(f"grant_missing:{actor}" for actor in fixture["principals"]
                   if route not in case["grants"].get(actor, []))
        why.extend(f"nontradeable:{item}" for item in case["protected_violations"].get(route, []))
        if why:
            excluded[route] = sorted(why)
        else:
            eligible.append(route)
    eligible.sort()
    profile = audit_profile(fixture, case, eligible) if eligible else {
        "extension_counts_by_principal": {}, "completion_count": 0, "possible_frontier": [],
        "certain_frontier": [], "verified_dominated_by": {}, "verified_undominated": [],
        "unresolved": [], "all_completion_frontiers": [],
    }
    quickest = min(eligible, key=lambda r: (fixture["routes"][r]["latency_ms"], r)) if eligible else None
    scores = {r: 0 for r in eligible}
    borda_applicable = bool(eligible)
    for actor in fixture["principals"]:
        rel = project(case["preferences"][actor], eligible)
        maps = [r for r in all_weak_rankings(eligible) if compatible(r, rel)]
        if len(maps) != 1 or len(set(maps[0].values())) != len(eligible):
            borda_applicable = False
        elif borda_applicable:
            for route, pos in maps[0].items():
                scores[route] += len(eligible) - pos - 1
    if borda_applicable:
        top = max(scores.values())
        winners = sorted(r for r, score in scores.items() if score == top)
        borda = {"status": "DECLARED_EQUAL_WEIGHT_BORDA_BASELINE", "scores": scores,
                 "winner": winners[0] if len(winners) == 1 else None, "tied_winners": winners}
    else:
        borda = {"status": "NOT_APPLICABLE_PARTIAL_OR_TIED", "scores": None, "winner": None}
    delegate = case["decision_maker"]
    choice = None
    if delegate:
        rel = project(case["preferences"][delegate], eligible)
        maps = [r for r in all_weak_rankings(eligible) if compatible(r, rel)]
        if len(maps) == 1:
            top_tier = [r for r in eligible if maps[0][r] == 0]
            if len(top_tier) == 1:
                choice = top_tier[0]
    if delegate:
        status = "DELEGATED_CHOICE" if choice else "DELEGATION_UNRESOLVED"
    elif len(profile["possible_frontier"]) > 1:
        status = "HANDOFF_MULTIPLE_OR_POSSIBLE_FRONTIER"
    elif profile["unresolved"]:
        status = "HANDOFF_PARTIAL_PREFERENCE"
    elif profile["possible_frontier"]:
        status = "NO_AUTO_CHOICE_WITHOUT_DECISION_RIGHT"
    else:
        status = "NO_AUTHORIZED_ALTERNATIVE"
    return {"case": name, "eligible": eligible, "excluded_reasons": excluded, "profile": profile,
            "requester_fastest": quickest, "grant_only_admissible": eligible, "borda": borda,
            "decision_status": status, "delegated_decision_maker": delegate,
            "delegated_choice": choice}


def mutated_inputs(fixture):
    consent = json.loads(json.dumps(fixture))
    consent["cases"]["partial_with_revoked_grant"]["preferences"]["requester"]["ties"].append(
        ["conflict", "review"])
    fabricated = json.loads(json.dumps(fixture))
    fabricated["cases"]["partial_with_revoked_grant"]["preferences"]["requester"]["strict"].append(
        ["conflict", "review"])
    veto = json.loads(json.dumps(fixture))
    veto["cases"]["protected_nontradeable"]["protected_violations"] = {}
    return {"consent_as_indifference": (consent, "partial_with_revoked_grant"),
            "fabricated_missing_rank": (fabricated, "partial_with_revoked_grant"),
            "majority_overrides_nontradeable": (veto, "protected_nontradeable")}


def verify(fixture, result):
    errors = []
    expected_cases = {name: evaluate(fixture, name) for name in fixture["cases"]}
    if result.get("schema") != "preference-explicit-choice-6274-t0-result-v1":
        errors.append("schema mismatch")
    if result.get("cases") != expected_cases:
        errors.append("candidate case results differ from independent exhaustive oracle")
    expected_mutants = {name: evaluate(mut_fixture, case_name)
                        for name, (mut_fixture, case_name) in mutated_inputs(fixture).items()}
    rejected = {}
    for name, expected in expected_mutants.items():
        got = result.get("mutation_probes", {}).get(name)
        if got != expected:
            errors.append(f"mutation not reconstructed: {name}")
        correct = expected_cases["partial_with_revoked_grant"] if name in (
            "consent_as_indifference", "fabricated_missing_rank") else expected_cases[
                "protected_nontradeable" if name == "majority_overrides_nontradeable" else "complete_conflict"]
        if expected == correct:
            errors.append(f"mutation ineffective: {name}")
        rejected[name] = got == expected and expected != correct
    unique = result.get("mutation_probes", {}).get("undominated_set_called_unique", {})
    if unique.get("decision_status") != "UNIQUE_COLLECTIVE_OPTIMUM" or unique.get("delegated_choice") != "review":
        errors.append("unique-frontier mutation not present")
    if unique == expected_cases["complete_conflict"]:
        errors.append("unique-frontier mutation was not rejected by comparison")
    rejected["undominated_set_called_unique"] = (
        unique.get("decision_status") == "UNIQUE_COLLECTIVE_OPTIMUM"
        and unique != expected_cases["complete_conflict"])
    expected_summary = {
        "cases": 5,
        "complete_conflict_fastest_dominated": "quick" in expected_cases["complete_conflict"]["profile"]["verified_dominated_by"],
        "complete_conflict_frontier": expected_cases["complete_conflict"]["profile"]["possible_frontier"],
        "partial_possible_frontier": expected_cases["partial_with_revoked_grant"]["profile"]["possible_frontier"],
        "partial_certain_frontier": expected_cases["partial_with_revoked_grant"]["profile"]["certain_frontier"],
        "revoked_route_excluded": "d_route" not in expected_cases["partial_with_revoked_grant"]["eligible"],
        "protected_route_excluded": "quick" not in expected_cases["protected_nontradeable"]["eligible"],
        "protected_quick_ranked_first_by": sum(
            (lambda maps: len(maps) == 1 and
             [r for r in sorted(fixture["routes"]) if maps[0][r] == 0] == ["quick"])(
                [rank for rank in all_weak_rankings(sorted(fixture["routes"]))
                 if compatible(rank, fixture["cases"]["protected_nontradeable"]["preferences"][actor])])
            for actor in fixture["principals"]),
        "delegated_choice": expected_cases["delegated_choice"]["delegated_choice"],
        "equal_profile_frontier": expected_cases["all_equal"]["profile"]["possible_frontier"],
        "equal_profile_unique_choice": expected_cases["all_equal"]["delegated_choice"],
        "mutations": 4,
    }
    if result.get("summary") != expected_summary:
        errors.append("summary differs from raw-fixture reconstruction")
    return {"status": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT",
            "errors": errors, "case_count": len(expected_cases),
            "mutation_controls_rejected": sum(rejected.values()), "mutation_rejections": rejected,
            "expected": expected_summary}


def main():
    fixture = json.loads((HERE / "fixture.json").read_text(encoding="utf-8"))
    result = json.loads((OUT / "candidate.json").read_text(encoding="utf-8"))
    audit = verify(fixture, result)
    (OUT / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": audit["status"], "errors": audit["errors"],
                      "cases": audit["case_count"], "mutation_controls_rejected": audit["mutation_controls_rejected"]},
                     indent=2, sort_keys=True))
    if audit["status"] != "PASS_METHOD_SCOPED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
