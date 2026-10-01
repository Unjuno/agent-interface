import copy
import itertools
import json
import sys
from pathlib import Path


def feasible(task, ex, ve):
    execution_ok = ex["domain"] == task["domain"] and ex["authority"] >= task["required_authority"]
    verification_ok = (
        ex["id"] != ve["id"]
        and (ve["evidence_mask"] & task["required_evidence_mask"]) == task["required_evidence_mask"]
        and (not task["high_risk"] or ve["failure_domain"] != ex["failure_domain"])
    )
    return execution_ok and verification_ok


def audit_policy(workload, result, must_be_safe):
    errors = []
    tasks = {t["id"]: t for t in workload["tasks"]}
    agents = {a["id"]: a for a in workload["agents"]}
    used = set()
    seen = set()
    computed = {"unsafe_admissions": 0, "safe_admitted_value": 0, "safe_shortfall_value": 0,
                "selected_cost": 0, "admitted_tasks": 0}
    decisions = result.get("decisions", [])
    if len(decisions) != len(tasks):
        errors.append("decision_cardinality")
    for d in decisions:
        tid = d.get("task_id")
        if tid not in tasks or tid in seen:
            errors.append("task_identity_or_duplicate")
            continue
        seen.add(tid)
        task = tasks[tid]
        if not d.get("admitted"):
            if d.get("executor_id") is not None or d.get("verifier_id") is not None:
                errors.append("unadmitted_has_pair")
            computed["safe_shortfall_value"] += task["value"]
            continue
        computed["admitted_tasks"] += 1
        ex_id, ve_id = d.get("executor_id"), d.get("verifier_id")
        if ex_id not in agents or ve_id not in agents:
            errors.append("unknown_agent")
            continue
        if ex_id == ve_id:
            errors.append("same_agent_two_roles")
        if ex_id in used or ve_id in used:
            errors.append("agent_capacity_reused")
        used.add(ex_id)
        used.add(ve_id)
        safe = feasible(task, agents[ex_id], agents[ve_id])
        if must_be_safe and not safe:
            errors.append("unsafe_admission")
        if d.get("safe") is not safe:
            errors.append("safe_flag_mismatch")
        if safe:
            computed["safe_admitted_value"] += task["value"]
        else:
            computed["unsafe_admissions"] += 1
        expected_cost = workload["bids"][tid][ex_id]["execute"] + workload["bids"][tid][ve_id]["verify"]
        if d.get("cost") != expected_cost:
            errors.append("cost_mismatch")
        computed["selected_cost"] += expected_cost
    if seen != set(tasks):
        errors.append("missing_task")
    if result.get("metrics") != computed:
        errors.append("metric_mismatch")
    return errors, computed


def oracle_value(workload):
    tasks = workload["tasks"]
    agents = sorted(workload["agents"], key=lambda x: x["id"])
    bids = workload["bids"]
    feasible_rows = []
    for task in tasks:
        row = []
        for ei, ex in enumerate(agents):
            exec_ok = ex["domain"] == task["domain"] and ex["authority"] >= task["required_authority"]
            if not exec_ok:
                continue
            for vi, ve in enumerate(agents):
                if ei == vi:
                    continue
                evidence_ok = (ve["evidence_mask"] & task["required_evidence_mask"]) == task["required_evidence_mask"]
                independent = not task["high_risk"] or ve["failure_domain"] != ex["failure_domain"]
                if evidence_ok and independent:
                    cost = bids[task["id"]][ex["id"]]["execute"] + bids[task["id"]][ve["id"]]["verify"]
                    row.append((1 << ei, 1 << vi, cost))
        feasible_rows.append(row)

    states = {0: 0}
    for index, task in enumerate(tasks):
        nxt = dict(states)
        for mask, value in states.items():
            for exbit, vebit, _ in feasible_rows[index]:
                if mask & (exbit | vebit):
                    continue
                newmask = mask | exbit | vebit
                nxt[newmask] = max(nxt.get(newmask, -1), value + task["value"])
        states = nxt
    return max(states.values(), default=0)


def audit_rows(rows):
    errors = []
    if len(rows) != 50:
        errors.append(f"run_count:{len(rows)}")
    totals = {p: {"unsafe_admissions": 0, "safe_admitted_value": 0, "safe_shortfall_value": 0,
                  "selected_cost": 0, "admitted_tasks": 0} for p in
              ("scalar_unconstrained", "value_first", "scarcity_first", "central_oracle")}
    for expected_seed, row in enumerate(rows):
        if row.get("schema") != "issue5407-market-t2-raw-v1":
            errors.append(f"schema:{expected_seed}")
        w = row.get("workload", {})
        if w.get("seed") != expected_seed or len(w.get("tasks", [])) != 8 or len(w.get("agents", [])) != 10:
            errors.append(f"workload_identity:{expected_seed}")
        policies = row.get("policies", {})
        if set(policies) != set(totals):
            errors.append(f"policy_set:{expected_seed}")
            continue
        for policy, result in policies.items():
            errors_policy, metrics = audit_policy(w, result, policy != "scalar_unconstrained")
            if errors_policy:
                errors.append(f"{policy}:{expected_seed}:{','.join(errors_policy)}")
            for key, value in metrics.items():
                totals[policy][key] += value
        optimum = oracle_value(w)
        if policies["central_oracle"]["metrics"]["safe_admitted_value"] != optimum:
            errors.append(f"oracle_not_optimal:{expected_seed}")
        if policies["value_first"]["metrics"]["unsafe_admissions"] != 0 or policies["scarcity_first"]["metrics"]["unsafe_admissions"] != 0:
            errors.append(f"constrained_unsafe:{expected_seed}")
        if optimum < policies["value_first"]["metrics"]["safe_admitted_value"] or optimum < policies["scarcity_first"]["metrics"]["safe_admitted_value"]:
            errors.append(f"oracle_below_greedy:{expected_seed}")
    if len(rows) == 50 and all(x.get("workload", {}).get("seed") == i for i, x in enumerate(rows)):
        rows_mut = copy.deepcopy(rows)
        target = next((r for r in rows_mut if any(d["admitted"] for d in r["policies"]["value_first"]["decisions"])), None)
        if target is None:
            errors.append("unsafe_mutation_setup_missing_assignment")
        else:
            d = next(d for d in target["policies"]["value_first"]["decisions"] if d["admitted"])
            d["verifier_id"] = d["executor_id"]
            w = target["workload"]
            if not audit_policy(w, target["policies"]["value_first"], True)[0]:
                errors.append("unsafe_mutation_accepted")
        rows_mut = copy.deepcopy(rows)
        target = next((r for r in rows_mut if sum(d["admitted"] for d in r["policies"]["value_first"]["decisions"]) >= 2), None)
        if target is None:
            errors.append("capacity_mutation_setup_missing_assignments")
        else:
            assigned = [d for d in target["policies"]["value_first"]["decisions"] if d["admitted"]]
            assigned[1]["executor_id"] = assigned[0]["executor_id"]
            w = target["workload"]
            if not audit_policy(w, target["policies"]["value_first"], True)[0]:
                errors.append("capacity_mutation_accepted")
    return errors, totals


if __name__ == "__main__":
    path = Path(sys.argv[1])
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    errors, totals = audit_rows(rows)
    print(json.dumps({"audit": "PASS" if not errors else "FAIL", "rows": len(rows), "errors": errors,
                      "totals": totals,
                      "criteria": {
                          "scarcity_reduces_shortfall": totals.get("scarcity_first", {}).get("safe_shortfall_value", 0) < totals.get("value_first", {}).get("safe_shortfall_value", 0),
                          "cost_within_125_percent": totals.get("scarcity_first", {}).get("selected_cost", 0) <= 1.25 * max(1, totals.get("value_first", {}).get("selected_cost", 0)),
                      }}, sort_keys=True, indent=2))
    raise SystemExit(0 if not errors else 1)

