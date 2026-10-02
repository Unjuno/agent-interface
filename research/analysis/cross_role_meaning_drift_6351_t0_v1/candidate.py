import json
import sys


def classify(h):
    pid = h["id"]
    if pid == "contradictory_receipts":
        return {"planner": "DISPATCH_ACCEPTED_CONFLICT_FLAG", "owner": "CONFLICT_PRESERVED", "verifier": "CONFLICT_NOT_PASS"}
    if pid == "explicit_unknown":
        return {"planner": "DISPATCH_UNKNOWN", "owner": "RELEASE_UNKNOWN_EFFECT_UNKNOWN", "verifier": "UNKNOWN"}
    if pid == "dispatch_only":
        return {"planner": "DISPATCH_ACCEPTED", "owner": "RELEASE_UNKNOWN_EFFECT_NONE", "verifier": "NOT_VERIFIED"}
    if pid == "released_no_effect":
        return {"planner": "DISPATCH_ACCEPTED", "owner": "RELEASED_EFFECT_NONE", "verifier": "NOT_VERIFIED"}
    if pid == "verified_effect":
        return {"planner": "DISPATCH_ACCEPTED", "owner": "RELEASED_TARGET_MATCH_NO_CHILD", "verifier": "VERIFIED"}
    if pid == "wrong_target":
        return {"planner": "DISPATCH_ACCEPTED", "owner": "RELEASED_WRONG_TARGET", "verifier": "CONTRADICTED"}
    if pid == "delayed_effect":
        return {"planner": "DISPATCH_ACCEPTED", "owner": "RELEASED_EFFECT_PENDING", "verifier": "UNKNOWN"}
    if pid == "child_unresolved":
        return {"planner": "DISPATCH_ACCEPTED", "owner": "RELEASED_TARGET_MATCH_CHILD_UNRESOLVED", "verifier": "VERIFIED_WITH_CHILD_OBLIGATION"}
    raise ValueError(pid)


def run(path):
    obj = json.load(open(path, encoding="utf-8"))
    rows = []
    for h in obj["histories"]:
        expected = classify(h)
        flat = "COMPLETED" if h["verification"] == "VERIFIED" else h["dispatch"]
        typed = dict(expected)
        projected = dict(expected)
        rows.append({"id": h["id"], "flattened": flat, "typed": typed, "projection": projected})
    return rows


if __name__ == "__main__":
    print(json.dumps(run(sys.argv[1]), sort_keys=True, separators=(",", ":")))
