"""Finite, synthetic preference-explicit choice certificate for Issue #6274."""
import itertools
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results" / "formal-01"


def ordered_partitions(items):
    """Enumerate all weak orders as ordered tiers, best tier first."""
    items = tuple(sorted(items))
    if not items:
        yield ()
        return
    for size in range(1, len(items) + 1):
        for top in itertools.combinations(items, size):
            top = tuple(sorted(top))
            remaining = tuple(item for item in items if item not in top)
            for tail in ordered_partitions(remaining):
                yield (top,) + tail


def ranks(order):
    return {item: tier for tier, group in enumerate(order) for item in group}


def consistent(order, preference):
    rank = ranks(order)
    return (all(rank[a] < rank[b] for a, b in preference["strict"])
            and all(rank[a] == rank[b] for a, b in preference["ties"]))


def project_preference(preference, eligible):
    allowed = set(eligible)
    return {kind: [pair for pair in preference[kind] if pair[0] in allowed and pair[1] in allowed]
            for kind in ("strict", "ties")}


def eligible_routes(fixture, case):
    principals = fixture["principals"]
    eligible, excluded = [], {}
    for route, details in fixture["routes"].items():
        reasons = []
        if details["effect_id"] != fixture["task_effect_id"]:
            reasons.append("requester_effect_mismatch")
        for principal in principals:
            if route not in case["grants"].get(principal, []):
                reasons.append(f"grant_missing:{principal}")
        reasons.extend(f"nontradeable:{item}" for item in case["protected_violations"].get(route, []))
        if reasons:
            excluded[route] = sorted(reasons)
        else:
            eligible.append(route)
    return sorted(eligible), excluded


def enumerate_profile(fixture, case, eligible):
    principals = fixture["principals"]
    extensions = []
    for principal in principals:
        pref = project_preference(case["preferences"][principal], eligible)
        rows = [ranks(order) for order in ordered_partitions(eligible) if consistent(order, pref)]
        if not rows:
            raise ValueError(f"inconsistent preference profile for {principal}")
        extensions.append(rows)
    combos = list(itertools.product(*extensions))
    frontier_rows = []
    for combo in combos:
        frontier = []
        for option in eligible:
            dominated = False
            for rival in eligible:
                if rival == option:
                    continue
                weak_all = all(row[rival] <= row[option] for row in combo)
                strict_some = any(row[rival] < row[option] for row in combo)
                if weak_all and strict_some:
                    dominated = True
                    break
            if not dominated:
                frontier.append(option)
        frontier_rows.append(tuple(frontier))
    possible = sorted(set(itertools.chain.from_iterable(frontier_rows)))
    certain = sorted(set(eligible).intersection(*map(set, frontier_rows))) if frontier_rows else []
    verified_dominated = {}
    verified_undominated = []
    unresolved = []
    for option in eligible:
        dominators = []
        for rival in eligible:
            if rival == option:
                continue
            weak_everywhere = all(all(row[rival] <= row[option] for row in combo)
                                  for combo in combos)
            strict_witness_everywhere = any(
                all(combo[ix][rival] < combo[ix][option] for combo in combos)
                for ix in range(len(principals)))
            if weak_everywhere and strict_witness_everywhere:
                dominators.append(rival)
        if dominators:
            verified_dominated[option] = dominators
            continue
        if all(option in frontier for frontier in frontier_rows):
            verified_undominated.append(option)
        else:
            unresolved.append(option)
    return {
        "extension_counts_by_principal": dict(zip(principals, map(len, extensions), strict=True)),
        "completion_count": len(combos),
        "possible_frontier": possible,
        "certain_frontier": certain,
        "verified_dominated_by": verified_dominated,
        "verified_undominated": sorted(verified_undominated),
        "unresolved": sorted(unresolved),
        "all_completion_frontiers": [list(row) for row in sorted(set(frontier_rows))],
    }


def borda_winner(fixture, case, eligible):
    scores = {route: 0 for route in eligible}
    for principal in fixture["principals"]:
        pref = project_preference(case["preferences"][principal], eligible)
        extensions = [order for order in ordered_partitions(eligible) if consistent(order, pref)]
        if len(extensions) != 1 or any(len(tier) != 1 for tier in extensions[0]):
            return {"status": "NOT_APPLICABLE_PARTIAL_OR_TIED", "scores": None, "winner": None}
        for route, rank in ranks(extensions[0]).items():
            scores[route] += len(eligible) - rank - 1
    best = max(scores.values()) if scores else None
    winners = sorted(route for route, score in scores.items() if score == best)
    return {"status": "DECLARED_EQUAL_WEIGHT_BORDA_BASELINE", "scores": scores,
            "winner": winners[0] if len(winners) == 1 else None, "tied_winners": winners}


def evaluate(fixture, case_name):
    case = fixture["cases"][case_name]
    eligible, excluded = eligible_routes(fixture, case)
    profile = enumerate_profile(fixture, case, eligible) if eligible else {
        "extension_counts_by_principal": {}, "completion_count": 0,
        "possible_frontier": [], "certain_frontier": [], "verified_dominated_by": {},
        "verified_undominated": [], "unresolved": [], "all_completion_frontiers": [],
    }
    requester = fixture["principals"][0]
    fastest = min(eligible, key=lambda route: (fixture["routes"][route]["latency_ms"], route)) if eligible else None
    delegated = case["decision_maker"]
    delegated_choice = None
    if delegated and eligible:
        pref = project_preference(case["preferences"][delegated], eligible)
        pref_orders = [order for order in ordered_partitions(eligible) if consistent(order, pref)]
        if len(pref_orders) == 1 and len(pref_orders[0][0]) == 1:
            delegated_choice = pref_orders[0][0][0]
    if delegated:
        status = "DELEGATED_CHOICE" if delegated_choice else "DELEGATION_UNRESOLVED"
    elif len(profile["possible_frontier"]) > 1:
        status = "HANDOFF_MULTIPLE_OR_POSSIBLE_FRONTIER"
    elif profile["unresolved"]:
        status = "HANDOFF_PARTIAL_PREFERENCE"
    elif profile["possible_frontier"]:
        status = "NO_AUTO_CHOICE_WITHOUT_DECISION_RIGHT"
    else:
        status = "NO_AUTHORIZED_ALTERNATIVE"
    return {
        "case": case_name,
        "eligible": eligible,
        "excluded_reasons": excluded,
        "profile": profile,
        "requester_fastest": fastest,
        "grant_only_admissible": eligible,
        "borda": borda_winner(fixture, case, eligible),
        "decision_status": status,
        "delegated_decision_maker": delegated,
        "delegated_choice": delegated_choice,
    }


def mutate(fixture):
    """Return deliberately invalid variants; the independent auditor must reject each."""
    consent = json.loads(json.dumps(fixture))
    p = consent["cases"]["partial_with_revoked_grant"]["preferences"]["requester"]
    p["ties"].append(["conflict", "review"])  # incorrectly equate joint grant with indifference

    fabricated = json.loads(json.dumps(fixture))
    p = fabricated["cases"]["partial_with_revoked_grant"]["preferences"]["requester"]
    p["strict"].append(["conflict", "review"])  # invent one missing comparison

    veto = json.loads(json.dumps(fixture))
    veto["cases"]["protected_nontradeable"]["protected_violations"] = {}

    unique = evaluate(fixture, "complete_conflict")
    unique["decision_status"] = "UNIQUE_COLLECTIVE_OPTIMUM"
    unique["delegated_choice"] = "review"
    return {"consent_as_indifference": evaluate(consent, "partial_with_revoked_grant"),
            "fabricated_missing_rank": evaluate(fabricated, "partial_with_revoked_grant"),
            "majority_overrides_nontradeable": evaluate(veto, "protected_nontradeable"),
            "undominated_set_called_unique": unique}


def run(fixture):
    cases = {name: evaluate(fixture, name) for name in fixture["cases"]}
    mutations = mutate(fixture)
    protected = fixture["cases"]["protected_nontradeable"]
    majority_preference_count = 0
    all_routes = sorted(fixture["routes"])
    for principal in fixture["principals"]:
        pref = protected["preferences"][principal]
        orders = [order for order in ordered_partitions(all_routes) if consistent(order, pref)]
        if len(orders) == 1 and orders[0][0] == ("quick",):
            majority_preference_count += 1
    return {
        "schema": "preference-explicit-choice-6274-t0-result-v1",
        "method": "exhaustive finite weak-order completion; authorization and nontradeable constraints before preferences",
        "cases": cases,
        "mutation_probes": mutations,
        "summary": {
            "cases": len(cases),
            "complete_conflict_fastest_dominated": "quick" in cases["complete_conflict"]["profile"]["verified_dominated_by"],
            "complete_conflict_frontier": cases["complete_conflict"]["profile"]["possible_frontier"],
            "partial_possible_frontier": cases["partial_with_revoked_grant"]["profile"]["possible_frontier"],
            "partial_certain_frontier": cases["partial_with_revoked_grant"]["profile"]["certain_frontier"],
            "revoked_route_excluded": "d_route" not in cases["partial_with_revoked_grant"]["eligible"],
            "protected_route_excluded": "quick" not in cases["protected_nontradeable"]["eligible"],
            "protected_quick_ranked_first_by": majority_preference_count,
            "delegated_choice": cases["delegated_choice"]["delegated_choice"],
            "equal_profile_frontier": cases["all_equal"]["profile"]["possible_frontier"],
            "equal_profile_unique_choice": cases["all_equal"]["delegated_choice"],
            "mutations": len(mutations),
        },
    }


def main():
    fixture = json.loads((HERE / "fixture.json").read_text(encoding="utf-8"))
    result = run(fixture)
    (OUT / "candidate.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
