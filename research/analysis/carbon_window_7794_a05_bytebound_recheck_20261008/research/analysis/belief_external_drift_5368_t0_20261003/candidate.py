"""Candidate reachable-belief gate; standard library only."""
from __future__ import annotations


def evaluate(case: dict, action_contracts: dict) -> dict:
    """Return a decision from public gate input; never receives hidden truth."""
    item = case["input"]
    if item.get("transition_complete") is not True:
        return {"id": case["id"], "reachable": [], "decision": "UNKNOWN_MODEL", "reason": "transition_coverage_unverified"}

    relation = item["transition_relation"]
    belief = set(item["initial_belief"])
    if not belief or not belief.issubset(relation):
        return {"id": case["id"], "reachable": [], "decision": "UNKNOWN_MODEL", "reason": "initial_belief_outside_model"}

    for _ in range(item["elapsed_steps"]):
        next_belief: set[str] = set()
        for state in belief:
            successors = relation.get(state)
            if not successors:
                return {"id": case["id"], "reachable": [], "decision": "UNKNOWN_MODEL", "reason": "transition_successor_missing"}
            next_belief.update(successors)
        belief = next_belief
        if not belief or not belief.issubset(relation):
            return {"id": case["id"], "reachable": [], "decision": "UNKNOWN_MODEL", "reason": "reachable_state_outside_model"}

    observation = item.get("observation")
    if (
        observation is not None
        and observation.get("source_bound") is True
        and observation.get("generation") == item["current_generation"]
    ):
        observed = set(observation.get("states", []))
        intersection = belief.intersection(observed)
        if not intersection:
            return {"id": case["id"], "reachable": [], "decision": "UNKNOWN_MODEL", "reason": "fresh_observation_contradicts_model"}
        belief = intersection

    safe_states = set(action_contracts[item["action"]]["safe_states"])
    safe = belief.issubset(safe_states)
    return {
        "id": case["id"],
        "reachable": sorted(belief),
        "decision": "ADMIT" if safe else "YIELD_UNSAFE_OR_AMBIGUOUS",
        "reason": "all_reachable_states_safe" if safe else "unsafe_state_remains_possible",
    }
