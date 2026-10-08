"""Finite T0 construction for Issue #5797; standard library only."""

from __future__ import annotations

from itertools import combinations


TASKS = ("cheap_a", "cheap_b", "rare_sentinel")
COST = {"cheap_a": 1, "cheap_b": 1, "rare_sentinel": 4}
CAPABILITIES = {
    "cheap_a": frozenset({"navigation", "readback"}),
    "cheap_b": frozenset({"navigation", "readback"}),
    # The emergency sentinel is outside the ordinary capability-coverage
    # objective by design; only its safety constraint makes it mandatory.
    "rare_sentinel": frozenset({"navigation"}),
}
FAULTS = ("wrong_target", "stale_authority", "release_loss", "equivalent_mutant", "unknown_fault")
MANDATORY = frozenset({"wrong_target", "stale_authority", "release_loss"})
# None encodes UNKNOWN, never an observed miss.
KILLS = {
    "cheap_a": {"wrong_target": True, "stale_authority": False, "release_loss": False,
                "equivalent_mutant": False, "unknown_fault": None},
    "cheap_b": {"wrong_target": False, "stale_authority": True, "release_loss": False,
                "equivalent_mutant": False, "unknown_fault": None},
    "rare_sentinel": {"wrong_target": False, "stale_authority": False, "release_loss": True,
                      "equivalent_mutant": False, "unknown_fault": None},
}


def cost(portfolio: tuple[str, ...]) -> int:
    return sum(COST[t] for t in portfolio)


def killed(portfolio: tuple[str, ...], fault: str) -> bool:
    return any(KILLS[t][fault] is True for t in portfolio)


def exhaustive_minima():
    subsets = [tuple(s) for n in range(len(TASKS) + 1) for s in combinations(TASKS, n)]
    coverage = frozenset().union(*(CAPABILITIES[t] for t in TASKS))
    coverage_only = [s for s in subsets if frozenset().union(*(CAPABILITIES[t] for t in s)) == coverage]
    ccost = min(map(cost, coverage_only))
    coverage_winners = [s for s in coverage_only if cost(s) == ccost]
    coverage_choice = min(coverage_winners)
    eligible_faults = tuple(f for f in FAULTS if f != "equivalent_mutant" and
                            any(KILLS[t][f] is True for t in TASKS))
    detection = [s for s in subsets if MANDATORY <= frozenset(f for f in MANDATORY if killed(s, f))
                 and all(killed(s, f) for f in eligible_faults)]
    dcost = min(map(cost, detection))
    detection_choice = min(s for s in detection if cost(s) == dcost)
    return subsets, coverage, coverage_choice, eligible_faults, detection_choice


def run():
    subsets, coverage, coverage_choice, eligible_faults, detection_choice = exhaustive_minima()
    full = TASKS
    random_support = [s for s in subsets if cost(s) == cost(coverage_choice)]
    unknown_preserved = all(KILLS[t]["unknown_fault"] is None for t in TASKS)
    equivalent_excluded = all(not KILLS[t]["equivalent_mutant"] for t in TASKS)
    return {
        "full": {"tasks": list(full), "cost": cost(full), "kills": {f: killed(full, f) for f in FAULTS}},
        "coverage_only": {"tasks": list(coverage_choice), "cost": cost(coverage_choice),
                          "covers": sorted(frozenset().union(*(CAPABILITIES[t] for t in coverage_choice))),
                          "kills": {f: killed(coverage_choice, f) for f in FAULTS}},
        "detection_aware": {"tasks": list(detection_choice), "cost": cost(detection_choice),
                            "eligible_faults": list(eligible_faults),
                            "kills": {f: killed(detection_choice, f) for f in FAULTS}},
        "random_same_cost_support": [{"tasks": list(s), "kills_release_loss": killed(s, "release_loss")}
                                     for s in random_support],
        "mandatory_sentinels": sorted(MANDATORY),
        "unknown_cell_count": sum(KILLS[t][f] is None for t in TASKS for f in FAULTS),
        "unknown_preserved": unknown_preserved,
        "equivalent_mutant_excluded": equivalent_excluded,
        "coverage_negative_control_misses_release_loss": not killed(coverage_choice, "release_loss"),
        "detection_subset_retains_all_mandatory": MANDATORY <= frozenset(f for f in MANDATORY if killed(detection_choice, f)),
        "detection_subset_retains_all_known_detectable": all(killed(detection_choice, f) for f in eligible_faults),
        "subset_count": len(subsets),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=2, sort_keys=True))
