"""Bounded belief-state advisory validator; never executes or grants authority."""
import json
import sys

TERMINALS = {"TASK_SUCCESS", "SAFE_HANDOFF"}


def validate_node(model, belief, node, depth=0):
    if depth >= model["horizon"] or not belief:
        return False
    grouped = {}
    for state_id in belief:
        state = model["states"].get(state_id)
        if state is None:
            return False
        action = state.get("actions", {}).get(node.get("action"))
        if action is None:
            return False
        if (not action.get("safe") or not action.get("preconditions") or
                action.get("actor") not in state.get("authorized_actors", []) or
                action.get("generation") != state.get("authority_generation") or
                action.get("cost", model["horizon"] + 1) > state.get("budget", -1) or
                set(action.get("replays", [])) & set(state.get("committed_effects", []))):
            return False
        outcomes = action.get("outcomes", [])
        if not outcomes:
            return False
        for outcome in outcomes:
            obs, nxt = outcome.get("observation"), outcome.get("next")
            if not obs or not nxt:
                return False
            if nxt not in TERMINALS:
                successor = model["states"].get(nxt)
                if (successor is None or successor.get("budget", model["horizon"] + 1) > state["budget"] - action["cost"] or
                        successor.get("authority_generation", -1) < state["authority_generation"]):
                    return False
                if successor["authority_generation"] > state["authority_generation"] and not (
                        node["action"] == "request_human_authority" and obs == "approved"):
                    return False
            grouped.setdefault(obs, set()).add(nxt)
    branches = node.get("branches", {})
    if set(branches) != set(grouped):
        return False
    for observation, next_ids in grouped.items():
        child = branches[observation]
        terminals = next_ids & TERMINALS
        states = next_ids - TERMINALS
        if terminals:
            if states or len(terminals) != 1 or child != {"terminal": next(iter(terminals))}:
                return False
        elif not validate_node(model, sorted(states), child, depth + 1):
            return False
    return True


def any_world_valid(model, belief, policy):
    return any(validate_node(model, [state], policy) for state in belief)


def classify_case(model, case):
    validity = {name: validate_node(model, case["belief"], policy)
                for name, policy in case.get("policies", {}).items()}
    selected = case.get("selected_policy")
    if selected == "none":
        label = "NO_ROUTE_WITHIN_BOUND" if not any(validity.values()) else "UNKNOWN_FEASIBILITY"
    elif validity.get(selected):
        label = "CONDITIONAL_ADVISORY" if case.get("conditional_actor") or case.get("new_authority_required") else "ROBUST_ADVISORY"
    elif any(any_world_valid(model, case["belief"], p) for p in case.get("policies", {}).values()):
        label = "EXISTENTIAL_ONLY"
    else:
        label = "UNKNOWN_FEASIBILITY"
    return {"id": case["id"], "selected_policy": selected,
            "selected_policy_valid": bool(validity.get(selected, False)),
            "generic_retry_valid": bool(validity.get("generic_retry", False)),
            "diagnosis_only_valid": bool(validity.get("diagnosis_only", False)),
            "generic_retry_existential": any_world_valid(model, case["belief"], case.get("policies", {}).get("generic_retry", {"action": "", "branches": {}})),
            "label": label, "authority_created": False, "coordinates_emitted": False}


def run(model):
    return {"schema": "5862-belief-robust-recourse-result-v1",
            "cases": [classify_case(model, case) for case in model["cases"]]}


if __name__ == "__main__":
    print(json.dumps(run(json.load(sys.stdin)), sort_keys=True, separators=(",", ":")))
