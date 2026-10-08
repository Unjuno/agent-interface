"""Independent oracle audit for the finite T6 raw output."""
import itertools
import hashlib
import json
import sys


def oracle(case):
    if case["probe_state"] != "VALID":
        return "YIELD" if case["fallback"] == "YIELD" else "TASK_ACTION"
    if case["harm"] > case["budget"]:
        return "YIELD"
    if case["probe_cost"] > 1:
        return "TASK_ACTION"
    return "PROBE"


def main(path):
    payload = json.load(open(path, encoding="utf-8"))
    rows = payload["all_rows"]
    semantic_payload = dict(payload)
    claimed_semantic_sha = semantic_payload.pop("semantic_sha256")
    recomputed_semantic_sha = hashlib.sha256(
        json.dumps(semantic_payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    assert claimed_semantic_sha == recomputed_semantic_sha
    keys = [(r["target"], r["probe_state"], r["probe_cost"], r["harm"],
             r["budget"], r["fallback"]) for r in rows]
    expected = set(itertools.product(("A", "B"), ("VALID", "FAILED", "UNKNOWN", "STALE"),
                                     (0, 1, 2), (0, 1, 2), (0, 1, 2), ("YIELD", "TASK")))
    assert len(rows) == 432 and len(set(keys)) == 432 and set(keys) == expected
    for r in rows:
        assert r["decision"] == oracle(r)
        assert r["authority"] is False
        assert r["wrong_target"] == (r["decision"] == "TASK_ACTION" and r["target"] == "B")
        assert r["effect"] == ("COMMIT_A" if r["decision"] == "TASK_ACTION" else "NONE")
        if r["probe_state"] != "VALID" or r["harm"] > r["budget"] or r["probe_cost"] > 1:
            assert r["decision"] != "PROBE"
    failed = [r for r in rows if r["probe_state"] == "FAILED"]
    task = [r for r in failed if r["fallback"] == "TASK"]
    yielding = [r for r in failed if r["fallback"] == "YIELD"]
    assert len(task) == len(yielding) == 54
    assert sum(r["wrong_target"] for r in task) == 27
    assert sum(r["wrong_target"] for r in yielding) == 0
    print(json.dumps({"status": "PASS_T6_INDEPENDENT_FINITE_ORACLE",
                      "rows": len(rows), "unique_cases": len(set(keys)),
                      "independent_row_matches": len(rows),
                      "semantic_sha256": recomputed_semantic_sha,
                      "failed_probe_task_fallback_wrong_target": 27,
                      "failed_probe_yield_wrong_target": 0,
                      "authority_grants": 0,
                      "errors": []}, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main(sys.argv[1])
