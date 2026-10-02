import itertools
import json
from pathlib import Path


ROOT = Path(__file__).parent


def topology(routes, classes):
    sets = [frozenset(r["classes"]) for r in routes]
    all_classes = frozenset(classes)
    if any(s == all_classes for s in sets):
        return "exact_copies" if len(sets) > 1 and all(s == all_classes for s in sets) else "universal_fallback"
    if len(sets) == 1:
        return "infeasible"
    if sets[0] == sets[1]:
        return "exact_copies"
    if sets[0].isdisjoint(sets[1]):
        return "disjoint_specialists"
    return "partial_overlap"


def portfolios(routes, classes, fixed_budget, capacity):
    out = {k: [] for k in ("exact_copies", "disjoint_specialists", "partial_overlap", "universal_fallback")}
    for size in (1, 2):
        for group in itertools.combinations(routes, size):
            if sum(r["fixed_cost"] for r in group) > fixed_budget:
                continue
            if sum(r["capacity"] for r in group) != capacity:
                continue
            kind = topology(group, classes)
            if kind in out:
                out[kind].append(tuple(sorted(r["id"] for r in group)))
    for key in out:
        out[key] = sorted(set(out[key]))
    return out


def ready_time(route, scenario):
    lost = set(scenario["faults"])
    hit = bool(set(route["dependencies"]) & lost)
    if scenario["kind"] == "permanent":
        if hit:
            return None
        recovery = scenario["reconfigure_ms"] if lost else 0
    elif scenario["kind"] == "transient":
        recovery = scenario["duration_ms"] if hit else (scenario["reconfigure_ms"] if lost else 0)
    else:
        recovery = 0
    return recovery + route["ready_ms"]


def candidate_choices(task, group, route_map, scenario):
    if task["state"] != "uncommitted" or not task["authorized"] or task["effect_truth"] != "exact":
        return []
    choices = []
    for rid in group:
        route = route_map[rid]
        if route["edge_truth"].get(task["class"]) != "exact":
            continue
        if task["class"] not in route["grants"]:
            continue
        if ready_time(route, scenario) is not None:
            choices.append(rid)
    return sorted(choices)


def evaluate_assignment(tasks, group, assignment, route_map, scenario, budget):
    slots = {}
    for rid in group:
        route = route_map[rid]
        slots[rid] = [ready_time(route, scenario)] * route["capacity"]
    rows = []
    total_cost = sum(route_map[r]["fixed_cost"] for r in group)
    completions = 0
    chosen_by_route = {rid: [] for rid in group}
    for task, rid in zip(tasks, assignment):
        if rid is not None:
            chosen_by_route[rid].append(task)
    for rid, assigned in chosen_by_route.items():
        route = route_map[rid]
        for task in sorted(assigned, key=lambda x: (x["release_ms"], x["deadline_ms"], x["id"])):
            worker = min(range(len(slots[rid])), key=lambda i: (slots[rid][i], i))
            start = max(slots[rid][worker], task["release_ms"])
            finish = start + route["effect_ms"]
            slots[rid][worker] = finish
            rows.append((task["id"], rid, start, finish))
            total_cost += route["per_use_cost"]
            if finish > task["deadline_ms"]:
                return None
            completions += task["weight"]
    if total_cost > budget + 1e-9:
        return None
    by_task = {task_id: (rid, start, finish) for task_id, rid, start, finish in rows}
    result_rows = []
    for task in tasks:
        item = by_task.get(task["id"])
        if item:
            rid, start, finish = item
            result_rows.append({"task": task["id"], "route": rid, "start_ms": start, "finish_ms": finish, "status": "EXACT_ON_TIME"})
        else:
            result_rows.append({"task": task["id"], "route": None, "start_ms": None, "finish_ms": None, "status": abstention_reason(task, group, route_map, scenario)})
    return {"score": completions, "cost": round(total_cost, 6), "completion_sum_ms": sum(r["finish_ms"] for r in result_rows if r["finish_ms"] is not None), "rows": result_rows}


def abstention_reason(task, group, route_map, scenario):
    if task["state"] != "uncommitted":
        return "ALREADY_COMMITTED_NO_REPLAY"
    if not task["authorized"]:
        return "UNAUTHORIZED"
    if task["effect_truth"] != "exact":
        return "EFFECT_UNKNOWN_OR_PARTIAL"
    routes = [route_map[r] for r in group]
    exact = [r for r in routes if r["edge_truth"].get(task["class"]) == "exact" and task["class"] in r["grants"]]
    if not exact:
        return "NO_EXACT_AUTHORIZED_EDGE"
    viable = [ready_time(r, scenario) for r in exact]
    if all(t is None for t in viable):
        return "NO_SURVIVING_ROUTE"
    earliest = min(max(t, task["release_ms"]) + r["effect_ms"] for t, r in zip(viable, exact) if t is not None)
    if earliest > task["deadline_ms"]:
        return "MISSED_DEADLINE_POTENTIAL_ONLY"
    return "CAPACITY_CONTENTION"


def solve(tasks, group, route_map, scenario, budget):
    options = [candidate_choices(task, group, route_map, scenario) + [None] for task in tasks]
    candidates = []
    for assignment in itertools.product(*options):
        result = evaluate_assignment(tasks, group, assignment, route_map, scenario, budget)
        if result is not None:
            tie = tuple("~" if r is None else r for r in assignment)
            candidates.append(((-result["score"], result["cost"], result["completion_sum_ms"], tie), result))
    return min(candidates, key=lambda x: x[0])[1]


def mark_reassignment(nominal, result, scenario):
    planned = {row["task"]: row["route"] for row in nominal["rows"]}
    for row in result["rows"]:
        prev = planned.get(row["task"])
        row["planned_route"] = prev
        row["reassigned"] = row["route"] is not None and row["route"] != prev
    result["reconfigure_ms"] = scenario["reconfigure_ms"]
    result["recovery_mode"] = "RESUME_AFTER_RECOVERY" if scenario["kind"] == "transient" and scenario.get("resume_existing") else ("REROUTE_AFTER_RECONFIG" if scenario["faults"] else "NOMINAL")
    return result


def optimize(routes, tasks, scenarios, fixture):
    route_map = {r["id"]: r for r in routes}
    candidates = portfolios(routes, fixture["classes"], fixture["fixed_budget"], fixture["portfolio_capacity"])
    result = {}
    for kind, groups in candidates.items():
        scored = []
        for group in groups:
            rows = [solve(tasks, group, route_map, scenario, fixture["cost_budget"]) for scenario in scenarios]
            # A design class is comparable only if its candidate can cover the complete offered task mix in nominal conditions.
            nominal = next((rows[i] for i, s in enumerate(scenarios) if s["id"] == "no_fault"), None)
            if nominal is None or nominal["score"] != sum(t["weight"] for t in tasks):
                continue
            scored.append({"portfolio": list(group), "fixed_cost": sum(route_map[r]["fixed_cost"] for r in group), "total_capacity": sum(route_map[r]["capacity"] for r in group), "training_score": sum(x["score"] for x in rows), "scenario_scores": {s["id"]: x["score"] for s, x in zip(scenarios, rows)}, "training_results": {s["id"]: mark_reassignment(nominal, x, s) for s, x in zip(scenarios, rows)}, "completion_sum_ms": sum(x["completion_sum_ms"] for x in rows)})
        if not scored:
            result[kind] = {"status": "INCOMPARABLE", "feasible_designs": 0, "designs": [], "winner": None}
            continue
        scored.sort(key=lambda x: (-x["training_score"], x["completion_sum_ms"], x["portfolio"]))
        winner = scored[0]["portfolio"]
        nominal = solve(tasks, winner, route_map, next(s for s in scenarios if s["id"] == "no_fault"), fixture["cost_budget"])
        heldout = {s["id"]: mark_reassignment(nominal, solve(tasks + s.get("extra_tasks", []), winner, route_map, s, fixture["cost_budget"]), s) for s in fixture["heldout_scenarios"]}
        result[kind] = {"status": "OPTIMIZED", "feasible_designs": len(scored), "designs": scored, "winner": winner, "heldout": heldout}
    return result


def run(fixture):
    base = optimize(fixture["route_options"], fixture["tasks"], fixture["training_scenarios"], fixture)
    route_map = {r["id"]: r for r in fixture["route_options"]}
    dominance_routes = fixture["route_options"] + [fixture["dominance_control_route"]]
    dominance_map = {r["id"]: r for r in dominance_routes}
    dominance_rows = []
    u = fixture["dominance_control_route"]["id"]
    for group in portfolios(dominance_routes, fixture["classes"], fixture["fixed_budget"], fixture["portfolio_capacity"])["partial_overlap"]:
        for scenario in fixture["training_scenarios"]:
            pscore = solve(fixture["tasks"], group, dominance_map, scenario, fixture["cost_budget"])["score"]
            uscore = solve(fixture["tasks"], (u,), dominance_map, scenario, fixture["cost_budget"])["score"]
            dominance_rows.append({"portfolio": list(group), "scenario": scenario["id"], "partial_score": pscore, "universal_score": uscore, "partial_strictly_better": pscore > uscore})
    pos = fixture["positive_bottleneck_control"]
    pos_map = {r["id"]: r for r in pos["routes"]}
    pos_tasks = fixture["tasks"]
    pos_rows = {}
    for kind, ids in pos["portfolios"].items():
        nominal = solve(pos_tasks, tuple(ids), pos_map, pos["scenarios"][0], pos["budget"])
        pos_rows[kind] = {s["id"]: mark_reassignment(nominal, solve(pos_tasks, tuple(ids), pos_map, s, pos["budget"]), s) for s in pos["scenarios"]}
    pos_scores = {kind: sum(v["score"] for v in rows.values()) for kind, rows in pos_rows.items()}
    return {"schema":"effect-overlap-portfolio-raw-v2","training_optimization":base,"dominance_control":dominance_rows,"positive_bottleneck_control":{"scenario_results":pos_rows,"aggregate_scores":pos_scores,"same_fixed_cost":True,"same_total_capacity":True},"hard_release":{"id":fixture["hard_release"]["id"],"issued_ms":fixture["hard_release"]["issue_ms"],"completed_ms":fixture["hard_release"]["issue_ms"],"state":fixture["hard_release"]["required_state"],"deadline_ms":fixture["hard_release"]["deadline_ms"]}}


def main():
    fixture = json.loads((ROOT / "FIXTURE.json").read_text())
    out = ROOT / "formal"
    out.mkdir(exist_ok=True)
    (out / "candidate.json").write_text(json.dumps(run(fixture), indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
