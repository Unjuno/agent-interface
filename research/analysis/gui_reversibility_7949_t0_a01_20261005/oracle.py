"""Independent exhaustive sequence-enumeration oracle; no candidate imports."""
from itertools import product


def enumerate_word(alphabet, length):
    if length == 0:
        return [()]
    return list(product(alphabet, repeat=length))


def words(alphabet, bound):
    found = []
    for size in range(bound + 1):
        found.extend(enumerate_word(alphabet, size))
    return found


def execute(transitions, word, start):
    state = start
    visited = [start]
    for op in word:
        state = transitions.get(op, {}).get(state, state)
        visited.append(state)
    return state, visited


def evaluate(case, model):
    if case.get("coverage_complete") is not True:
        return {"id": case["id"], "label": "UNKNOWN", "reason": "coverage_not_certified", "enumeration": []}
    if case.get("receipt_valid") is not True:
        return {"id": case["id"], "label": "UNKNOWN", "reason": "receipt_not_current", "enumeration": []}
    declared = model["schemas"].get(case["schema"], [])
    starts = case["outcomes"]
    if any(s not in declared for s in starts):
        return {"id": case["id"], "label": "UNKNOWN", "reason": "case_contains_undeclared_state", "enumeration": []}

    trans = model["recovery"][case["recovery_table"]]
    alphabet = list(trans.keys())
    target = model["target"]
    all_words = words(alphabet, model["horizon"])
    enumeration = []
    reachable = {s: [] for s in starts}
    for start in starts:
        for word in all_words:
            final, visits = execute(trans, word, start)
            enumeration.append({"start": start, "word": list(word), "visited": visits, "final": final})
            if final == target:
                reachable[start].append(list(word))
    if any(not reachable[s] for s in starts):
        return {"id": case["id"], "label": "PARTIALLY_RECOVERABLE", "reason": "enumerated_start_without_target_word", "enumeration": enumeration}

    joint = []
    for word in all_words:
        if all(execute(trans, word, s)[0] == target for s in starts):
            joint.append(list(word))
    if joint:
        return {"id": case["id"], "label": "UNIVERSALLY_UNIFORM", "reason": "enumerated_joint_word", "joint_words": joint, "enumeration": enumeration}

    buckets = {}
    for start in starts:
        bucket = case.get("receipt_classes", {}).get(start)
        if bucket is None:
            return {"id": case["id"], "label": "UNKNOWN", "reason": "missing_receipt_bucket", "enumeration": enumeration}
        buckets.setdefault(bucket, []).append(start)
    plan_by_bucket = {}
    for bucket, members in buckets.items():
        bucket_words = [list(word) for word in all_words if all(execute(trans, word, s)[0] == target for s in members)]
        if not bucket_words:
            return {"id": case["id"], "label": "UNKNOWN", "reason": "receipt_bucket_has_no_joint_word", "enumeration": enumeration}
        plan_by_bucket[str(bucket)] = bucket_words
    return {"id": case["id"], "label": "UNIVERSALLY_BRANCHING", "reason": "enumerated_receipt_bucket_words", "plans": plan_by_bucket, "enumeration": enumeration}


def run(model):
    return [evaluate(case, model) for case in model["cases"]]
