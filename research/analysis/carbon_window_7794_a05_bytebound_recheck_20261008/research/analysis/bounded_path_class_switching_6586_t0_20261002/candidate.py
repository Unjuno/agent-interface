"""Finite-graph policies for Issue #6586; receives one visible observation at a time."""
from __future__ import annotations


def _valid_closure(observation: dict, state: dict) -> tuple[bool, str | None]:
    receipt = observation.get("closure_receipt")
    if receipt is None:
        return False, None
    if type(receipt) is not dict:
        return False, "malformed_receipt"
    if receipt.get("status") != "CLASS_BLOCKED":
        return False, "wrong_receipt_status"
    if receipt.get("binding") != observation.get("binding"):
        return False, "binding_mismatch"
    if type(receipt.get("epoch")) is not int or receipt["epoch"] != observation.get("epoch"):
        return False, "epoch_mismatch"
    if type(receipt.get("sequence")) is not int or receipt["sequence"] != observation.get("sequence"):
        return False, "sequence_mismatch"
    if receipt.get("complete_cutset") is not True:
        return False, "incomplete_cutset"
    if not state["path"]:
        return False, "no_current_route_receipt"
    if receipt.get("route_token") != state["path"][0]["route_token"]:
        return False, "route_token_mismatch"
    return True, None


def choose_action(observation: dict, state: dict, policy: str) -> tuple[dict, dict | None]:
    """Return one bounded action and optional evidence-classification event.

    The policy sees only the current observation plus its own visited/path receipts.
    It is never passed the complete graph or evaluator oracle.
    """
    epoch = observation["epoch"]
    if state["epoch"] is None:
        state["epoch"] = epoch
    elif epoch != state["epoch"]:
        state["epoch"] = epoch
        state["excluded_route_tokens"].clear()
        state["seen_receipts"].clear()

    if observation["node_id"] == observation["goal_id"]:
        return {"kind": "STOP_GOAL"}, None

    if observation["node_id"] == observation["start_id"]:
        state["root_route_tokens"].update(
            edge["route_token"] for edge in observation["edges"]
            if edge.get("traversable") is True and type(edge.get("route_token")) is str
        )

    evidence_event = None
    if policy == "class_aware" and observation.get("closure_receipt") is not None:
        receipt = observation["closure_receipt"]
        receipt_key = repr(sorted(receipt.items())) if type(receipt) is dict else repr(receipt)
        if receipt_key not in state["seen_receipts"]:
            state["seen_receipts"].add(receipt_key)
            valid, reason = _valid_closure(observation, state)
            current_token = state["path"][0]["route_token"] if state["path"] else None
            if valid:
                state["excluded_route_tokens"].add(current_token)
                alternatives = state["root_route_tokens"] - state["excluded_route_tokens"]
                if alternatives:
                    evidence_event = {
                        "kind": "CLASS_CERTIFICATE_ACCEPTED",
                        "sequence": observation["sequence"],
                        "route_token": current_token,
                        "alternative_tokens": sorted(alternatives),
                    }
                    return {"kind": "BACKTRACK", "reason": "class_switch"}, evidence_event
                evidence_event = {
                    "kind": "CLASS_CERTIFICATE_ACCEPTED_NO_ALTERNATE",
                    "sequence": observation["sequence"],
                    "route_token": current_token,
                }
                return {"kind": "YIELD", "reason": "NO_ALTERNATE_CLASS"}, evidence_event
            evidence_event = {
                "kind": "CLASS_CERTIFICATE_REJECTED",
                "sequence": observation["sequence"],
                "reason": reason,
            }

    visited_nodes = set(state["visited_nodes"])
    eligible = [edge for edge in observation["edges"]
                if edge.get("traversable") is True
                and edge["to"] not in visited_nodes
                and edge.get("route_token") not in state["excluded_route_tokens"]]
    if eligible:
        if policy == "novel_cell":
            edge = min(eligible, key=lambda item: (-item["novelty"], item["order"], item["id"]))
        else:
            edge = min(eligible, key=lambda item: (item["order"], item["id"]))
        return {"kind": "TRAVERSE", "edge_id": edge["id"], "to": edge["to"],
                "route_token": edge["route_token"]}, evidence_event
    if state["path"]:
        return {"kind": "BACKTRACK", "reason": "visited_edge_exhaustion"}, evidence_event
    if state["excluded_route_tokens"]:
        return {"kind": "YIELD", "reason": "NO_ALTERNATE_CLASS"}, evidence_event
    return {"kind": "YIELD", "reason": "NO_UNVISITED_SAFE_EDGE"}, evidence_event


def new_state(start_id: str) -> dict:
    return {
        "epoch": None,
        "visited_nodes": [start_id],
        "visited_edges": [],
        "path": [],
        "root_route_tokens": set(),
        "excluded_route_tokens": set(),
        "seen_receipts": set(),
        "switch_count": 0,
    }
