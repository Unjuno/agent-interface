#!/usr/bin/env python3
"""Independent raw-only verifier; intentionally does not import simulate.py."""
from __future__ import annotations

import json
import sys
from pathlib import Path

KNOWN_IDS = {"modal-a", "modal-b", "modal-c"}
DEPTH_LIMIT = 3
EXPECTED = {
    "root_action": "ACCEPT",
    "valid_depth_1": "ACCEPT",
    "valid_depth_2": "ACCEPT",
    "valid_depth_3": "ACCEPT",
    "wrong_parent_close": "UNKNOWN_NESTING",
    "duplicate_close": "UNKNOWN_NESTING",
    "parent_destroyed_with_child": "UNKNOWN_NESTING",
    "non_lifo_switch": "UNKNOWN_NESTING",
    "missing_open": "UNKNOWN_NESTING",
    "stale_generation_after_reuse": "UNKNOWN_NESTING",
    "interleaved_window": "UNKNOWN_NESTING",
    "unknown_identity": "UNKNOWN_NESTING",
    "wrong_action_context": "UNKNOWN_NESTING",
    "depth_overflow": "UNKNOWN_NESTING",
}


def independent_stack(events: list[dict]) -> dict:
    frames: list[tuple[str, int]] = []
    for pos, item in enumerate(events):
        kind = item.get("op")
        if kind == "OPEN":
            current = frames[-1][0] if frames else "root"
            value = (item.get("child"), item.get("generation"))
            if item.get("parent") != current or value[0] not in KNOWN_IDS or len(frames) == DEPTH_LIMIT or value in frames:
                return {"decision": "UNKNOWN_NESTING", "at": pos, "context": [list(f) for f in frames]}
            frames.append(value)
        elif kind == "CLOSE":
            parent = frames[-2][0] if len(frames) > 1 else "root"
            if not frames or frames[-1] != (item.get("child"), item.get("generation")) or item.get("parent") != parent:
                return {"decision": "UNKNOWN_NESTING", "at": pos, "context": [list(f) for f in frames]}
            frames.pop()
        elif kind == "ACT":
            current = frames[-1] if frames else ("root", 0)
            if (item.get("parent"), item.get("generation")) != current:
                return {"decision": "UNKNOWN_NESTING", "at": pos, "context": [list(f) for f in frames]}
        else:
            return {"decision": "UNKNOWN_NESTING", "at": pos, "context": [list(f) for f in frames]}
    return {"decision": "ACCEPT", "at": None, "context": [list(f) for f in frames]}


def independent_fsm(events: list[dict]) -> dict:
    # The finite automaton's current node is the canonical tuple of frames.
    node: tuple[tuple[str, int], ...] = ()
    states = {node}
    for pos, item in enumerate(events):
        event = item.get("op")
        active = node[-1] if node else ("root", 0)
        candidate = node
        legal = True
        if event == "OPEN":
            frame = (item.get("child"), item.get("generation"))
            legal = item.get("parent") == active[0] and frame[0] in KNOWN_IDS and len(node) < DEPTH_LIMIT and frame not in node
            if legal:
                candidate = (*node, frame)
        elif event == "CLOSE":
            parent = node[-2][0] if len(node) > 1 else "root"
            legal = bool(node) and node[-1] == (item.get("child"), item.get("generation")) and item.get("parent") == parent
            if legal:
                candidate = node[:-1]
        elif event == "ACT":
            legal = (item.get("parent"), item.get("generation")) == active
        else:
            legal = False
        if not legal:
            return {"decision": "UNKNOWN_NESTING", "at": pos, "context": [list(f) for f in node], "transitions": pos + 1, "states_visited": len(states)}
        node = candidate
        states.add(node)
    return {"decision": "ACCEPT", "at": None, "context": [list(f) for f in node], "transitions": len(events), "states_visited": len(states)}


def independent_flat(events: list[dict]) -> dict:
    modal_visible = False
    accepted = 0
    for pos, item in enumerate(events):
        if item.get("op") == "OPEN":
            modal_visible = True
        elif item.get("op") == "CLOSE":
            modal_visible = False
        elif item.get("op") == "ACT":
            plausible = (item.get("parent") == "root" and not modal_visible) or (item.get("parent") != "root" and modal_visible)
            if not plausible:
                return {"decision": "UNKNOWN_NESTING", "at": pos, "accepted_actions": accepted}
            accepted += 1
        else:
            return {"decision": "UNKNOWN_NESTING", "at": pos, "accepted_actions": accepted}
    return {"decision": "ACCEPT", "at": None, "accepted_actions": accepted}


def audit_rows(rows: list[dict]) -> dict:
    errors: list[str] = []
    if len(rows) != len(EXPECTED):
        errors.append(f"case_count:{len(rows)}")
    observed: set[str] = set()
    flat_counterexample = False
    for row in rows:
        name = row.get("case_id")
        if name not in EXPECTED or name in observed:
            errors.append(f"case_identity:{name}")
            continue
        observed.add(name)
        events = row.get("events")
        if not isinstance(events, list):
            errors.append(f"events_not_list:{name}")
            continue
        stack = independent_stack(events)
        finite = independent_fsm(events)
        flat = independent_flat(events)
        if row.get("stack") != stack:
            errors.append(f"stack_mismatch:{name}")
        if row.get("fsm") != finite:
            errors.append(f"fsm_mismatch:{name}")
        if row.get("flat") != flat:
            errors.append(f"flat_mismatch:{name}")
        expected = EXPECTED[name]
        if stack["decision"] != expected or finite["decision"] != expected:
            errors.append(f"oracle_disposition:{name}")
        if stack["decision"] != finite["decision"] or stack.get("context") != finite.get("context"):
            errors.append(f"stack_fsm_divergence:{name}")
        if name == "wrong_parent_close" and flat["decision"] == "ACCEPT":
            flat_counterexample = True
    if observed != set(EXPECTED):
        errors.append("missing_cases")
    if not flat_counterexample:
        errors.append("flat_counterexample_absent")
    return {
        "disposition": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT",
        "cases": len(rows),
        "stack_fsm_exact_matches": sum(1 for r in rows if r.get("stack") == independent_stack(r.get("events", [])) and r.get("fsm") == independent_fsm(r.get("events", []))),
        "invalid_cases_fail_closed": sum(1 for r in rows if EXPECTED.get(r.get("case_id")) == "UNKNOWN_NESTING" and r.get("stack", {}).get("decision") == "UNKNOWN_NESTING"),
        "flat_wrong_parent_counterexample": flat_counterexample,
        "max_supported_depth": DEPTH_LIMIT,
        "errors": errors,
    }


def main(source: str) -> int:
    rows = [json.loads(line) for line in Path(source).read_text(encoding="utf-8").splitlines() if line]
    result = audit_rows(rows)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if not result["errors"] else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python audit.py RAW.jsonl")
    raise SystemExit(main(sys.argv[1]))
