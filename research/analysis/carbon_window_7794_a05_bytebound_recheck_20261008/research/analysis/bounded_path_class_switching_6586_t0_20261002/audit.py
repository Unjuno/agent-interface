"""Independent raw-only graph replay and hidden-oracle audit; imports no candidate code."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ALLOCATION = "PATH-CLASS-6586-T0-20261002-01"
MAIN_SHA = "f1d8f6319ad6a1d6fd7f0219c17bb13f48fae7aa"
POLICIES = ("novel_cell", "visited_edge_backtrack", "class_aware")
HASHED_INPUTS = ("fixture_visible.json", "oracle.json", "candidate.py", "run_candidate.py", "audit.py",
                 "test_method.py", "preregistration.md", "README.md")
RAW_KEYS = {
    "schema", "allocation", "main_sha", "freeze_sha256", "visible_fixture_sha256",
    "candidate_sha256", "runner_sha256", "policy_order", "case_order", "budget", "rows", "row_count",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def receipt_status(obs: dict, route_token: str | None) -> tuple[bool, str | None]:
    receipt = obs.get("closure_receipt")
    if receipt is None:
        return False, None
    if type(receipt) is not dict:
        return False, "malformed_receipt"
    if receipt.get("status") != "CLASS_BLOCKED":
        return False, "wrong_receipt_status"
    if receipt.get("binding") != obs.get("binding"):
        return False, "binding_mismatch"
    if type(receipt.get("epoch")) is not int or receipt["epoch"] != obs.get("epoch"):
        return False, "epoch_mismatch"
    if type(receipt.get("sequence")) is not int or receipt["sequence"] != obs.get("sequence"):
        return False, "sequence_mismatch"
    if receipt.get("complete_cutset") is not True:
        return False, "incomplete_cutset"
    if route_token is None:
        return False, "no_current_route_receipt"
    if receipt.get("route_token") != route_token:
        return False, "route_token_mismatch"
    return True, None


def graph_paths(case: dict, start: str, goal: str, route_token: str | None = None) -> list[list[str]]:
    """Enumerate simple paths independently from candidate-visible adjacency."""
    paths: list[list[str]] = []

    def visit(node: str, seen: set[str], tokens: list[str]) -> None:
        if node == goal:
            paths.append(tokens[:])
            return
        for edge in case["nodes"].get(node, {}).get("edges", []):
            if edge.get("traversable") is not True or edge["to"] in seen:
                continue
            if route_token is not None and edge.get("route_token") != route_token:
                continue
            visit(edge["to"], seen | {edge["to"]}, tokens + [edge.get("route_token")])

    visit(start, {start}, [])
    return paths


def expected_observation(case: dict, node_id: str, sequence: int) -> dict:
    node = case["nodes"][node_id]
    out = {
        "node_id": node_id,
        "start_id": case["start"],
        "goal_id": case["goal"],
        "binding": case["binding"],
        "epoch": node["epoch"],
        "sequence": sequence,
        "edges": node["edges"],
    }
    if "closure_receipt" in node:
        out["closure_receipt"] = node["closure_receipt"]
    return out


def replay_row(case: dict, oracle: dict, row: dict, budgets: dict) -> list[str]:
    errors: list[str] = []
    policy = row.get("policy")
    if policy not in POLICIES:
        return ["policy_invalid"]
    current = case["start"]
    path: list[dict] = []
    visited = {current}
    obs_count = 0
    input_count = 0
    sequence = 0
    accepted_class = None
    accepted_alt_tokens: list[str] = []
    excluded_tokens: set[str] = set()
    rejected_receipts: list[str] = []
    trace = row.get("events")
    if not isinstance(trace, list):
        return ["events_not_list"]

    index = 0
    terminal = "UNFINISHED"
    while index < len(trace):
        event = trace[index]
        if not isinstance(event, dict) or event.get("kind") != "OBSERVE":
            errors.append(f"expected_observation:{index}")
            break
        sequence += 1
        obs_count += 1
        obs = event.get("observation")
        expected = expected_observation(case, current, sequence)
        if obs != expected:
            errors.append(f"observation_mismatch:{index}")
            break
        index += 1

        # Evidence classification is independently recomputed from current visible binding,
        # source sequence, topology epoch, and the route receipt already traversed.
        evidence = trace[index] if (policy == "class_aware" and index < len(trace)
                                    and trace[index].get("kind", "").startswith("CLASS_CERTIFICATE_")) else None
        if evidence is not None:
            if policy != "class_aware":
                errors.append("baseline_consumed_class_certificate")
                break
            if evidence.get("sequence") != obs.get("sequence"):
                errors.append("certificate_event_sequence_mismatch")
                break
            current_token = path[0]["route_token"] if path else None
            valid, reason = receipt_status(obs, current_token)
            if evidence.get("kind") == "CLASS_CERTIFICATE_REJECTED":
                if valid or evidence.get("reason") != reason:
                    errors.append("false_certificate_rejection")
                    break
                rejected_receipts.append(reason)
                index += 1
            elif evidence.get("kind") in {"CLASS_CERTIFICATE_ACCEPTED", "CLASS_CERTIFICATE_ACCEPTED_NO_ALTERNATE"}:
                if not valid:
                    errors.append("invalid_certificate_accepted")
                    break
                root = case["nodes"][case["start"]]
                root_tokens = {edge.get("route_token") for edge in root["edges"]
                               if edge.get("traversable") is True}
                alternatives = sorted(root_tokens - {current_token})
                if alternatives:
                    if evidence.get("kind") != "CLASS_CERTIFICATE_ACCEPTED":
                        errors.append("alternate_route_not_used")
                        break
                    if evidence.get("route_token") != current_token or evidence.get("alternative_tokens") != alternatives:
                        errors.append("certificate_alternative_mismatch")
                        break
                    accepted_class = current_token
                    accepted_alt_tokens = alternatives
                    excluded_tokens.add(current_token)
                    index += 1
                else:
                    if evidence.get("kind") != "CLASS_CERTIFICATE_ACCEPTED_NO_ALTERNATE" or evidence.get("route_token") != current_token:
                        errors.append("single_class_certificate_mismatch")
                        break
                    accepted_class = current_token
                    excluded_tokens.add(current_token)
                    index += 1
            else:
                errors.append("unknown_certificate_event")
                break

        if index >= len(trace):
            errors.append("missing_action_after_observation")
            break
        action = trace[index]
        kind = action.get("kind")
        if kind == "TRAVERSE":
            edge = next((item for item in obs["edges"] if item["id"] == action.get("edge_id")
                         and item["to"] == action.get("to")), None)
            if edge is None or edge.get("traversable") is not True:
                errors.append("unsafe_or_unobserved_traverse")
                break
            if action.get("from") != current or action.get("route_token") != edge.get("route_token"):
                errors.append("traverse_source_or_route_mismatch")
                break
            if accepted_class is not None and not path and current == case["start"]:
                if edge.get("route_token") not in accepted_alt_tokens:
                    errors.append("class_switch_not_to_observed_alternative")
                    break
                accepted_class = None
                accepted_alt_tokens = []
            path.append({"from": current, "to": edge["to"], "edge_id": edge["id"],
                         "route_token": edge.get("route_token")})
            current = edge["to"]
            visited.add(current)
            input_count += 1
        elif kind == "BACKTRACK":
            if not path:
                errors.append("backtrack_without_path")
                break
            prior = path.pop()
            if (action.get("from") != current or action.get("to") != prior["from"]
                    or action.get("edge_id") != prior["edge_id"]):
                errors.append("backtrack_receipt_mismatch")
                break
            reason = action.get("reason")
            if reason == "class_switch":
                if policy != "class_aware" or accepted_class is None or not accepted_alt_tokens:
                    errors.append("unsupported_class_switch")
                    break
            elif reason != "visited_edge_exhaustion":
                errors.append("unknown_backtrack_reason")
                break
            current = prior["from"]
            input_count += 1
        elif kind == "YIELD":
            if action.get("node_id") != current or action.get("reason") not in {"NO_ALTERNATE_CLASS", "NO_UNVISITED_SAFE_EDGE"}:
                errors.append("invalid_yield")
                break
            if action.get("reason") == "NO_ALTERNATE_CLASS" and not accepted_class:
                errors.append("yield_without_valid_class_certificate")
                break
            terminal = action["reason"]
            index += 1
            break
        else:
            errors.append(f"unknown_action:{kind}")
            break
        index += 1

    if errors:
        return errors
    target = oracle["target_by_case"][case["id"]]
    expected_success = current == target and terminal == "UNFINISHED"
    if current == target:
        terminal = "GOAL_OBSERVED"
    elif terminal == "UNFINISHED":
        terminal = "OBSERVATION_BUDGET_EXHAUSTED" if obs_count >= budgets["max_observations"] else "INPUT_BUDGET_EXHAUSTED"
    summary = {
        "terminal_node": current,
        "terminal": terminal,
        "goal_observed": expected_success,
        "observations": obs_count,
        "input_actions": input_count,
        "total_counted_events": obs_count + input_count,
        "model_calls": 0,
        "backtracks": sum(e.get("kind") == "BACKTRACK" for e in trace),
        "switch_backtracks": sum(e.get("kind") == "BACKTRACK" and e.get("reason") == "class_switch" for e in trace),
        "visited_nodes": sorted(visited),
        "excluded_route_tokens": sorted(excluded_tokens),
    }
    for key, value in summary.items():
        if row.get(key) != value:
            errors.append(f"summary_mismatch:{key}")
    if obs_count > budgets["max_observations"] or input_count > budgets["max_input_actions"]:
        errors.append("budget_exceeded")
    return errors


def validate_payload(raw: dict, visible: dict, oracle: dict, freeze: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(raw, dict) or set(raw) != RAW_KEYS:
        return ["raw_schema_keys"]
    if raw.get("schema") != "path-class-switching-raw-v1" or raw.get("allocation") != ALLOCATION:
        errors.append("raw_identity")
    if raw.get("main_sha") != MAIN_SHA or freeze.get("main_sha") != MAIN_SHA:
        errors.append("main_sha")
    if raw.get("freeze_sha256") != digest(ROOT / "FREEZE.json"):
        errors.append("freeze_hash")
    if raw.get("visible_fixture_sha256") != digest(ROOT / "fixture_visible.json"):
        errors.append("fixture_hash")
    if raw.get("candidate_sha256") != digest(ROOT / "candidate.py"):
        errors.append("candidate_hash")
    if raw.get("runner_sha256") != digest(ROOT / "run_candidate.py"):
        errors.append("runner_hash")
    for name in HASHED_INPUTS:
        if freeze.get("sha256", {}).get(name) != digest(ROOT / name):
            errors.append(f"frozen_source_hash:{name}")
    expected_case_order = [case["id"] for case in visible["cases"]]
    if raw.get("case_order") != expected_case_order or raw.get("policy_order") != list(POLICIES):
        errors.append("case_or_policy_order")
    budgets = {"max_observations": visible["max_observations"],
               "max_input_actions": visible["max_input_actions"]}
    if raw.get("budget") != {**budgets, "model_calls": 0}:
        errors.append("budget_identity")
    expected_keys = {(case_id, policy) for case_id in expected_case_order for policy in POLICIES}
    rows = raw.get("rows")
    if not isinstance(rows, list) or len(rows) != len(expected_keys) or raw.get("row_count") != len(expected_keys):
        return errors + ["row_count"]
    by_key: dict[tuple[str, str], dict] = {}
    for row in rows:
        key = (row.get("case_id"), row.get("policy")) if isinstance(row, dict) else None
        if key in by_key:
            errors.append("duplicate_row")
        else:
            by_key[key] = row
    if set(by_key) != expected_keys:
        errors.append("row_identity_set")
        return errors
    cases = {case["id"]: case for case in visible["cases"]}
    for key, row in by_key.items():
        errors.extend(f"{key[0]}/{key[1]}:{e}" for e in replay_row(cases[key[0]], oracle, row, budgets))

    primary = oracle["expected_primary_case"]
    primary_rows = {policy: by_key[(primary, policy)] for policy in POLICIES}
    if not all(row["goal_observed"] for row in primary_rows.values()):
        errors.append("primary_correctness_not_equal")
    if not (primary_rows["class_aware"]["total_counted_events"] < primary_rows["novel_cell"]["total_counted_events"]
            and primary_rows["class_aware"]["total_counted_events"] < primary_rows["visited_edge_backtrack"]["total_counted_events"]):
        errors.append("primary_no_strict_budgeted_gain")
    if primary_rows["class_aware"]["switch_backtracks"] != 1:
        errors.append("primary_switch_count")

    for case_id in ("viable_same_class", "same_class_dead_end", "unsupported_false_cue", "dynamic_epoch_invalidation"):
        row = by_key[(case_id, "class_aware")]
        if row["switch_backtracks"] != 0 or not row["goal_observed"]:
            errors.append(f"control_forced_switch_or_lost_goal:{case_id}")
    false_row = by_key[("unsupported_false_cue", "class_aware")]
    dynamic_row = by_key[("dynamic_epoch_invalidation", "class_aware")]
    if not any(e.get("kind") == "CLASS_CERTIFICATE_REJECTED" and e.get("reason") == "binding_mismatch" for e in false_row["events"]):
        errors.append("false_cue_not_rejected")
    if not any(e.get("kind") == "CLASS_CERTIFICATE_REJECTED" and e.get("reason") == "epoch_mismatch" for e in dynamic_row["events"]):
        errors.append("stale_epoch_not_rejected")
    single = by_key[("single_class_no_alternate", "class_aware")]
    if single["switch_backtracks"] != 0 or single["goal_observed"] or single["terminal"] != "NO_ALTERNATE_CLASS":
        errors.append("single_class_forced_or_misclassified")

    # The evaluator verifies its cutset truth independently by enumerating complete graph paths.
    for case_id in oracle["true_cutset_cases"]:
        case = cases[case_id]
        upper_paths = graph_paths(case, case["start"], oracle["target_by_case"][case_id], "upper")
        if upper_paths:
            errors.append(f"oracle_cutset_not_true:{case_id}")
    for case_id in ("viable_same_class", "dynamic_epoch_invalidation"):
        case = cases[case_id]
        if not graph_paths(case, case["start"], oracle["target_by_case"][case_id], "upper"):
            errors.append(f"oracle_viable_class_missing:{case_id}")
    return errors


def mutation_controls(raw: dict, visible: dict, oracle: dict, freeze: dict) -> dict:
    results: dict[str, bool] = {}
    single_index = next(i for i, row in enumerate(raw["rows"])
                        if row["case_id"] == "single_class_no_alternate" and row["policy"] == "class_aware")
    changed = copy.deepcopy(raw)
    changed["rows"][single_index]["goal_observed"] = True
    results["false_goal_claim"] = bool(validate_payload(changed, visible, oracle, freeze))

    blocked_index = next(i for i, row in enumerate(raw["rows"])
                         if row["case_id"] == "blocked_class_gain" and row["policy"] == "visited_edge_backtrack")
    changed = copy.deepcopy(raw)
    changed["rows"][blocked_index]["events"] = [e for e in changed["rows"][blocked_index]["events"]
                                                    if not (e["kind"] == "BACKTRACK" and e["edge_id"] == "d23")]
    results["omitted_reversal"] = bool(validate_payload(changed, visible, oracle, freeze))

    changed = copy.deepcopy(raw)
    changed["oracle"] = {"target_by_case": oracle["target_by_case"]}
    results["oracle_leak_in_raw"] = bool(validate_payload(changed, visible, oracle, freeze))

    changed = copy.deepcopy(raw)
    changed["rows"][0]["total_counted_events"] += 1
    results["cost_laundering"] = bool(validate_payload(changed, visible, oracle, freeze))
    return results


def run(raw_path: Path, out_path: Path) -> dict:
    visible = json.loads((ROOT / "fixture_visible.json").read_text(encoding="utf-8"))
    oracle = json.loads((ROOT / "oracle.json").read_text(encoding="utf-8"))
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    errors = validate_payload(raw, visible, oracle, freeze)
    mutations = mutation_controls(raw, visible, oracle, freeze) if not errors else {}
    pass_gate = not errors and bool(mutations) and all(mutations.values())
    rows = {(row["case_id"], row["policy"]): row for row in raw.get("rows", [])}
    summary = {
        "status": "PASS_METHOD_HOST_SCOPED" if pass_gate else "FAIL_OR_HOLD",
        "allocation": ALLOCATION,
        "main_sha": MAIN_SHA,
        "audited_rows": raw.get("row_count"),
        "errors": errors,
        "mutations_rejected": mutations,
        "primary_metrics": {
            policy: {"goal_observed": rows.get(("blocked_class_gain", policy), {}).get("goal_observed"),
                     "observations": rows.get(("blocked_class_gain", policy), {}).get("observations"),
                     "input_actions": rows.get(("blocked_class_gain", policy), {}).get("input_actions"),
                     "total_counted_events": rows.get(("blocked_class_gain", policy), {}).get("total_counted_events"),
                     "backtracks": rows.get(("blocked_class_gain", policy), {}).get("backtracks")}
            for policy in POLICIES
        },
        "scope": "Finite authored graph method result only; host execution was not container-isolated and establishes no real topological inference, GUI/DOOM behavior, runtime benefit, or product claim.",
    }
    if out_path.exists():
        raise SystemExit("STOP_AUDIT_OUTPUT_ALREADY_EXISTS")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": summary["status"], "audited_rows": summary["audited_rows"],
                      "errors": len(errors), "mutation_controls": mutations}, sort_keys=True))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, default=ROOT / "results" / "a01" / "raw.json")
    parser.add_argument("--out", type=Path, default=ROOT / "results" / "a01" / "audit.json")
    args = parser.parse_args()
    result = run(args.raw, args.out)
    return 0 if result["status"] == "PASS_METHOD_HOST_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
