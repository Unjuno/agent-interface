import itertools
import json
from pathlib import Path


ROOT = Path(__file__).parent


def ready(route, scenario):
    if set(route["dependencies"]) & set(scenario["faults"]):
        return None
    return scenario["reconfigure_ms"] + route["ready_ms"]


def assignment(tasks, ids, route_map, scenario, fixture, declared_only):
    options = []
    for task in tasks:
        eligible = []
        for rid in ids:
            route = route_map[rid]
            if task["class"] not in route["classes"] or task["class"] not in route["grants"]:
                continue
            if not declared_only and route["edge_truth"].get(task["class"]) != "exact":
                continue
            if ready(route, scenario) is not None:
                eligible.append(rid)
        options.append(eligible + [None])
    candidates = []
    for choices in itertools.product(*options):
        slots = {rid: [ready(route_map[rid], scenario)] * route_map[rid]["capacity"] for rid in ids}
        results = {}
        cost = sum(route_map[rid]["fixed_cost"] for rid in ids)
        valid = True
        for rid in ids:
            assigned = [t for t, chosen in zip(tasks, choices) if chosen == rid]
            assigned.sort(key=lambda t: (t["release_ms"], t["deadline_ms"], t["id"]))
            for task in assigned:
                worker = min(range(len(slots[rid])), key=lambda i: (slots[rid][i], i))
                start = max(slots[rid][worker], task["release_ms"])
                finish = start + route_map[rid]["effect_ms"]
                slots[rid][worker] = finish
                if finish > task["deadline_ms"]:
                    valid = False
                    break
                results[task["id"]] = {"route": rid, "start_ms": start, "finish_ms": finish, "status": "EXACT_ON_TIME"}
                cost += route_map[rid]["per_use_cost"]
            if not valid:
                break
        if not valid or cost > fixture["budget"]:
            continue
        rows = [{"task": t["id"], **results.get(t["id"], {"route": None, "start_ms": None, "finish_ms": None, "status": "NO_QUALIFIED_OR_CAPACITY"})} for t in tasks]
        score = sum(t["weight"] for t in tasks if t["id"] in results)
        key = (-score, cost, sum(r["finish_ms"] or 0 for r in rows), tuple("~" if x is None else x for x in choices))
        candidates.append((key, {"score": score, "cost": round(cost, 6), "rows": rows}))
    return min(candidates, key=lambda x: x[0])[1]


def run(fixture):
    route_map = {r["id"]: r for r in fixture["routes"]}
    outputs = {}
    for mode, declared_only in (("declared_graph", True), ("exact_effect_qualified_graph", False)):
        by_class = {}
        for kind, ids in fixture["portfolios"].items():
            by_class[kind] = {s["id"]: assignment(fixture["tasks"], ids, route_map, s, fixture, declared_only) for s in fixture["scenarios"]}
        by_class["aggregate_scores"] = {kind: sum(x["score"] for x in rows.values()) for kind, rows in by_class.items()}
        outputs[mode] = by_class
    declared = outputs["declared_graph"]["aggregate_scores"]
    qualified = outputs["exact_effect_qualified_graph"]["aggregate_scores"]
    return {
        "schema": "effect-overlap-same-graph-filter-raw-v1",
        "edge": {**fixture["filter_pair"]["edge"], "declared_truth": route_map[fixture["filter_pair"]["edge"]["route"]]["edge_truth"][fixture["filter_pair"]["edge"]["class"]], "grant_present": fixture["filter_pair"]["edge"]["class"] in route_map[fixture["filter_pair"]["edge"]["route"]]["grants"], "rejection_reason": fixture["filter_pair"]["rejection_reason"]},
        "only_changed_variable": fixture["filter_pair"]["only_changed_variable"],
        "same_budget": fixture["budget"],
        "same_capacity": fixture["portfolio_capacity"],
        "arms": outputs,
        "diagnostic": {
            "declared_partial_over_disjoint": declared["partial_overlap"] - declared["disjoint_specialist"],
            "qualified_partial_over_disjoint": qualified["partial_overlap"] - qualified["disjoint_specialist"],
            "apparent_advantage_disappears": declared["partial_overlap"] > declared["disjoint_specialist"] and qualified["partial_overlap"] == qualified["disjoint_specialist"]
        }
    }


def main():
    fixture = json.loads((ROOT / "FIXTURE.json").read_text())
    out = ROOT / "formal" / "candidate.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(run(fixture), indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
