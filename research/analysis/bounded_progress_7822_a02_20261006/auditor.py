"""Independent exhaustive-set audit; deliberately does not import candidate.py."""
import copy
import json
import sys


def winning_sets(case, truth, cap):
    # Independent formulation: enumerate every enabled subset of controllable
    # edges and ask whether one complete supervisor choice stays in the prior
    # winning layer. Uncontrollable edges are mandatory.
    edge_rows = {e["id"]: e for e in case["edges"]}
    safe_ids = set(truth["actual_safe_edges"])
    evidence_ids = set(truth["actual_evidence_edges"])
    goals = set(truth["actual_goal_states"])
    states = {case["start"]}
    for edge in case["edges"]:
        states.update((edge["source"], edge["target"]))
    layers = [goals]
    for horizon in range(1, cap + 1):
        previous = layers[-1]
        current = set(goals)
        for state in states - goals:
            outgoing = [e for e in case["edges"] if e["source"] == state]
            mandatory = [e for e in outgoing if e["kind"] == "U"]
            if any(e["id"] not in safe_ids or e["id"] not in evidence_ids or e["target"] not in previous
                   for e in mandatory):
                continue
            controllable = [e for e in outgoing if e["kind"] == "C"]
            admissible_subsets = []
            for mask in range(1 << len(controllable)):
                chosen = [controllable[i] for i in range(len(controllable)) if mask & (1 << i)]
                if any(e["id"] not in safe_ids or e["id"] not in evidence_ids or e["target"] not in previous
                       for e in chosen):
                    continue
                if mandatory or chosen:
                    admissible_subsets.append(chosen)
            if admissible_subsets:
                current.add(state)
        layers.append(current)
    return layers, edge_rows, safe_ids, evidence_ids


def safe_nonblocking(case, truth):
    usable = [e for e in case["edges"]
              if e["id"] in truth["actual_safe_edges"] and e["id"] in truth["actual_evidence_edges"]]
    reachable, pending = set(), [case["start"]]
    while pending:
        state = pending.pop()
        if state not in reachable:
            reachable.add(state)
            pending.extend(e["target"] for e in usable if e["source"] == state)
    can_finish = set(truth["actual_goal_states"])
    while True:
        grown = can_finish | {e["source"] for e in usable if e["target"] in can_finish}
        if grown == can_finish:
            break
        can_finish = grown
    return reachable <= can_finish


def has_nonmarker_cycle(case, truth):
    goals = set(truth["actual_goal_states"])
    edges = [e for e in case["edges"] if e["id"] in truth["actual_safe_edges"]]
    reachable, todo = set(), [case["start"]]
    while todo:
        state = todo.pop()
        if state not in reachable:
            reachable.add(state)
            todo.extend(e["target"] for e in edges if e["source"] == state)
    # Kahn elimination on the reachable nonmarker subgraph: any residue has a cycle.
    nodes = reachable - goals
    indegree = {state: 0 for state in nodes}
    for edge in edges:
        if edge["source"] in nodes and edge["target"] in nodes:
            indegree[edge["target"]] += 1
    queue = [state for state, degree in indegree.items() if degree == 0]
    removed = 0
    while queue:
        state = queue.pop()
        removed += 1
        for edge in edges:
            if edge["source"] == state and edge["target"] in indegree:
                indegree[edge["target"]] -= 1
                if indegree[edge["target"]] == 0:
                    queue.append(edge["target"])
    return removed != len(nodes)


def audit_case(case, truth, observed, cap, yield_contract):
    errors = []
    layers, edge_rows, safe_ids, evidence_ids = winning_sets(case, truth, cap)
    public_goals = set(case["goal_states"])
    actual_goals = set(truth["actual_goal_states"])
    public_safe = {e["id"] for e in case["edges"] if e["safe"]}
    public_evidence = {e["id"] for e in case["edges"] if e["evidence_available"]}
    contract_mismatch = (public_goals != actual_goals or public_safe != safe_ids or public_evidence != evidence_ids)
    if observed.get("completion_claim") is not False or observed.get("app_actions") != []:
        errors.append("candidate_emits_effect_or_completion")

    start_bound = next((h for h, layer in enumerate(layers) if case["start"] in layer), None)
    if contract_mismatch:
        declared_truth = {"actual_goal_states": sorted(public_goals),
                          "actual_safe_edges": sorted(public_safe),
                          "actual_evidence_edges": sorted(public_evidence)}
        declared_layers, _, _, _ = winning_sets(case, declared_truth, cap)
        declared_bound = next((h for h, layer in enumerate(declared_layers) if case["start"] in layer), None)
        if observed.get("status") != "POLICY_PROPOSED" or observed.get("bound") != declared_bound:
            errors.append("contract_conflict_proposal_not_retained_for_audit")
        return {"disposition": "HOLD_TASK_CONTRACT_ORACLE_DISAGREEMENT" if not errors else "FAIL_METHOD",
                "errors": errors, "minimal_oracle_bound": start_bound,
                "yield_validated": yield_contract == {"app_events": [], "application_effect": False,
                                                        "lease_released": True}}

    if start_bound is None:
        if observed.get("status") != "SAFE_YIELD" or observed.get("bound") is not None:
            errors.append("unbounded_case_not_yielded")
        if observed.get("policy_layers") != []:
            errors.append("policy_emitted_without_finite_bound")
        return {"disposition": "SAFE_YIELD" if not errors else "FAIL_METHOD", "errors": errors,
                "minimal_oracle_bound": None,
                "yield_validated": yield_contract == {"app_events": [], "application_effect": False,
                                                        "lease_released": True}}

    if observed.get("status") != "POLICY_PROPOSED" or observed.get("bound") != start_bound:
        errors.append("status_or_minimal_bound")
    if observed.get("nonblocking_baseline") != safe_nonblocking(case, truth):
        errors.append("nonblocking_baseline")
    policy_layers = observed.get("policy_layers", [])
    if len(policy_layers) != start_bound:
        errors.append("policy_layer_count")
    for horizon, layer in enumerate(policy_layers, start=1):
        if layer.get("remaining") != horizon:
            errors.append(f"layer_number:{horizon}")
            continue
        allowed = layer.get("allowed_edges", {})
        expected_states = layers[horizon] - actual_goals
        if set(allowed) != expected_states:
            errors.append(f"policy_state_coverage:{horizon}")
        for state, ids in allowed.items():
            if len(ids) != len(set(ids)):
                errors.append(f"duplicate_edge:{horizon}:{state}")
            for edge_id in ids:
                edge = edge_rows.get(edge_id)
                if edge is None or edge["source"] != state:
                    errors.append(f"unknown_or_misbound_edge:{horizon}:{state}:{edge_id}")
                    continue
                if edge_id not in safe_ids or edge_id not in evidence_ids:
                    errors.append(f"unsafe_or_unverified_edge:{horizon}:{edge_id}")
                if edge["target"] not in layers[horizon - 1]:
                    errors.append(f"edge_not_rank_decreasing:{horizon}:{edge_id}")
            expected = []
            for edge in case["edges"]:
                if edge["source"] != state:
                    continue
                if edge["kind"] == "U":
                    if edge["id"] not in safe_ids or edge["id"] not in evidence_ids or edge["target"] not in layers[horizon - 1]:
                        errors.append(f"mandatory_uncontrollable_not_winning:{horizon}:{edge['id']}")
                    else:
                        expected.append(edge["id"])
                elif edge["kind"] == "C" and edge["id"] in safe_ids and edge["id"] in evidence_ids and edge["target"] in layers[horizon - 1]:
                    expected.append(edge["id"])
            if sorted(ids) != sorted(expected):
                errors.append(f"not_maximal_within_bound:{horizon}:{state}")

    first = policy_layers[-1].get("allowed_edges", {}).get(case["start"], []) if policy_layers else []
    if not first:
        errors.append("start_has_no_permitted_progress_step")
    if start_bound > 0 and case["start"] in layers[start_bound - 1]:
        errors.append("reported_bound_not_minimal")
    return {"disposition": "PASS_POLICY_BOUND" if not errors else "FAIL_METHOD", "errors": errors,
            "minimal_oracle_bound": start_bound,
            "safe_nonblocking": safe_nonblocking(case, truth),
            "reachable_nonmarker_cycle": has_nonmarker_cycle(case, truth)}


def full_audit(public, oracle, raw):
    outcomes, errors = {}, []
    if raw.get("allocation") != public.get("allocation") or raw.get("allocation") != oracle.get("allocation"):
        errors.append("allocation_identity")
    by_public = {c["id"]: c for c in public["cases"]}
    if set(by_public) != set(oracle["cases"]) or set(by_public) != set(raw.get("cases", {})):
        errors.append("case_coverage")
    for name, case in by_public.items():
        outcomes[name] = audit_case(case, oracle["cases"][name], raw["cases"][name],
                                    public["max_horizon"], oracle["yield_contract"])
    wait = outcomes["safe_wait_cycle"]
    if wait.get("safe_nonblocking") is not True or wait.get("reachable_nonmarker_cycle") is not True:
        errors.append("ordinary_safe_nonblocking_livelock_not_reproduced")
    for name, outcome in outcomes.items():
        if outcome["disposition"] == "FAIL_METHOD" or outcome["errors"]:
            errors.append(f"case_failure:{name}")
    expected_holds = {"contract_disagreement": "HOLD_TASK_CONTRACT_ORACLE_DISAGREEMENT",
                      "uncontrollable_cycle": "SAFE_YIELD",
                      "missing_marker_evidence": "SAFE_YIELD"}
    for name, expected in expected_holds.items():
        if outcomes[name]["disposition"] != expected or not outcomes[name]["yield_validated"]:
            errors.append(f"required_fail_closed:{name}")
    return {"errors": errors, "outcomes": outcomes,
            "disposition": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD"}


def mutations_rejected(public, oracle, raw):
    tests = {}
    cases = {c["id"]: c for c in public["cases"]}
    broken = copy.deepcopy(raw)
    broken["cases"]["safe_wait_cycle"]["policy_layers"][0]["allowed_edges"]["s"].append("wait_s_w")
    tests["enable_wait_cycle"] = bool(full_audit(public, oracle, broken)["errors"])
    broken = copy.deepcopy(raw)
    broken["cases"]["bounded_async"]["policy_layers"][2]["allowed_edges"]["a0"] = []
    tests["suppress_mandatory_tick"] = bool(full_audit(public, oracle, broken)["errors"])
    broken = copy.deepcopy(raw)
    broken["cases"]["unsafe_control_alternative"]["policy_layers"][0]["allowed_edges"]["p"].append("unsafe_finish")
    tests["enable_unsafe_edge"] = bool(full_audit(public, oracle, broken)["errors"])
    broken = copy.deepcopy(raw)
    broken["cases"]["bounded_async"]["completion_claim"] = True
    tests["claim_completion_from_proposal"] = bool(full_audit(public, oracle, broken)["errors"])
    broken = copy.deepcopy(raw)
    broken["cases"]["bounded_async"]["bound"] = 2
    tests["understate_bound"] = bool(full_audit(public, oracle, broken)["errors"])
    broken = copy.deepcopy(raw)
    broken["cases"]["contract_disagreement"]["completion_claim"] = True
    tests["promote_conflicted_contract"] = bool(full_audit(public, oracle, broken)["errors"])
    return tests


def main(public_path, oracle_path, raw_path):
    with open(public_path, encoding="utf-8") as stream:
        public = json.load(stream)
    with open(oracle_path, encoding="utf-8") as stream:
        oracle = json.load(stream)
    with open(raw_path, encoding="utf-8") as stream:
        raw = json.load(stream)
    result = full_audit(public, oracle, raw)
    mutations = mutations_rejected(public, oracle, raw)
    result["mutation_rejected"] = mutations
    if not all(mutations.values()):
        result["errors"].append("mutation_control_survived")
        result["disposition"] = "FAIL_METHOD"
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
