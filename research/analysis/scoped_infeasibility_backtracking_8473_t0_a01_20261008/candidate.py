#!/usr/bin/env python3
"""Candidate policy simulator. It never reads the audit oracle's derived labels."""
import json
import sys


def feasible_step(step, state):
    return all(state.get(condition) is True for condition in step["requires"])


def run_case(case, policy):
    state = dict(case["truth"])
    generation = case["generation"]
    constraints = []
    rows = []
    pending = [plan["id"] for plan in case["plans"]]
    plan_by_id = {plan["id"]: plan for plan in case["plans"]}
    while pending:
        plan_id = pending.pop(0)
        plan = plan_by_id[plan_id]
        if policy == "GLOBAL_BLACKLIST" and constraints and any(
            step["action"] == constraints[0]["action"] for step in plan["steps"]
        ):
            rows.append({"event": "pruned", "plan": plan_id, "reason": "global_blacklist"})
            continue
        blocked = False
        for index, step in enumerate(plan["steps"]):
            signature = (step["action"], step["target"], step["surface"], generation)
            if policy == "SCOPED_NOGOOD" and any(c["signature"] == signature for c in constraints):
                rows.append({"event": "pruned", "plan": plan_id, "step": index, "reason": "scoped_nogood"})
                blocked = True
                break
            if feasible_step(step, state):
                rows.append({"event": "query", "plan": plan_id, "step": index, "feasible": True})
                transition = next((t for t in case["transitions"] if t["after_action"] == step["action"]), None)
                if transition:
                    state.update(transition["set"])
                    generation += 1
                    constraints = []
                continue
            missing = next(c for c in step["requires"] if state.get(c) is not True)
            rows.append({"event": "query", "plan": plan_id, "step": index, "feasible": False, "reason": missing})
            blocked = True
            if policy == "SCOPED_NOGOOD":
                # Only a source-grounded, current, typed blocker gains temporary scope.
                f = case["failure"]
                if (f["kind"] == "verified_blocker" and f["condition"] == missing
                        and f["generation"] == generation and f["target"] == step["target"]
                        and f["surface"] == step["surface"]):
                    constraints.append({"signature": signature, "action": step["action"]})
            elif policy == "GLOBAL_BLACKLIST":
                constraints.append({"action": step["action"]})
            break
        if not blocked:
            rows.append({"event": "selected", "plan": plan_id})
            return {"case": case["id"], "policy": policy, "rows": rows, "outcome": "PLAN_FOUND", "selected": plan_id}
    return {"case": case["id"], "policy": policy, "rows": rows, "outcome": "NO_PLAN", "selected": None}


def main(fixture_path, output_path):
    fixture = json.load(open(fixture_path, encoding="utf-8"))
    rows = [run_case(case, policy) for case in fixture["cases"] for policy in ("NO_FEEDBACK", "GLOBAL_BLACKLIST", "SCOPED_NOGOOD")]
    with open(output_path, "w", encoding="utf-8") as out:
        json.dump({"schema": "scoped-infeasibility-candidate-v1", "rows": rows}, out, sort_keys=True, indent=2)
        out.write("\n")
    print(json.dumps({"rows": len(rows), "output": output_path}))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
