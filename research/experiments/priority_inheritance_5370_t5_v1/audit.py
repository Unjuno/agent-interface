"""Independent combinatorial oracle for the T5 raw candidate output."""
import hashlib
import itertools
import json
import sys


def oracle(case):
    eligible = (
        case["authenticated"] is True
        and case["request_matches"] is True
        and case["target_matches"] is True
        and case["unexpired"] is True
        and case["blocking_edge_exists"] is True
    )
    if not eligible:
        return 1
    return max(1, min(case["claimed_priority"], case["priority_cap"]))


def main(path):
    payload = json.load(open(path, encoding="utf-8"))
    claimed_hash = payload.pop("semantic_sha256")
    semantic = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    actual_hash = hashlib.sha256(semantic).hexdigest()
    assert actual_hash == claimed_hash
    rows = payload["all_rows"]
    flags = ("authenticated", "request_matches", "target_matches", "unexpired", "blocking_edge_exists")
    expected = set(itertools.product((False, True), repeat=5))
    observed = [tuple(row[name] for name in flags) for row in rows]
    assert len(rows) == 256
    assert len(set((key, r["claimed_priority"], r["priority_cap"]) for key, r in zip(observed, rows))) == 256
    assert set(observed) == expected
    mismatches = []
    for row in rows:
        value = oracle(row)
        if row["effective_priority"] != value:
            mismatches.append(row)
        assert row["inherited"] is (value > 1)
        assert row["effective_priority"] <= row["priority_cap"]
    assert not mismatches
    inherited = [r for r in rows if r["effective_priority"] > 1]
    assert len(inherited) == 6
    assert all(all(row[k] is True for k in flags) for row in inherited)
    print(json.dumps({
        "status": "PASS_T5_INDEPENDENT_CLAIM_BINDING_ORACLE",
        "rows": len(rows),
        "unique_input_cases": 256,
        "independent_matches": 256,
        "inherited_cases": len(inherited),
        "unauthorized_or_unbound_inheritance": sum(not all(r[k] for k in flags) for r in inherited),
        "max_priority": max(r["effective_priority"] for r in rows),
        "semantic_sha256": actual_hash,
        "errors": [],
    }, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main(sys.argv[1])
