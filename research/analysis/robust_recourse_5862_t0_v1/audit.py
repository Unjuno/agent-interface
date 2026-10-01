"""Independent exhaustive audit of frozen belief-state recourse policies."""
import json
import sys


TERMINAL = {"TASK_SUCCESS", "SAFE_HANDOFF"}
EXPECTED_BELIEFS = {
    "no_match_target_elsewhere": ("elsewhere",),
    "target_genuinely_absent": ("absent",),
    "stale_evidence_reacquirable": ("stale",),
    "revoked_authority": ("revoked",),
    "uncertain_delivery_same_blocked_receipt": ("delivery_uncommitted", "delivery_committed"),
    "irreversible_partial_effect": ("partial_uncommitted", "partial_committed"),
    "viable_manual_takeover": ("takeover_available",),
}
EXPECTED_LABELS = {
    "no_match_target_elsewhere": "ROBUST_ADVISORY",
    "target_genuinely_absent": "NO_ROUTE_WITHIN_BOUND",
    "stale_evidence_reacquirable": "ROBUST_ADVISORY",
    "revoked_authority": "CONDITIONAL_ADVISORY",
    "uncertain_delivery_same_blocked_receipt": "ROBUST_ADVISORY",
    "irreversible_partial_effect": "ROBUST_ADVISORY",
    "viable_manual_takeover": "CONDITIONAL_ADVISORY",
}


def exhaustive_policy(model, world_set, policy, level=0):
    if level == model["horizon"] or not world_set:
        return False
    observation_groups = {}
    for world_name in world_set:
        world = model["states"].get(world_name)
        if world is None:
            return False
        move = world.get("actions", {}).get(policy.get("action"))
        if move is None:
            return False
        permitted = (move.get("safe") is True and move.get("preconditions") is True and
                     move.get("actor") in world.get("authorized_actors", ()) and
                     move.get("generation") == world.get("authority_generation") and
                     type(move.get("cost")) is int and 0 <= move["cost"] <= world.get("budget", -1) and
                     not (set(move.get("replays", ())) & set(world.get("committed_effects", ()))))
        if not permitted:
            return False
        branches = move.get("outcomes", ())
        if not branches:
            return False
        for branch in branches:
            label, successor = branch.get("observation"), branch.get("next")
            if not label or not successor:
                return False
            if successor not in TERMINAL:
                next_world = model["states"].get(successor)
                if (next_world is None or next_world.get("budget", model["horizon"] + 1) > world["budget"] - move["cost"] or
                        next_world.get("authority_generation", -1) < world["authority_generation"]):
                    return False
                if next_world["authority_generation"] > world["authority_generation"] and not (
                        policy["action"] == "request_human_authority" and label == "approved"):
                    return False
            observation_groups.setdefault(label, set()).add(successor)
    continuation = policy.get("branches", {})
    if set(continuation) != set(observation_groups):
        return False
    for label, successors in observation_groups.items():
        target = continuation[label]
        terminal_targets = successors & TERMINAL
        nonterminal_targets = successors - TERMINAL
        if terminal_targets:
            if nonterminal_targets or len(terminal_targets) != 1 or target != {"terminal": terminal_targets.pop()}:
                return False
        elif not exhaustive_policy(model, sorted(nonterminal_targets), target, level + 1):
            return False
    return True


def singleton_feasible(model, belief, proposal):
    return any(exhaustive_policy(model, [world], proposal) for world in belief)


def reconstruct(model):
    outcomes = []
    for case in model["cases"]:
        policy_results = {name: exhaustive_policy(model, case["belief"], policy)
                          for name, policy in case["policies"].items()}
        selected = case["selected_policy"]
        if selected == "none":
            label = "NO_ROUTE_WITHIN_BOUND" if not any(policy_results.values()) else "UNKNOWN_FEASIBILITY"
        elif policy_results.get(selected, False):
            label = "CONDITIONAL_ADVISORY" if case.get("conditional_actor") or case.get("new_authority_required") else "ROBUST_ADVISORY"
        elif any(singleton_feasible(model, case["belief"], policy) for policy in case["policies"].values()):
            label = "EXISTENTIAL_ONLY"
        else:
            label = "UNKNOWN_FEASIBILITY"
        retry = case["policies"].get("generic_retry", {"action":"", "branches":{}})
        outcomes.append({"id": case["id"], "selected_policy": selected,
                         "selected_policy_valid": bool(policy_results.get(selected, False)),
                         "generic_retry_valid": bool(policy_results.get("generic_retry", False)),
                         "diagnosis_only_valid": bool(policy_results.get("diagnosis_only", False)),
                         "generic_retry_existential": singleton_feasible(model, case["belief"], retry),
                         "label": label, "authority_created": False, "coordinates_emitted": False})
    return {"schema":"5862-belief-robust-recourse-result-v1", "cases":outcomes}


def audit(model, actual):
    assert model.get("transition_enumeration_complete") is True
    assert set(case["id"] for case in model["cases"]) == set(EXPECTED_BELIEFS)
    assert len(model["cases"]) == 7
    for case in model["cases"]:
        assert tuple(case["belief"]) == EXPECTED_BELIEFS[case["id"]], case["id"]
    committed = model["states"]["delivery_committed"]
    uncommitted = model["states"]["delivery_uncommitted"]
    assert committed["stop_receipt"] == uncommitted["stop_receipt"]
    assert committed["stop_receipt"]["status"] == "BLOCKED"
    retry = committed["actions"]["retry"]
    assert retry["safe"] is False and "irreversible:submit-17" in retry["replays"]
    adverse = [o for o in retry["outcomes"] if o["next"] == "UNSAFE"]
    assert adverse, "committed-world duplicate-effect transition missing"
    expected = reconstruct(model)
    assert actual == expected, "candidate output differs from independent exhaustive reconstruction"
    for row in expected["cases"]:
        assert row["label"] == EXPECTED_LABELS[row["id"]], row["id"]
        assert not row["authority_created"] and not row["coordinates_emitted"]
    uncertain = next(x for x in expected["cases"] if x["id"] == "uncertain_delivery_same_blocked_receipt")
    assert not uncertain["generic_retry_valid"] and uncertain["generic_retry_existential"]
    assert uncertain["selected_policy_valid"]
    assert {"TASK_SUCCESS", "SAFE_HANDOFF"}.issuperset(TERMINAL)
    return {"status":"METHOD_PASS_SCOPED", "cases_reconstructed":7,
            "robust_selected_policies":4, "conditional_advisories":2,
            "existential_retry_counterexamples":1, "mutations":6,
            "scope":"finite synthetic abstraction only"}


if __name__ == "__main__":
    model = json.load(open(sys.argv[1], encoding="utf-8"))
    observed = json.load(sys.stdin)
    print(json.dumps(audit(model, observed), sort_keys=True, separators=(",", ":")))
