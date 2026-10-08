"""T5 finite policy model: bind inherited urgency to a real blocker claim."""
import hashlib
import itertools
import json


def decide(case):
    valid = all((
        case["authenticated"],
        case["request_matches"],
        case["target_matches"],
        case["unexpired"],
        case["blocking_edge_exists"],
    ))
    if not valid:
        return case["base_priority"]
    return max(case["base_priority"], min(case["claimed_priority"], case["priority_cap"]))


def main():
    rows = []
    dimensions = (False, True)
    for authenticated, request_matches, target_matches, unexpired, blocking_edge_exists, claimed, cap in itertools.product(
        dimensions, dimensions, dimensions, dimensions, dimensions,
        (1, 2, 3, 4), (2, 3),
    ):
        case = {
            "authenticated": authenticated,
            "request_matches": request_matches,
            "target_matches": target_matches,
            "unexpired": unexpired,
            "blocking_edge_exists": blocking_edge_exists,
            "claimed_priority": claimed,
            "priority_cap": cap,
            "base_priority": 1,
        }
        effective = decide(case)
        should_inherit = all((authenticated, request_matches, target_matches, unexpired, blocking_edge_exists))
        expected = max(1, min(claimed, cap)) if should_inherit else 1
        assert effective == expected
        rows.append({**case, "effective_priority": effective, "inherited": effective > 1})
    assert len(rows) == 2**5 * 4 * 2 == 256
    assert sum(row["inherited"] for row in rows) == 6
    assert all(row["effective_priority"] == 1 for row in rows if not all((
        row["authenticated"], row["request_matches"], row["target_matches"],
        row["unexpired"], row["blocking_edge_exists"],
    )))
    assert all(row["effective_priority"] <= row["priority_cap"] for row in rows)
    payload = {
        "experiment": "issue-5370-t5-bound-urgency-claim",
        "scope": "synthetic finite scheduler-claim policy; no real scheduler or crypto",
        "case_count": len(rows),
        "dimensions": ["authenticated", "request_matches", "target_matches", "unexpired", "blocking_edge_exists", "claimed_priority", "priority_cap"],
        "inherited_cases": sum(row["inherited"] for row in rows),
        "unauthorized_or_unbound_inheritance": sum(row["inherited"] and not all((row["authenticated"], row["request_matches"], row["target_matches"], row["unexpired"], row["blocking_edge_exists"])) for row in rows),
        "all_rows": rows,
    }
    semantic = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload["semantic_sha256"] = hashlib.sha256(semantic.encode()).hexdigest()
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
