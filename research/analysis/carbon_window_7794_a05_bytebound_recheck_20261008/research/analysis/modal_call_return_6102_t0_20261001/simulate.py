#!/usr/bin/env python3
"""Finite source-bound GUI modal traces; no GUI or external service."""
from __future__ import annotations

import json
import sys
from pathlib import Path

MAX_DEPTH = 3
ROOT = ("root", 0)

CASES = {
    "root_action": [{"op": "ACT", "parent": "root", "generation": 0}],
    "valid_depth_1": [
        {"op": "OPEN", "parent": "root", "child": "modal-a", "generation": 1},
        {"op": "ACT", "parent": "modal-a", "generation": 1},
        {"op": "CLOSE", "parent": "root", "child": "modal-a", "generation": 1},
        {"op": "ACT", "parent": "root", "generation": 0},
    ],
    "valid_depth_2": [
        {"op": "OPEN", "parent": "root", "child": "modal-a", "generation": 1},
        {"op": "OPEN", "parent": "modal-a", "child": "modal-b", "generation": 1},
        {"op": "CLOSE", "parent": "modal-a", "child": "modal-b", "generation": 1},
        {"op": "ACT", "parent": "modal-a", "generation": 1},
        {"op": "CLOSE", "parent": "root", "child": "modal-a", "generation": 1},
    ],
    "valid_depth_3": [
        {"op": "OPEN", "parent": "root", "child": "modal-a", "generation": 1},
        {"op": "OPEN", "parent": "modal-a", "child": "modal-b", "generation": 1},
        {"op": "OPEN", "parent": "modal-b", "child": "modal-c", "generation": 2},
        {"op": "CLOSE", "parent": "modal-b", "child": "modal-c", "generation": 2},
        {"op": "CLOSE", "parent": "modal-a", "child": "modal-b", "generation": 1},
        {"op": "CLOSE", "parent": "root", "child": "modal-a", "generation": 1},
    ],
    "wrong_parent_close": [
        {"op": "OPEN", "parent": "root", "child": "modal-a", "generation": 1},
        {"op": "OPEN", "parent": "modal-a", "child": "modal-b", "generation": 1},
        {"op": "CLOSE", "parent": "root", "child": "modal-b", "generation": 1},
        {"op": "ACT", "parent": "root", "generation": 0},
    ],
    "duplicate_close": [
        {"op": "OPEN", "parent": "root", "child": "modal-a", "generation": 1},
        {"op": "CLOSE", "parent": "root", "child": "modal-a", "generation": 1},
        {"op": "CLOSE", "parent": "root", "child": "modal-a", "generation": 1},
    ],
    "parent_destroyed_with_child": [
        {"op": "OPEN", "parent": "root", "child": "modal-a", "generation": 1},
        {"op": "OPEN", "parent": "modal-a", "child": "modal-b", "generation": 1},
        {"op": "DESTROY_PARENT", "parent": "root", "child": "modal-a", "generation": 1},
    ],
    "non_lifo_switch": [
        {"op": "OPEN", "parent": "root", "child": "modal-a", "generation": 1},
        {"op": "OPEN", "parent": "modal-a", "child": "modal-b", "generation": 1},
        {"op": "CLOSE", "parent": "root", "child": "modal-a", "generation": 1},
    ],
    "missing_open": [{"op": "CLOSE", "parent": "root", "child": "modal-a", "generation": 1}],
    "stale_generation_after_reuse": [
        {"op": "OPEN", "parent": "root", "child": "modal-a", "generation": 1},
        {"op": "CLOSE", "parent": "root", "child": "modal-a", "generation": 1},
        {"op": "OPEN", "parent": "root", "child": "modal-a", "generation": 2},
        {"op": "CLOSE", "parent": "root", "child": "modal-a", "generation": 1},
    ],
    "interleaved_window": [
        {"op": "OPEN", "parent": "root", "child": "modal-a", "generation": 1},
        {"op": "FOCUS_OTHER", "surface": "window-b", "generation": 1},
    ],
    "unknown_identity": [
        {"op": "OPEN", "parent": "root", "child": "modal-z", "generation": 1},
    ],
    "wrong_action_context": [
        {"op": "OPEN", "parent": "root", "child": "modal-a", "generation": 1},
        {"op": "ACT", "parent": "root", "generation": 0},
    ],
    "depth_overflow": [
        {"op": "OPEN", "parent": "root", "child": "modal-a", "generation": 1},
        {"op": "OPEN", "parent": "modal-a", "child": "modal-b", "generation": 1},
        {"op": "OPEN", "parent": "modal-b", "child": "modal-c", "generation": 1},
        {"op": "OPEN", "parent": "modal-c", "child": "modal-a", "generation": 2},
    ],
}


def stack_policy(events: list[dict]) -> dict:
    stack: list[tuple[str, int]] = []
    for index, event in enumerate(events):
        op = event["op"]
        top = stack[-1] if stack else ROOT
        if op == "OPEN":
            parent, child = event["parent"], event["child"]
            frame = (child, event["generation"])
            if parent != top[0] or child not in {"modal-a", "modal-b", "modal-c"} or len(stack) >= MAX_DEPTH or frame in stack:
                return {"decision": "UNKNOWN_NESTING", "at": index, "context": list(stack)}
            stack.append(frame)
        elif op == "CLOSE":
            frame = (event["child"], event["generation"])
            if not stack or stack[-1] != frame or event["parent"] != (stack[-2][0] if len(stack) > 1 else "root"):
                return {"decision": "UNKNOWN_NESTING", "at": index, "context": list(stack)}
            stack.pop()
        elif op == "ACT":
            if (event["parent"], event["generation"]) != top:
                return {"decision": "UNKNOWN_NESTING", "at": index, "context": list(stack)}
        elif op in {"DESTROY_PARENT", "FOCUS_OTHER"}:
            return {"decision": "UNKNOWN_NESTING", "at": index, "context": list(stack)}
        else:
            return {"decision": "UNKNOWN_NESTING", "at": index, "context": list(stack)}
    return {"decision": "ACCEPT", "at": None, "context": list(stack)}


def fsm_policy(events: list[dict]) -> dict:
    """Depth-3 DFA: state is a canonical finite encoding of a stack configuration."""
    state: tuple[tuple[str, int], ...] = ()
    transitions = 0
    visited = {state}
    for index, event in enumerate(events):
        op = event["op"]
        parent = state[-1][0] if state else "root"
        top = state[-1] if state else ROOT
        nxt = state
        valid = True
        if op == "OPEN":
            frame = (event["child"], event["generation"])
            valid = event["parent"] == parent and event["child"] in {"modal-a", "modal-b", "modal-c"} and len(state) < MAX_DEPTH and frame not in state
            if valid:
                nxt = state + (frame,)
        elif op == "CLOSE":
            valid = bool(state) and state[-1] == (event["child"], event["generation"]) and event["parent"] == parent_of(state)
            if valid:
                nxt = state[:-1]
        elif op == "ACT":
            valid = (event["parent"], event["generation"]) == top
        else:
            valid = False
        transitions += 1
        if not valid:
            return {"decision": "UNKNOWN_NESTING", "at": index, "context": [list(x) for x in state], "transitions": transitions, "states_visited": len(visited)}
        state = nxt
        visited.add(state)
    return {"decision": "ACCEPT", "at": None, "context": [list(x) for x in state], "transitions": transitions, "states_visited": len(visited)}


def parent_of(state: tuple[tuple[str, int], ...]) -> str:
    return state[-2][0] if len(state) > 1 else "root"


def flat_policy(events: list[dict]) -> dict:
    open_flag = False
    accepted_actions = 0
    for index, event in enumerate(events):
        if event["op"] == "OPEN":
            open_flag = True
        elif event["op"] == "CLOSE":
            open_flag = False
        elif event["op"] == "ACT":
            if (event["parent"] == "root" and not open_flag) or (event["parent"] != "root" and open_flag):
                accepted_actions += 1
            else:
                return {"decision": "UNKNOWN_NESTING", "at": index, "accepted_actions": accepted_actions}
        else:
            # A flat visibility bit cannot interpret these events and conservatively yields.
            return {"decision": "UNKNOWN_NESTING", "at": index, "accepted_actions": accepted_actions}
    return {"decision": "ACCEPT", "at": None, "accepted_actions": accepted_actions}


def main(output: str) -> None:
    with Path(output).open("w", encoding="utf-8", newline="\n") as stream:
        for case_id, events in CASES.items():
            row = {
                "case_id": case_id,
                "events": events,
                "stack": stack_policy(events),
                "fsm": fsm_policy(events),
                "flat": flat_policy(events),
                "max_depth": MAX_DEPTH,
                "dfa_states_visited": fsm_policy(events)["states_visited"],
            }
            stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"cases": len(CASES), "output": output}, sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python simulate.py OUTPUT.jsonl")
    main(sys.argv[1])
