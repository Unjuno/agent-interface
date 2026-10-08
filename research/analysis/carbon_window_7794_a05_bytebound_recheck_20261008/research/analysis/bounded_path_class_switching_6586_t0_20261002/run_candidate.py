"""One-shot raw-only candidate runner. The evaluator oracle is not an input."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import candidate


ROOT = Path(__file__).resolve().parent
ALLOCATION = "PATH-CLASS-6586-T0-20261002-01"
MAIN_SHA = "f1d8f6319ad6a1d6fd7f0219c17bb13f48fae7aa"
HASHED_INPUTS = ("fixture_visible.json", "candidate.py", "run_candidate.py")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_freeze() -> dict:
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    if freeze.get("allocation") != ALLOCATION or freeze.get("main_sha") != MAIN_SHA:
        raise SystemExit("STOP_FREEZE_IDENTITY_MISMATCH")
    expected = freeze.get("sha256", {})
    for name in HASHED_INPUTS:
        if expected.get(name) != sha256(ROOT / name):
            raise SystemExit(f"STOP_FROZEN_HASH_MISMATCH:{name}")
    return freeze


def execute_case(case: dict, policy: str, max_observations: int, max_input_actions: int) -> dict:
    state = candidate.new_state(case["start"])
    current = case["start"]
    events: list[dict] = []
    observations = 0
    input_actions = 0
    sequence = 0
    terminal = "UNFINISHED"

    while observations < max_observations and input_actions < max_input_actions:
        node = case["nodes"].get(current)
        if node is None:
            terminal = "UNKNOWN_NODE"
            break
        sequence += 1
        observation = {
            "node_id": current,
            "start_id": case["start"],
            "goal_id": case["goal"],
            "binding": case["binding"],
            "epoch": node["epoch"],
            "sequence": sequence,
            "edges": node["edges"],
        }
        if "closure_receipt" in node:
            observation["closure_receipt"] = node["closure_receipt"]
        observations += 1
        events.append({"kind": "OBSERVE", "observation": observation})

        action, evidence_event = candidate.choose_action(observation, state, policy)
        if evidence_event is not None:
            events.append(evidence_event)
        if action["kind"] == "STOP_GOAL":
            terminal = "GOAL_OBSERVED"
            break
        if action["kind"] == "YIELD":
            terminal = action["reason"]
            events.append({"kind": "YIELD", "reason": terminal, "node_id": current})
            break
        if action["kind"] == "TRAVERSE":
            edge = next((item for item in observation["edges"]
                         if item["id"] == action["edge_id"]
                         and item["to"] == action["to"]), None)
            if edge is None or edge.get("traversable") is not True:
                terminal = "FORBIDDEN_OR_UNOBSERVED_TRANSITION"
                events.append({"kind": "INVALID_TRANSITION", "node_id": current,
                               "action": action})
                break
            source = current
            current = edge["to"]
            state["path"].append({"from": source, "to": current,
                                  "edge_id": edge["id"],
                                  "route_token": edge["route_token"]})
            state["visited_edges"].append(edge["id"])
            state["visited_nodes"].append(current)
            input_actions += 1
            events.append({"kind": "TRAVERSE", "from": source, "to": current,
                           "edge_id": edge["id"], "route_token": edge["route_token"]})
        elif action["kind"] == "BACKTRACK":
            if not state["path"]:
                terminal = "INVALID_BACKTRACK"
                events.append({"kind": "INVALID_BACKTRACK", "node_id": current})
                break
            edge = state["path"].pop()
            if current != edge["to"]:
                terminal = "PATH_RECEIPT_MISMATCH"
                events.append({"kind": "PATH_RECEIPT_MISMATCH", "node_id": current})
                break
            source = current
            current = edge["from"]
            input_actions += 1
            if action.get("reason") == "class_switch":
                state["switch_count"] += 1
            events.append({"kind": "BACKTRACK", "from": source, "to": current,
                           "edge_id": edge["edge_id"], "reason": action.get("reason")})
        else:
            terminal = "UNKNOWN_ACTION"
            events.append({"kind": "UNKNOWN_ACTION", "action": action})
            break

    if terminal == "UNFINISHED":
        terminal = "OBSERVATION_BUDGET_EXHAUSTED" if observations >= max_observations else "INPUT_BUDGET_EXHAUSTED"
    return {
        "case_id": case["id"],
        "policy": policy,
        "events": events,
        "terminal_node": current,
        "terminal": terminal,
        "goal_observed": terminal == "GOAL_OBSERVED" and current == case["goal"],
        "observations": observations,
        "input_actions": input_actions,
        "total_counted_events": observations + input_actions,
        "model_calls": 0,
        "backtracks": sum(event["kind"] == "BACKTRACK" for event in events),
        "switch_backtracks": sum(event["kind"] == "BACKTRACK" and event.get("reason") == "class_switch" for event in events),
        "visited_nodes": sorted(set(state["visited_nodes"])),
        "excluded_route_tokens": sorted(state["excluded_route_tokens"]),
    }


def run(out_path: Path) -> dict:
    freeze = verify_freeze()
    fixture_path = ROOT / "fixture_visible.json"
    visible = json.loads(fixture_path.read_text(encoding="utf-8"))
    if visible.get("allocation") != ALLOCATION:
        raise SystemExit("STOP_FIXTURE_ALLOCATION_MISMATCH")
    rows = [execute_case(case, policy, visible["max_observations"], visible["max_input_actions"])
            for case in visible["cases"] for policy in visible["policies"]]
    raw = {
        "schema": "path-class-switching-raw-v1",
        "allocation": ALLOCATION,
        "main_sha": MAIN_SHA,
        "freeze_sha256": sha256(ROOT / "FREEZE.json"),
        "visible_fixture_sha256": sha256(fixture_path),
        "candidate_sha256": sha256(ROOT / "candidate.py"),
        "runner_sha256": sha256(ROOT / "run_candidate.py"),
        "policy_order": visible["policies"],
        "case_order": [case["id"] for case in visible["cases"]],
        "budget": {"max_observations": visible["max_observations"],
                   "max_input_actions": visible["max_input_actions"], "model_calls": 0},
        "rows": rows,
        "row_count": len(rows),
    }
    if out_path.exists():
        raise SystemExit("STOP_RAW_OUTPUT_ALREADY_EXISTS")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"allocation": ALLOCATION, "rows": len(rows),
                      "output": str(out_path), "freeze_sha256": raw["freeze_sha256"]}, sort_keys=True))
    return raw


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "results" / "a01" / "raw.json")
    args = parser.parse_args()
    run(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
