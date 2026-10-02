"""Independently authored exhaustive oracle; does not import candidate.py."""

from itertools import chain, combinations


def powerset(items):
    seq = tuple(items)
    return chain.from_iterable(combinations(seq, n) for n in range(len(seq) + 1))


def main():
    tasks = ("cheap_a", "cheap_b", "rare_sentinel")
    costs = (1, 1, 4)
    caps = ({"navigation", "readback"}, {"navigation", "readback"}, {"navigation"})
    matrix = (
        (1, 0, 0, 0, "UNKNOWN"),
        (0, 1, 0, 0, "UNKNOWN"),
        (0, 0, 1, 0, "UNKNOWN"),
    )
    all_sets = list(powerset(range(len(tasks))))
    total_caps = set.union(*caps)
    covers = [s for s in all_sets if set().union(*(caps[i] for i in s)) == total_caps]
    cover_cost = min(sum(costs[i] for i in s) for s in covers)
    cover = min(s for s in covers if sum(costs[i] for i in s) == cover_cost)
    mandatory_columns = (0, 1, 2)
    known_non_equivalent = (0, 1, 2)

    def observed_kill(s, j):
        return any(matrix[i][j] == 1 for i in s)

    safe = [s for s in all_sets if all(observed_kill(s, j) for j in mandatory_columns)]
    detect_cost = min(sum(costs[i] for i in s) for s in safe)
    detect = min(s for s in safe if sum(costs[i] for i in s) == detect_cost)
    same_cost = [s for s in all_sets if sum(costs[i] for i in s) == cover_cost]
    assert len(all_sets) == 8
    assert cover == (0,) and cover_cost == 1
    assert not observed_kill(cover, 2)
    assert detect == (0, 1, 2) and detect_cost == 6
    assert all(observed_kill(detect, j) for j in known_non_equivalent)
    assert matrix[0][4] == matrix[1][4] == matrix[2][4] == "UNKNOWN"
    assert all(not matrix[i][3] for i in range(3))
    assert all(not observed_kill(s, 2) for s in same_cost)
    print({
        "enumerated_subsets": len(all_sets),
        "coverage_only_indices": cover,
        "coverage_only_cost": cover_cost,
        "coverage_only_misses_mandatory_release_loss": True,
        "detection_aware_indices": detect,
        "detection_aware_cost": detect_cost,
        "mandatory_and_known_faults_retained": True,
        "unknown_cells_preserved": 3,
        "equivalent_mutant_not_in_target": True,
        "same_cost_random_support": len(same_cost),
        "same_cost_random_release_retention": sum(observed_kill(s, 2) for s in same_cost),
    })


if __name__ == "__main__":
    main()
