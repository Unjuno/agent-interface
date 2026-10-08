from __future__ import annotations

import itertools
import json


def weak_orders(routes):
    """Enumerate ordered partitions by normalized rank vectors, not recursion."""
    names = tuple(sorted(routes))
    n = len(names)
    found = set()
    for vector in itertools.product(range(n), repeat=n):
        levels = sorted(set(vector))
        if levels != list(range(len(levels))):
            continue
        tiers = tuple(
            tuple(names[i] for i, rank in enumerate(vector) if rank == level)
            for level in levels
        )
        found.add(tiers)
    return sorted(found)


def encoded(order):
    rank = {route: level for level, tier in enumerate(order) for route in tier}
    strict, ties = [], []
    names = sorted(rank)
    for i, left in enumerate(names):
        for right in names[i + 1:]:
            if rank[left] < rank[right]:
                strict.append([left, right])
            elif rank[right] < rank[left]:
                strict.append([right, left])
            else:
                ties.append([left, right])
    return {"strict": sorted(strict), "ties": sorted(ties)}


def order_key(order):
    return json.dumps([list(t) for t in order], separators=(",", ":"))


def is_consistent(order, preference):
    rank = {route: level for level, tier in enumerate(order) for route in tier}
    return (
        all(rank[a] < rank[b] for a, b in preference["strict"])
        and all(rank[a] == rank[b] for a, b in preference["ties"])
    )


def projected(preference, eligible):
    allowed = set(eligible)
    return {
        "strict": [p for p in preference["strict"] if p[0] in allowed and p[1] in allowed],
        "ties": [p for p in preference["ties"] if p[0] in allowed and p[1] in allowed],
    }


def certificate(fixture, preferences, decision_maker=None, grants=None, protected=None):
    principals = fixture["principals"]
    routes = sorted(fixture["routes"])
    grants = grants or {p: list(routes) for p in principals}
    protected = protected or {}
    eligible, excluded = [], {}
    for route, details in fixture["routes"].items():
        reasons = []
        if details["effect_id"] != fixture["task_effect_id"]:
            reasons.append("requester_effect_mismatch")
        for principal in principals:
            if route not in grants.get(principal, []):
                reasons.append(f"grant_missing:{principal}")
        reasons.extend(f"nontradeable:{x}" for x in protected.get(route, []))
        if reasons:
            excluded[route] = sorted(reasons)
        else:
            eligible.append(route)
    eligible.sort()

    projected_prefs = {p: projected(preferences[p], eligible) for p in principals}
    orders = weak_orders(eligible)
    extensions = {
        p: [o for o in orders if is_consistent(o, projected_prefs[p])]
        for p in principals
    }
    if eligible and any(not extensions[p] for p in principals):
        raise ValueError("empty preference completion")
    combinations = list(itertools.product(*(extensions[p] for p in principals))) if eligible else []

    completion_frontiers = []
    for combo in combinations:
        ranks = [
            {route: level for level, tier in enumerate(order) for route in tier}
            for order in combo
        ]
        frontier = []
        for option in eligible:
            dominated = any(
                rival != option
                and all(row[rival] <= row[option] for row in ranks)
                and any(row[rival] < row[option] for row in ranks)
                for rival in eligible
            )
            if not dominated:
                frontier.append(option)
        completion_frontiers.append(tuple(frontier))

    possible = sorted({route for f in completion_frontiers for route in f})
    certain = sorted(set(eligible).intersection(*map(set, completion_frontiers))) if completion_frontiers else []
    dominated_by, undominated, unresolved = {}, [], []
    for option in eligible:
        dominators = []
        for rival in eligible:
            if rival == option:
                continue
            weak_everywhere = all(
                all(
                    {r: level for level, tier in enumerate(order) for r in tier}[rival]
                    <= {r: level for level, tier in enumerate(order) for r in tier}[option]
                    for order in combo
                )
                for combo in combinations
            )
            strict_witness_everywhere = any(
                all(
                    {r: level for level, tier in enumerate(combo[ix]) for r in tier}[rival]
                    < {r: level for level, tier in enumerate(combo[ix]) for r in tier}[option]
                    for combo in combinations
                )
                for ix in range(len(principals))
            )
            if weak_everywhere and strict_witness_everywhere:
                dominators.append(rival)
        if dominators:
            dominated_by[option] = dominators
        elif all(option in f for f in completion_frontiers):
            undominated.append(option)
        else:
            unresolved.append(option)

    fastest = min(eligible, key=lambda r: (fixture["routes"][r]["latency_ms"], r)) if eligible else None
    delegated_choice = None
    if decision_maker and eligible:
        delegate_orders = extensions[decision_maker]
        if len(delegate_orders) == 1 and len(delegate_orders[0][0]) == 1:
            delegated_choice = delegate_orders[0][0][0]
    if decision_maker:
        status = "DELEGATED_CHOICE" if delegated_choice else "DELEGATION_UNRESOLVED"
    elif len(possible) > 1:
        status = "HANDOFF_MULTIPLE_OR_POSSIBLE_FRONTIER"
    elif unresolved:
        status = "HANDOFF_PARTIAL_PREFERENCE"
    elif possible:
        status = "NO_AUTO_CHOICE_WITHOUT_DECISION_RIGHT"
    else:
        status = "NO_AUTHORIZED_ALTERNATIVE"

    scores = {route: 0 for route in eligible}
    borda_applicable = True
    for principal in principals:
        rows = extensions[principal]
        if len(rows) != 1 or any(len(tier) != 1 for tier in rows[0]):
            borda_applicable = False
            break
        for level, tier in enumerate(rows[0]):
            scores[tier[0]] += len(eligible) - level - 1
    if not borda_applicable:
        borda = {"status": "NOT_APPLICABLE_PARTIAL_OR_TIED", "scores": None, "winner": None}
    else:
        best = max(scores.values()) if scores else None
        winners = sorted(r for r, score in scores.items() if score == best)
        borda = {
            "status": "DECLARED_EQUAL_WEIGHT_BORDA_BASELINE",
            "scores": scores,
            "winner": winners[0] if len(winners) == 1 else None,
            "tied_winners": winners,
        }
    return {
        "eligible": eligible,
        "excluded_reasons": excluded,
        "extension_counts_by_principal": {p: len(extensions[p]) for p in principals} if eligible else {},
        "completion_count": len(combinations),
        "possible_frontier": possible,
        "certain_frontier": certain,
        "verified_dominated_by": dominated_by,
        "verified_undominated": sorted(undominated),
        "unresolved": sorted(unresolved),
        "all_completion_frontiers": [list(f) for f in sorted(set(completion_frontiers))],
        "requester_fastest": fastest,
        "grant_only_admissible": eligible,
        "borda": borda,
        "decision_status": status,
        "delegated_decision_maker": decision_maker,
        "delegated_choice": delegated_choice,
    }


def signature(result):
    return {k: result[k] for k in (
        "eligible", "excluded_reasons", "extension_counts_by_principal",
        "completion_count", "possible_frontier", "certain_frontier",
        "verified_dominated_by", "verified_undominated", "unresolved",
        "all_completion_frontiers", "decision_status",
        "delegated_decision_maker", "delegated_choice",
    )}
