import hashlib
import itertools
import json
import sys
from pathlib import Path


ROOT = Path(__file__).parent


def class_of(rs, all_classes):
    covers = [set(x["classes"]) for x in rs]
    all_classes = set(all_classes)
    if any(x == all_classes for x in covers):
        return "exact_copies" if len(covers) > 1 and all(x == all_classes for x in covers) else "universal_fallback"
    if len(rs) == 1:
        return None
    if covers[0] == covers[1]:
        return "exact_copies"
    if not covers[0].isdisjoint(covers[1]):
        return "partial_overlap"
    return "disjoint_specialists"


def make_designs(route_list, fixture):
    found = {x: [] for x in ("exact_copies", "disjoint_specialists", "partial_overlap", "universal_fallback")}
    for n in range(1, 3):
        for rs in itertools.combinations(route_list, n):
            if sum(r["fixed_cost"] for r in rs) > fixture["fixed_budget"]:
                continue
            if sum(r["capacity"] for r in rs) != fixture["portfolio_capacity"]:
                continue
            typ = class_of(rs, fixture["classes"])
            if typ:
                found[typ].append(tuple(sorted(r["id"] for r in rs)))
    return {k: sorted(set(v)) for k, v in found.items()}


def available_at(r, s):
    intersection = set(r["dependencies"]) & set(s["faults"])
    if s["kind"] == "permanent":
        if intersection:
            return None
        return r["ready_ms"] + (s["reconfigure_ms"] if s["faults"] else 0)
    if s["kind"] == "transient":
        return r["ready_ms"] + (s["duration_ms"] if intersection else (s["reconfigure_ms"] if s["faults"] else 0))
    return r["ready_ms"]


def task_routes(t, ids, by_id, s):
    if not t["authorized"] or t["state"] != "uncommitted" or t["effect_truth"] != "exact":
        return []
    eligible = []
    for rid in ids:
        r = by_id[rid]
        if r["edge_truth"].get(t["class"]) == "exact" and t["class"] in r["grants"] and available_at(r, s) is not None:
            eligible.append(rid)
    return sorted(eligible)


def reason_for(t, ids, by_id, s):
    if t["state"] != "uncommitted":
        return "ALREADY_COMMITTED_NO_REPLAY"
    if not t["authorized"]:
        return "UNAUTHORIZED"
    if t["effect_truth"] != "exact":
        return "EFFECT_UNKNOWN_OR_PARTIAL"
    eligible = [by_id[x] for x in ids if by_id[x]["edge_truth"].get(t["class"]) == "exact" and t["class"] in by_id[x]["grants"]]
    if not eligible:
        return "NO_EXACT_AUTHORIZED_EDGE"
    starts = [available_at(r, s) for r in eligible]
    if all(x is None for x in starts):
        return "NO_SURVIVING_ROUTE"
    best = min(max(x, t["release_ms"]) + r["effect_ms"] for x, r in zip(starts, eligible) if x is not None)
    if best > t["deadline_ms"]:
        return "MISSED_DEADLINE_POTENTIAL_ONLY"
    return "CAPACITY_CONTENTION"


def score(tlist, ids, by_id, s, budget):
    options = [task_routes(t, ids, by_id, s) + [None] for t in tlist]
    candidates = []
    for decisions in itertools.product(*options):
        server_clocks = {rid: [available_at(by_id[rid], s)] * by_id[rid]["capacity"] for rid in ids}
        todo = {rid: [] for rid in ids}
        for t, d in zip(tlist, decisions):
            if d is not None:
                todo[d].append(t)
        task_out = {}
        spend = sum(by_id[rid]["fixed_cost"] for rid in ids)
        total_finish = 0
        invalid = False
        for rid in ids:
            r = by_id[rid]
            for t in sorted(todo[rid], key=lambda z: (z["release_ms"], z["deadline_ms"], z["id"])):
                k = min(range(len(server_clocks[rid])), key=lambda q: (server_clocks[rid][q], q))
                begin = max(server_clocks[rid][k], t["release_ms"])
                done = begin + r["effect_ms"]
                if done > t["deadline_ms"]:
                    invalid = True
                    break
                server_clocks[rid][k] = done
                task_out[t["id"]] = {"task": t["id"], "route": rid, "start_ms": begin, "finish_ms": done, "status": "EXACT_ON_TIME"}
                spend += r["per_use_cost"]
                total_finish += done
            if invalid:
                break
        if invalid or spend > budget + 1e-9:
            continue
        rows = []
        for t in tlist:
            rows.append(task_out.get(t["id"], {"task": t["id"], "route": None, "start_ms": None, "finish_ms": None, "status": reason_for(t, ids, by_id, s)}))
        assignment_key = tuple("~" if x is None else x for x in decisions)
        score_value = sum(t["weight"] for t in tlist if t["id"] in task_out)
        candidates.append(((-score_value, spend, total_finish, assignment_key), {"score": score_value, "cost": round(spend, 6), "completion_sum_ms": total_finish, "rows": rows}))
    return min(candidates, key=lambda x: x[0])[1]


def annotate_recovery(before, after, scenario):
    old_route = {x["task"]: x["route"] for x in before["rows"]}
    for row in after["rows"]:
        old = old_route.get(row["task"])
        row["planned_route"] = old
        row["reassigned"] = row["route"] is not None and row["route"] != old
    after["reconfigure_ms"] = scenario["reconfigure_ms"]
    after["recovery_mode"] = "RESUME_AFTER_RECOVERY" if scenario["kind"] == "transient" and scenario.get("resume_existing") else ("REROUTE_AFTER_RECONFIG" if scenario["faults"] else "NOMINAL")
    return after


def optimize(route_list, fixture):
    by_id = {r["id"]: r for r in route_list}
    all_designs = make_designs(route_list, fixture)
    result = {}
    for typ, designs in all_designs.items():
        scored = []
        for ids in designs:
            runs = [score(fixture["tasks"], ids, by_id, s, fixture["cost_budget"]) for s in fixture["training_scenarios"]]
            no_fault_i = next((i for i, s in enumerate(fixture["training_scenarios"]) if s["id"] == "no_fault"), None)
            if no_fault_i is None or runs[no_fault_i]["score"] != sum(t["weight"] for t in fixture["tasks"]):
                continue
            scored.append({"portfolio": list(ids), "fixed_cost": sum(by_id[x]["fixed_cost"] for x in ids), "total_capacity": sum(by_id[x]["capacity"] for x in ids), "training_score": sum(x["score"] for x in runs), "scenario_scores": {s["id"]: x["score"] for s, x in zip(fixture["training_scenarios"], runs)}, "training_results": {s["id"]: annotate_recovery(runs[no_fault_i], x, s) for s, x in zip(fixture["training_scenarios"], runs)}, "completion_sum_ms": sum(x["completion_sum_ms"] for x in runs)})
        if not scored:
            result[typ] = {"status": "INCOMPARABLE", "feasible_designs": 0, "designs": [], "winner": None}
            continue
        scored.sort(key=lambda z: (-z["training_score"], z["completion_sum_ms"], z["portfolio"]))
        win = scored[0]["portfolio"]
        nominal = score(fixture["tasks"], win, by_id, fixture["training_scenarios"][no_fault_i], fixture["cost_budget"])
        held = {s["id"]: annotate_recovery(nominal, score(fixture["tasks"] + s.get("extra_tasks", []), win, by_id, s, fixture["cost_budget"]), s) for s in fixture["heldout_scenarios"]}
        result[typ] = {"status": "OPTIMIZED", "feasible_designs": len(scored), "designs": scored, "winner": win, "heldout": held}
    return result


def expected(fixture):
    route_list = fixture["route_options"]
    base = optimize(route_list, fixture)
    dom = route_list + [fixture["dominance_control_route"]]
    dm = {r["id"]: r for r in dom}
    u = fixture["dominance_control_route"]["id"]
    dominance = []
    for ids in make_designs(dom, fixture)["partial_overlap"]:
        for s in fixture["training_scenarios"]:
            partial = score(fixture["tasks"], ids, dm, s, fixture["cost_budget"])["score"]
            universal = score(fixture["tasks"], (u,), dm, s, fixture["cost_budget"])["score"]
            dominance.append({"portfolio": list(ids), "scenario": s["id"], "partial_score": partial, "universal_score": universal, "partial_strictly_better": partial > universal})
    pos = fixture["positive_bottleneck_control"]
    pm = {r["id"]: r for r in pos["routes"]}
    pos_results = {}
    for kind, ids in pos["portfolios"].items():
        nominal = score(fixture["tasks"], tuple(ids), pm, pos["scenarios"][0], pos["budget"])
        pos_results[kind] = {s["id"]: annotate_recovery(nominal, score(fixture["tasks"], tuple(ids), pm, s, pos["budget"]), s) for s in pos["scenarios"]}
    pos_totals = {kind: sum(v["score"] for v in rows.values()) for kind, rows in pos_results.items()}
    hard = fixture["hard_release"]
    release = {"id": hard["id"], "issued_ms": hard["issue_ms"], "completed_ms": hard["issue_ms"], "state": hard["required_state"], "deadline_ms": hard["deadline_ms"]}
    return {"schema":"effect-overlap-portfolio-raw-v2","training_optimization":base,"dominance_control":dominance,"positive_bottleneck_control":{"scenario_results":pos_results,"aggregate_scores":pos_totals,"same_fixed_cost":True,"same_total_capacity":True},"hard_release":release}


def validate(raw, fixture):
    exp = expected(fixture)
    errors = []
    if raw != exp:
        for key in exp:
            if raw.get(key) != exp[key]:
                errors.append("mismatch:" + key)
    for item in raw.get("dominance_control", []):
        if item["partial_strictly_better"]:
            errors.append("universal_dominance_violated:" + item["scenario"])
    pos = raw.get("positive_bottleneck_control", {}).get("aggregate_scores", {})
    if pos.get("partial_overlap", 0) <= pos.get("disjoint_specialist", 0):
        errors.append("positive_contention_control_not_discriminating")
    release = raw.get("hard_release", {})
    if release.get("completed_ms", 999) > release.get("deadline_ms", -1):
        errors.append("mandatory_release_late")
    return sorted(set(errors)), exp


def main():
    raw_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "formal" / "candidate.json"
    fixture = json.loads((ROOT / "FIXTURE.json").read_text())
    raw = json.loads(raw_path.read_text())
    errors, exp = validate(raw, fixture)
    result = {"schema":"effect-overlap-portfolio-audit-v2","errors":errors,"disposition":"PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT_GATE","expected_sha256":hashlib.sha256(json.dumps(exp,sort_keys=True,separators=(",",":")).encode()).hexdigest(),"scenario_count":len(fixture["training_scenarios"])+len(fixture["heldout_scenarios"]),"topology_classes":list(exp["training_optimization"])}
    out = ROOT / "formal" / "audit.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
