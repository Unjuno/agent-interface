import collections
import copy
import hashlib
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
RAW = HERE / "candidate_raw.json"
RECEIPT = HERE / "audit_receipt.json"
SYMBOLS = ["A0", "A1", "R", "U0", "U1", "Q0", "Q1", "Q0_STALE", "F"]
INITIAL = (0, 0, 0)


def independent_transition(node, op):
    x, y, gone = node
    vals = [x, y]
    if op.startswith("A"):
        who = int(op[-1])
        if gone == 0 and vals[who] == 0:
            vals[who] = 1
    elif op == "R":
        gone = 1
    elif op.startswith("Q") and op != "Q0_STALE":
        who = int(op[-1])
        if vals[who] == 1:
            vals[who] = 2
    elif op == "F":
        vals = [3 if value == 1 else value for value in vals]
    return (vals[0], vals[1], gone)


def reference_graph():
    pending = collections.deque([(INITIAL, ())])
    seen = {INITIAL: ()}
    arcs = 0
    while pending:
        node, trace = pending.popleft()
        for op in SYMBOLS:
            arcs += 1
            child = independent_transition(node, op)
            if child not in seen:
                seen[child] = trace + (op,)
                pending.append((child, trace + (op,)))
    unsafe = []
    stale_effect = 0
    post_remove_allowed = 0
    baseline_post_reclaim_allowed = 0
    for node, trace in seen.items():
        if node[2] and 1 not in node[:2]:  # a valid reclaim point
            for op in ("U0", "U1"):
                reader = node[int(op[-1])]
                if reader == 1:
                    unsafe.append(list(trace + (op,)))
        if node[2]:
            for reader in (0, 1):
                if node[reader] == 1:
                    post_remove_allowed += 1
                    baseline_post_reclaim_allowed += 1
        if independent_transition(node, "Q0_STALE") != node:
            stale_effect += 1
    # Revoke-only baseline calls REMOVE a reclamation while active readers live.
    baseline = next(
        (list(trace + ("U0",)) for node, trace in seen.items()
         if node[2] and node[0] == 1), None
    )
    inventory = [
        {"state": list(node), "events": list(seen[node])}
        for node in sorted(seen)
    ]
    return (len(seen), arcs, unsafe, stale_effect, baseline, inventory,
            post_remove_allowed, baseline_post_reclaim_allowed)


def verify(payload):
    errors = []
    try:
        expected = reference_graph()
        if payload["reachable_state_count"] != expected[0]:
            errors.append("reachable_state_count")
        if payload["transition_count"] != expected[1]:
            errors.append("transition_count")
        if payload["two_phase_reclaim_then_active_use_witnesses"] != expected[2]:
            errors.append("reclaim_counterexamples")
        if payload["stale_receipt_state_changes"] != expected[3]:
            errors.append("stale_receipt_effect")
        if payload["baseline_remove_then_active_use_witness"] != expected[4]:
            errors.append("baseline_counterexample")
        if payload["baseline_allowed_uses_after_declared_reclaim"] <= 0:
            errors.append("baseline_did_not_expose_gap")
        if payload["two_phase_allowed_uses_after_remove"] <= 0:
            errors.append("active_quiescing_reader_not_modeled")
        if payload["shortest_paths"] != expected[5]:
            errors.append("state_path_inventory")
        if payload["two_phase_allowed_uses_after_remove"] != expected[6]:
            errors.append("two_phase_post_remove_use_count")
        if payload["baseline_allowed_uses_after_declared_reclaim"] != expected[7]:
            errors.append("baseline_post_reclaim_use_count")
        if payload["reclaimed_states_with_active_reader"] != 0:
            errors.append("reclaimed_active_state")
    except (KeyError, TypeError, ValueError):
        errors.append("schema_or_type")
    return errors


def main():
    if RECEIPT.exists():
        raise SystemExit("REFUSE_OVERWRITE audit_receipt.json")
    if not RAW.is_file():
        raise SystemExit("STOP_MISSING_CANDIDATE_RAW")
    raw_bytes = RAW.read_bytes()
    result = json.loads(raw_bytes)
    errors = verify(result)
    mutations = []
    for name, mutate in (
        ("state_count", lambda x: x.update(reachable_state_count=x["reachable_state_count"] + 1)),
        ("transition_count", lambda x: x.update(transition_count=x["transition_count"] - 1)),
        ("baseline_witness", lambda x: x.update(baseline_remove_then_active_use_witness=None)),
        ("stale_ack_effect", lambda x: x.update(stale_receipt_state_changes=1)),
        ("unsafe_reclaim", lambda x: x.update(two_phase_reclaim_then_active_use_witnesses=[["A0", "R", "U0"]])),
    ):
        changed = copy.deepcopy(result)
        mutate(changed)
        mutations.append({"name": name, "rejected": bool(verify(changed))})
    status = "PASS_METHOD_SCOPED" if not errors and all(m["rejected"] for m in mutations) else "STOP_AUDIT"
    receipt = {
        "status": status,
        "errors": errors,
        "candidate_raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "independently_recomputed": {
            "reachable_state_count": reference_graph()[0],
            "transition_count": reference_graph()[1],
            "two_phase_allowed_uses_after_remove": reference_graph()[6],
            "baseline_allowed_uses_after_declared_reclaim": reference_graph()[7],
        },
        "mutation_controls": mutations,
        "mutation_controls_rejected": sum(m["rejected"] for m in mutations),
        "mutation_controls_total": len(mutations),
        "scope": "two-reader finite-state protocol only",
    }
    RECEIPT.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(receipt, sort_keys=True))
    if status != "PASS_METHOD_SCOPED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
