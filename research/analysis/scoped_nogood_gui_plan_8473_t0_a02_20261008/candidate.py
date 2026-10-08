#!/usr/bin/env python3
"""Deterministic planner-feedback candidate for Issue #8473 T0."""

import json
import sys
from pathlib import Path


def _check(scenario, generation, operation, cursors):
    key = f"{generation}|{operation}"
    item = scenario["checks"].get(key, {"status": "UNKNOWN"})
    if "sequence" in item:
        pos = cursors.get(key, 0)
        result = item["sequence"][min(pos, len(item["sequence"]) - 1)]
        cursors[key] = pos + 1
        return result
    return item


def run(source):
    runs = []
    for case in source["scenarios"]:
        for policy in source["policy_order"]:
            generation = case["initial_generation"]
            scoped = []
            blacklist = set()
            cursors = {}
            attempts = []
            queries = 0
            duplicate_infeasible_queries = 0
            seen_infeasible = set()
            pruned = 0
            terminal = "NO_PLAN"
            selected_proposal = None
            completed_effects = []
            proposal_ids = []
            for proposal in case["proposals"]:
                proposal_ids.append(proposal["id"])
                generation = proposal.get("generation", generation)
                tick = proposal.get("tick", 0)
                rejected = False
                if policy == "GLOBAL_BLACKLIST" and any(op in blacklist for op in proposal["steps"]):
                    attempts.append({"proposal": proposal["id"], "status": "PRUNED", "by": "GLOBAL_BLACKLIST"})
                    pruned += 1
                    continue
                for op in proposal["steps"]:
                    check_key = f"{generation}|{op}"
                    if policy == "SCOPED_NOGOOD":
                        live = [entry for entry in scoped
                                if entry["generation"] == generation and tick < entry["expires_at"]]
                        scoped = live
                        hint = case["checks"].get(check_key, {})
                        if "sequence" in hint:
                            hint = hint["sequence"][0]
                        evidence = hint.get("reason")
                        if any(entry["operation"] == op and entry["target"] == (evidence or {}).get("target")
                               and entry["surface"] == (evidence or {}).get("surface")
                               and entry["evidence"] == (evidence or {}).get("evidence")
                               and entry["expires_at"] == (evidence or {}).get("expires_at")
                               for entry in scoped):
                            attempts.append({"proposal": proposal["id"], "operation": op,
                                             "generation": generation, "tick": tick,
                                             "status": "PRUNED", "by": "SCOPED_NOGOOD",
                                             "target": (evidence or {}).get("target"),
                                             "surface": (evidence or {}).get("surface"),
                                             "evidence": (evidence or {}).get("evidence"),
                                             "expires_at": (evidence or {}).get("expires_at")})
                            pruned += 1
                            rejected = True
                            break
                    result = _check(case, generation, op, cursors)
                    queries += 1
                    status = result["status"]
                    record = {"proposal": proposal["id"], "operation": op,
                              "generation": generation, "tick": tick, "status": status}
                    if "reason" in result:
                        record["reason"] = result["reason"]
                    if "effect" in result:
                        record["effect"] = result["effect"]
                    attempts.append(record)
                    if status == "INFEASIBLE":
                        identity = (generation, op)
                        if identity in seen_infeasible:
                            duplicate_infeasible_queries += 1
                        seen_infeasible.add(identity)
                        reason = result.get("reason")
                        if policy == "GLOBAL_BLACKLIST":
                            blacklist.add(op)
                        elif (policy == "SCOPED_NOGOOD" and reason
                              and reason.get("generation") == generation
                              and isinstance(reason.get("expires_at"), int)
                              and tick < reason["expires_at"]):
                            scoped.append({"operation": op, "target": reason["target"],
                                           "surface": reason["surface"], "generation": generation,
                                           "evidence": reason["evidence"],
                                           "expires_at": reason["expires_at"]})
                        rejected = True
                        break
                    if status in ("TIMEOUT", "UNKNOWN"):
                        terminal = "UNKNOWN"
                        rejected = True
                        break
                    if status != "FEASIBLE":
                        terminal = "UNKNOWN"
                        rejected = True
                        break
                    completed_effects.append(result.get("effect"))
                    if "next_generation" in result:
                        generation = result["next_generation"]
                if not rejected:
                    terminal = "EFFECT"
                    selected_proposal = proposal["id"]
                    break
            runs.append({"scenario": case["id"], "policy": policy,
                         "proposal_ids": proposal_ids, "attempts": attempts,
                         "feasibility_queries": queries,
                         "duplicate_infeasible_queries": duplicate_infeasible_queries,
                         "pruned_plans": pruned, "terminal": terminal,
                         "selected_proposal": selected_proposal,
                         "effects": completed_effects, "authority": False})
    return {"schema": "scoped-nogood-raw-v1", "runs": runs}


def main(argv):
    src = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    Path(argv[2]).write_text(json.dumps(run(src), sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
