import hashlib
import itertools
import json
import sys
from pathlib import Path


ROOT = Path(__file__).parent


def available(route, scenario):
    return not any(dep in scenario["faults"] for dep in route["dependencies"])


def independently_score(tasks, selected, route_index, scenario, budget, use_exact_edges):
    legal = []
    for task in tasks:
        choices = []
        for name in selected:
            route = route_index[name]
            if task["class"] not in route["classes"] or task["class"] not in route["grants"]:
                continue
            if use_exact_edges and route["edge_truth"].get(task["class"]) != "exact":
                continue
            if available(route, scenario):
                choices.append(name)
        legal.append(choices + [None])

    possibilities = []
    for plan in itertools.product(*legal):
        inventory = {}
        ledger = {}
        expenditure = sum(route_index[name]["fixed_cost"] for name in selected)
        viable = True
        for name in selected:
            route = route_index[name]
            free_at = [scenario["reconfigure_ms"] + route["ready_ms"]] * route["capacity"]
            pending = [task for task, allocation in zip(tasks, plan) if allocation == name]
            pending = sorted(pending, key=lambda task: (task["release_ms"], task["deadline_ms"], task["id"]))
            inventory[name] = free_at
            for task in pending:
                lane = min(range(len(free_at)), key=lambda index: (free_at[index], index))
                begin = max(free_at[lane], task["release_ms"])
                end = begin + route["effect_ms"]
                free_at[lane] = end
                if end > task["deadline_ms"]:
                    viable = False
                    break
                ledger[task["id"]] = (name, begin, end)
                expenditure += route["per_use_cost"]
            if not viable:
                break
        if not viable or expenditure > budget:
            continue
        entries = []
        for task in tasks:
            scheduled = ledger.get(task["id"])
            if scheduled is None:
                entries.append({"task": task["id"], "route": None, "start_ms": None, "finish_ms": None, "status": "NO_QUALIFIED_OR_CAPACITY"})
            else:
                name, begin, end = scheduled
                entries.append({"task": task["id"], "route": name, "start_ms": begin, "finish_ms": end, "status": "EXACT_ON_TIME"})
        points = sum(task["weight"] for task in tasks if task["id"] in ledger)
        tie = tuple("~" if route is None else route for route in plan)
        order = (-points, expenditure, sum(item["finish_ms"] or 0 for item in entries), tie)
        possibilities.append((order, {"score": points, "cost": round(expenditure, 6), "rows": entries}))
    if not possibilities:
        raise AssertionError("no feasible assignment, including abstention")
    return min(possibilities, key=lambda item: item[0])[1]


def reconstruct(fixture):
    route_index = {route["id"]: route for route in fixture["routes"]}
    arms = {}
    for label, exact in (("declared_graph", False), ("exact_effect_qualified_graph", True)):
        outcome = {}
        for topology, route_names in fixture["portfolios"].items():
            outcome[topology] = {
                scenario["id"]: independently_score(fixture["tasks"], route_names, route_index, scenario, fixture["budget"], exact)
                for scenario in fixture["scenarios"]
            }
        outcome["aggregate_scores"] = {topology: sum(v["score"] for v in rows.values()) for topology, rows in outcome.items()}
        arms[label] = outcome
    edge_ref = fixture["filter_pair"]["edge"]
    route = route_index[edge_ref["route"]]
    declared = arms["declared_graph"]["aggregate_scores"]
    qualified = arms["exact_effect_qualified_graph"]["aggregate_scores"]
    return {
        "schema": "effect-overlap-same-graph-filter-raw-v1",
        "edge": {**edge_ref, "declared_truth": route["edge_truth"][edge_ref["class"]], "grant_present": edge_ref["class"] in route["grants"], "rejection_reason": fixture["filter_pair"]["rejection_reason"]},
        "only_changed_variable": fixture["filter_pair"]["only_changed_variable"],
        "same_budget": fixture["budget"],
        "same_capacity": fixture["portfolio_capacity"],
        "arms": arms,
        "diagnostic": {
            "declared_partial_over_disjoint": declared["partial_overlap"] - declared["disjoint_specialist"],
            "qualified_partial_over_disjoint": qualified["partial_overlap"] - qualified["disjoint_specialist"],
            "apparent_advantage_disappears": declared["partial_overlap"] > declared["disjoint_specialist"] and qualified["partial_overlap"] == qualified["disjoint_specialist"]
        }
    }


def validate(raw, fixture):
    expected = reconstruct(fixture)
    errors = []
    if raw != expected:
        errors.append("independent_assignment_reconstruction_mismatch")
    if raw.get("diagnostic", {}).get("apparent_advantage_disappears") is not True:
        errors.append("required_filter_negative_control_missing")
    edge = raw.get("edge", {})
    if edge.get("grant_present") is not True or edge.get("declared_truth") != "partial":
        errors.append("control_does_not_isolate_partial_effect_edge")
    for arm in ("declared_graph", "exact_effect_qualified_graph"):
        for topology in ("partial_overlap", "disjoint_specialist"):
            for scenario in fixture["scenarios"]:
                record = raw.get("arms", {}).get(arm, {}).get(topology, {}).get(scenario["id"], {})
                offered = {task["id"] for task in fixture["tasks"]}
                seen = [row.get("task") for row in record.get("rows", [])]
                if set(seen) != offered or len(seen) != len(set(seen)):
                    errors.append("denominator_mismatch:" + arm + ":" + topology + ":" + scenario["id"])
    return sorted(set(errors)), expected


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "formal" / "candidate.json"
    fixture = json.loads((ROOT / "FIXTURE.json").read_text())
    raw = json.loads(path.read_text())
    errors, expected = validate(raw, fixture)
    receipt = {"schema": "effect-overlap-same-graph-filter-audit-v1", "disposition": "PASS_FILTER_CONTROL_SCOPED" if not errors else "FAIL_CONTROL", "errors": errors, "expected_sha256": hashlib.sha256(json.dumps(expected, sort_keys=True, separators=(",", ":")).encode()).hexdigest(), "candidate_sha256": hashlib.sha256(json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()).hexdigest(), "scenario_count": len(fixture["scenarios"])}
    output = ROOT / "formal" / "audit.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
