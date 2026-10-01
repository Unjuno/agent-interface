import argparse
import functools
import itertools
import json
import random
from pathlib import Path


def make_workload(seed, task_count, agent_count):
    rng = random.Random(5_407_000 + seed)
    agents = []
    for i in range(agent_count):
        agents.append({
            "id": f"a{i}",
            "domain": rng.randrange(3),
            "authority": rng.randrange(3),
            "evidence_mask": rng.randrange(1, 8),
            "failure_domain": rng.randrange(5),
            "execute_cost": rng.randrange(1, 16),
            "verify_cost": rng.randrange(1, 8),
        })
    tasks = []
    for i in range(task_count):
        tasks.append({
            "id": f"t{i}",
            "domain": rng.randrange(3),
            "required_authority": rng.randrange(1, 3),
            "required_evidence_mask": rng.randrange(1, 8),
            "high_risk": rng.random() < 0.45,
            "value": rng.randrange(1, 21),
        })
    bids = {}
    for task in tasks:
        bids[task["id"]] = {}
        for agent in agents:
            bids[task["id"]][agent["id"]] = {
                "execute": agent["execute_cost"] + rng.randrange(0, 4),
                "verify": agent["verify_cost"] + rng.randrange(0, 3),
            }
    return {"seed": seed, "tasks": tasks, "agents": agents, "bids": bids}


def execute_ok(task, agent):
    return agent["domain"] == task["domain"] and agent["authority"] >= task["required_authority"]


def verify_ok(task, executor, verifier):
    return (
        executor["id"] != verifier["id"]
        and (verifier["evidence_mask"] & task["required_evidence_mask"]) == task["required_evidence_mask"]
        and (not task["high_risk"] or verifier["failure_domain"] != executor["failure_domain"])
    )


def ordered_pairs(task, agents, bids, feasible_only):
    out = []
    for ex, ve in itertools.permutations(agents, 2):
        if feasible_only and not (execute_ok(task, ex) and verify_ok(task, ex, ve)):
            continue
        cost = bids[task["id"]][ex["id"]]["execute"] + bids[task["id"]][ve["id"]]["verify"]
        out.append((cost, ex["id"], ve["id"]))
    return sorted(out)


def summarize(policy, workload, assignments):
    tasks = {x["id"]: x for x in workload["tasks"]}
    agents = {x["id"]: x for x in workload["agents"]}
    result = []
    for task_id, pair in assignments:
        task = tasks[task_id]
        if pair is None:
            result.append({"task_id": task_id, "admitted": False, "executor_id": None, "verifier_id": None})
            continue
        ex = agents[pair["executor_id"]]
        ve = agents[pair["verifier_id"]]
        safe = execute_ok(task, ex) and verify_ok(task, ex, ve)
        cost = workload["bids"][task_id][ex["id"]]["execute"] + workload["bids"][task_id][ve["id"]]["verify"]
        result.append({
            "task_id": task_id,
            "admitted": True,
            "executor_id": ex["id"],
            "verifier_id": ve["id"],
            "safe": safe,
            "cost": cost,
        })
    unsafe = sum(1 for r in result if r["admitted"] and not r["safe"])
    safe_value = sum(tasks[r["task_id"]]["value"] for r in result if r["admitted"] and r["safe"])
    shortfall = sum(tasks[r["task_id"]]["value"] for r in result if not r["admitted"])
    total_cost = sum(r["cost"] for r in result if r["admitted"])
    return {"policy": policy, "decisions": result, "metrics": {
        "unsafe_admissions": unsafe,
        "safe_admitted_value": safe_value,
        "safe_shortfall_value": shortfall,
        "selected_cost": total_cost,
        "admitted_tasks": sum(1 for r in result if r["admitted"]),
    }}


def scalar_policy(workload):
    tasks = sorted(workload["tasks"], key=lambda t: (-t["value"], t["id"]))
    agents = workload["agents"]
    remaining = {a["id"] for a in agents}
    amap = {a["id"]: a for a in agents}
    assignments = []
    for task in tasks:
        available = [a for a in agents if a["id"] in remaining]
        pairs = ordered_pairs(task, available, workload["bids"], False)
        if not pairs:
            assignments.append((task["id"], None))
        else:
            _, ex, ve = pairs[0]
            remaining.remove(ex)
            remaining.remove(ve)
            assignments.append((task["id"], {"executor_id": ex, "verifier_id": ve}))
    return summarize("scalar_unconstrained", workload, assignments)


def constrained_greedy(workload, scarcity_first):
    tasks = list(workload["tasks"])
    agents = workload["agents"]
    remaining = {a["id"] for a in agents}
    amap = {a["id"]: a for a in agents}
    assignments = {}
    while tasks:
        available = [a for a in agents if a["id"] in remaining]
        choices = []
        for task in tasks:
            pairs = ordered_pairs(task, available, workload["bids"], True)
            choices.append((task, pairs))
        if scarcity_first:
            task, pairs = min(choices, key=lambda x: (len(x[1]), -x[0]["value"], x[0]["id"]))
        else:
            task, pairs = min(choices, key=lambda x: (-x[0]["value"], x[0]["id"]))
        tasks.remove(task)
        if not pairs:
            assignments[task["id"]] = None
            continue
        _, ex, ve = pairs[0]
        remaining.remove(ex)
        remaining.remove(ve)
        assignments[task["id"]] = {"executor_id": ex, "verifier_id": ve}
    return summarize("scarcity_first" if scarcity_first else "value_first", workload,
                     [(t["id"], assignments[t["id"]]) for t in workload["tasks"]])


def oracle_policy(workload):
    tasks = workload["tasks"]
    agents = workload["agents"]
    by_id = {a["id"]: a for a in agents}
    pair_rows = [ordered_pairs(t, agents, workload["bids"], True) for t in tasks]

    @functools.lru_cache(None)
    def solve(index, used_mask):
        if index == len(tasks):
            return (0, 0, ())
        task = tasks[index]
        best = solve(index + 1, used_mask)
        for cost, ex_id, ve_id in pair_rows[index]:
            ex_bit = 1 << int(ex_id[1:])
            ve_bit = 1 << int(ve_id[1:])
            if used_mask & (ex_bit | ve_bit):
                continue
            value, subcost, picks = solve(index + 1, used_mask | ex_bit | ve_bit)
            candidate = (value + task["value"], subcost + cost, ((task["id"], ex_id, ve_id),) + picks)
            if candidate[0] > best[0] or (candidate[0] == best[0] and candidate[1] < best[1]) or (candidate[:2] == best[:2] and candidate[2] < best[2]):
                best = candidate
        return best

    _, _, picks = solve(0, 0)
    selected = {task: {"executor_id": ex, "verifier_id": ve} for task, ex, ve in picks}
    return summarize("central_oracle", workload,
                     [(t["id"], selected.get(t["id"])) for t in tasks])


def run(seed_start, seed_count, task_count, agent_count, out):
    with Path(out).open("w", encoding="utf-8", newline="\n") as f:
        for seed in range(seed_start, seed_start + seed_count):
            w = make_workload(seed, task_count, agent_count)
            row = {"schema": "issue5407-market-t2-raw-v1", "workload": w, "policies": {
                "scalar_unconstrained": scalar_policy(w),
                "value_first": constrained_greedy(w, False),
                "scarcity_first": constrained_greedy(w, True),
                "central_oracle": oracle_policy(w),
            }}
            f.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed-start", type=int, default=0)
    ap.add_argument("--seed-count", type=int, default=50)
    ap.add_argument("--tasks", type=int, default=8)
    ap.add_argument("--agents", type=int, default=10)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    run(a.seed_start, a.seed_count, a.tasks, a.agents, a.out)

