"""Independent replay and hindsight DP; intentionally does not import candidate.py."""
import copy
import hashlib
import json
from pathlib import Path

ALLOCATION = "ROUTE-SWITCHING-6009-T0-20261001-01"
POLICIES = ("greedy", "sticky", "switch_aware")
SUCCESS_KEYS = {"task_id","status","route","transition_cost","service_cost","decision_cost","effect"}
REFUSAL_KEYS = {"task_id","status","route","proposed_route","transition_cost","service_cost","decision_cost","effect","reason"}
DEADLINE_REFUSAL_KEYS = REFUSAL_KEYS | {"proposed_transition_cost","proposed_service_cost"}


def proven(task, routes):
    return [r for r in routes if task.get("eligible",{}).get(r) == "PASS"
            and task.get("proof",{}).get(r) == "PASS"]


def expected(policy, task, current, routes, tr):
    options = proven(task, routes)
    if not options:
        return None
    if policy == "greedy":
        return min(options, key=lambda r:(task["service"][r],r))
    if policy == "sticky":
        if current in options: return current
        if "A" in options: return "A"
        return min(options, key=lambda r:(task["service"][r],r))
    def score(r):
        move = tr["initial"][r] if current is None else tr["between"][current][r]
        return move+task["service"][r], (r != current), r
    return min(options, key=score)


def replay_one(run, scenario, policy, data):
    errors, route, cost, effects = [], None, 0, []
    rows = run.get("decisions",[])
    if len(rows) > len(scenario["tasks"]): errors.append("extra_decision")
    stopped = None
    for index,(task,row) in enumerate(zip(scenario["tasks"],rows)):
        if row.get("task_id") != task["id"]: errors.append("task_order")
        decision_cost = data["transition"]["decision_cost"]
        if row.get("decision_cost") != decision_cost: errors.append("decision_charge")
        cost += decision_cost
        choice = expected(policy,task,route,data["routes"],data["transition"])
        if row.get("status") == "COMPLETED":
            if set(row) != SUCCESS_KEYS: errors.append("success_schema_or_future_leak")
            chosen = row.get("route")
            if chosen != choice: errors.append("policy_choice")
            if chosen not in proven(task,data["routes"]):
                errors.append("ineligible_or_unproven_route"); break
            move = data["transition"]["initial"][chosen] if route is None else data["transition"]["between"][route][chosen]
            service = task["service"][chosen]
            if cost+move+service > scenario["deadline"]: errors.append("deadline_crossed")
            if row.get("transition_cost") != move: errors.append("transition_charge")
            if row.get("service_cost") != service: errors.append("service_charge")
            if row.get("effect") != task["effect"]: errors.append("effect_mismatch")
            if task["effect"] in effects: errors.append("duplicate_effect")
            cost += move+service
            effects.append(task["effect"])
            route = chosen
        elif row.get("status") == "REFUSED":
            reason = row.get("reason")
            expected_keys = DEADLINE_REFUSAL_KEYS if reason == "DEADLINE_BEFORE_EFFECT" else REFUSAL_KEYS
            if set(row) != expected_keys: errors.append("refusal_schema_or_future_leak")
            if row.get("route") is not None or row.get("effect") is not None:
                errors.append("effect_on_refusal")
            if row.get("transition_cost") != 0 or row.get("service_cost") != 0:
                errors.append("uncharged_refused_work")
            if choice is None:
                if reason != "NO_PROVEN_ROUTE" or row.get("proposed_route") is not None:
                    errors.append("wrong_no_route_stop")
            else:
                move = data["transition"]["initial"][choice] if route is None else data["transition"]["between"][route][choice]
                service = task["service"][choice]
                if row.get("proposed_route") != choice: errors.append("refused_choice")
                if row.get("proposed_transition_cost") != move or row.get("proposed_service_cost") != service:
                    errors.append("refused_estimate")
                if cost+move+service <= scenario["deadline"]: errors.append("premature_refusal")
                if reason != "DEADLINE_BEFORE_EFFECT": errors.append("wrong_stop_reason")
            if index != len(rows)-1: errors.append("rows_after_refusal")
            stopped = reason
            break
        else:
            errors.append("invalid_decision_status")
            break
    complete = (len(rows) == len(scenario["tasks"])
                and all(r.get("status") == "COMPLETED" for r in rows))
    if not complete and (not rows or rows[-1].get("status") != "REFUSED"):
        errors.append("missing_refusal_record")
    terminal = data["transition"]["terminal_to_A"][route] if route else 0
    cost += terminal
    if run.get("terminal_cost") != terminal: errors.append("terminal_charge")
    if run.get("total_cost") != cost: errors.append("total_cost")
    if run.get("complete") != complete: errors.append("complete_flag")
    if run.get("stopped") != (None if complete else stopped): errors.append("stop_status")
    if run.get("effects") != effects: errors.append("effect_ledger")
    if run.get("deadline_met") != (cost <= scenario["deadline"]): errors.append("deadline_flag")
    return errors,cost,complete,effects


def dp_optimum(scenario,data):
    tr,routes=data["transition"],data["routes"]
    layer={None:(0,())}
    for task in scenario["tasks"]:
        nxt={}
        for current,(cost,path) in layer.items():
            for dest in proven(task,routes):
                move=tr["initial"][dest] if current is None else tr["between"][current][dest]
                candidate=(cost+tr["decision_cost"]+move+task["service"][dest],path+(dest,))
                if dest not in nxt or candidate<nxt[dest]: nxt[dest]=candidate
        layer=nxt
    finals=[]
    for route,(cost,path) in layer.items():
        total=cost+(tr["terminal_to_A"][route] if route else 0)
        if total<=scenario["deadline"]: finals.append((total,path))
    return min(finals) if finals else None


def validate(raw,data):
    errors,summaries=[],{}
    canon=json.dumps(data,sort_keys=True,separators=(",",":")).encode()
    if raw.get("schema")!="route-switching-6009-candidate-v1": errors.append("schema")
    if raw.get("allocation")!=ALLOCATION: errors.append("allocation")
    if raw.get("scenario_sha256")!=hashlib.sha256(canon).hexdigest(): errors.append("scenario_hash")
    index={(r.get("scenario_id"),r.get("policy")):r for r in raw.get("runs",[])}
    if len(index)!=len(raw.get("runs",[])): errors.append("duplicate_run")
    for scenario in data["scenarios"]:
        optimum=dp_optimum(scenario,data)
        for policy in POLICIES:
            run=index.get((scenario["id"],policy))
            if run is None:
                errors.append("missing_run:"+scenario["id"]+":"+policy); continue
            errs,cost,complete,effects=replay_one(run,scenario,policy,data)
            errors.extend(scenario["id"]+":"+policy+":"+e for e in errs)
            if complete and optimum and cost<optimum[0]: errors.append("below_dp_bound:"+scenario["id"])
            summaries[scenario["id"]+":"+policy]={"total_cost":cost,"complete":complete,
                "effects":effects,"dp_cost":optimum[0] if optimum else None}
    by={r["scenario_id"]+":"+r["policy"]:r for r in raw.get("runs",[])}
    alt=[by.get("alternating_five:"+p,{}) for p in POLICIES]
    if not(all(x.get("complete") for x in alt)
           and alt[2].get("total_cost",10**9)<alt[0].get("total_cost",-1)
           and alt[2].get("total_cost",10**9)<alt[1].get("total_cost",-1)):
        errors.append("alternating_crossover")
    exp=by.get("binding_expiry:switch_aware",{})
    if not exp.get("complete") or [d.get("route") for d in exp.get("decisions",[])][2:]!=["C","C"]:
        errors.append("expiry_alternate_route")
    proof=by.get("unknown_effect_proof:switch_aware",{})
    if not proof.get("complete") or any(d.get("route")=="C" for d in proof.get("decisions",[])):
        errors.append("unknown_proof_used")
    deadline=by.get("deadline_no_safe_completion:switch_aware",{})
    if deadline.get("effects")!=[] or deadline.get("stopped")!="DEADLINE_BEFORE_EFFECT":
        errors.append("deadline_fail_closed")
    return errors,summaries


def mutation_controls(raw,data):
    results={}
    def reject(name,mutant): results[name]=bool(validate(mutant,data)[0])
    m=copy.deepcopy(raw); m["runs"][0]["decisions"][0]["transition_cost"]-=1
    reject("omitted_transition_charge",m)
    m=copy.deepcopy(raw); m["runs"][0]["decisions"][0]["future_task_ids"]=["hidden"]
    reject("future_task_leak",m)
    m=copy.deepcopy(raw)
    next(r for r in m["runs"] if r["scenario_id"]=="binding_expiry" and r["policy"]=="switch_aware")["decisions"][2]["route"]="B"
    reject("unknown_binding_used",m)
    m=copy.deepcopy(raw)
    next(r for r in m["runs"] if r["scenario_id"]=="unknown_effect_proof" and r["policy"]=="switch_aware")["decisions"][0]["route"]="C"
    reject("speed_over_missing_proof",m)
    return results


if __name__ == "__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--scenarios",default=str(Path(__file__).with_name("scenarios.json")))
    parser.add_argument("--candidate",required=True); parser.add_argument("--out",required=True)
    args=parser.parse_args()
    data=json.loads(Path(args.scenarios).read_text(encoding="utf-8"))
    raw=json.loads(Path(args.candidate).read_text(encoding="utf-8"))
    errors,summaries=validate(raw,data); mutations=mutation_controls(raw,data)
    passed=not errors and all(mutations.values())
    result={"schema":"route-switching-6009-audit-v1",
      "status":"PASS_METHOD_SCOPED" if passed else "FAIL_METHOD",
      "allocation":ALLOCATION,"errors":errors,"mutation_controls":mutations,
      "mutation_controls_passed":sum(mutations.values()),"summaries":summaries}
    Path(args.out).write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
