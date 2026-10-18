#!/usr/bin/env python3
"""Independent exhaustive oracle and raw-result auditor; no candidate imports."""
import copy
import hashlib
import json
import sys


def oracle_feasible(step, state):
    return all(condition in state and state[condition] is True for condition in step["requires"])


def oracle_plan(case, plan):
    state = copy.deepcopy(case["truth"])
    for step in plan["steps"]:
        if not oracle_feasible(step, state):
            return False
        for transition in case["transitions"]:
            if transition["after_action"] == step["action"]:
                state.update(transition["set"])
    return True


def exhaustive_labels(fixture):
    return {c["id"]: [p["id"] for p in c["plans"] if oracle_plan(c, p)] for c in fixture["cases"]}


def fixture_errors(fixture):
    errors = []
    for case in fixture["cases"]:
        failure = case["failure"]
        plan = next((p for p in case["plans"] if any(s["target"] == failure["target"] for s in p["steps"])), None)
        if plan is None:
            errors.append(f"failure target has no grounded plan {case['id']}")
            continue
        step = next(s for s in plan["steps"] if s["target"] == failure["target"])
        missing = [c for c in step["requires"] if case["truth"].get(c) is not True]
        if failure["condition"] not in missing or failure["surface"] != step["surface"]:
            errors.append(f"failure reason not independently grounded {case['id']}")
        if failure["kind"] == "timeout" or fixture["controls"]["unknown"]["promote_to_impossible"]:
            errors.append(f"unknown promoted to infeasibility {case['id']}")
    return errors


def audit(fixture, raw):
    errors = fixture_errors(fixture)
    labels = exhaustive_labels(fixture)
    rows = {(r["case"], r["policy"]): r for r in raw["rows"]}
    for case in fixture["cases"]:
        cid = case["id"]
        scoped, stateless, global_row = (rows.get((cid, p)) for p in ("SCOPED_NOGOOD", "NO_FEEDBACK", "GLOBAL_BLACKLIST"))
        if not all((scoped, stateless, global_row)):
            errors.append(f"missing policy row {cid}")
            continue
        if scoped["selected"] is not None and scoped["selected"] not in labels[cid]:
            errors.append(f"selected infeasible plan {cid}")
        if scoped["selected"] is None and labels[cid]:
            errors.append(f"pruned feasible alternatives {cid}")
        if cid in ("occluded-with-rearrangement", "focus-unavailable-with-recovery") and scoped["selected"] is None:
            errors.append(f"lost recovery alternative {cid}")
        if cid == "transient-stale-then-feasible" and scoped["selected"] is None:
            errors.append("stale constraint survived generation change")
        if cid == "truly-infeasible" and scoped["selected"] is not None:
            errors.append("false alternative in no-alternative control")
        dup = lambda row: sum(r["event"] == "query" and r.get("feasible") is False for r in row["rows"])
        if dup(scoped) > dup(stateless):
            errors.append(f"scoped duplicate query regression {cid}")
        if cid == "occluded-with-rearrangement" and not dup(scoped) < dup(stateless):
            errors.append("scoped no-good did not reduce repeated infeasibility query")
        if cid == "occluded-with-rearrangement" and dup(global_row) != dup(scoped):
            # The global comparator loses the recovery plan; it is not allowed to
            # score fewer queries as useful progress when it prunes that alternative.
            if global_row["selected"] in labels[cid]:
                errors.append("global comparator query tally inconsistent with selected plan")
        if any(r.get("reason") == "timeout" and r["event"] == "pruned" for r in scoped["rows"]):
            errors.append(f"timeout treated as infeasible {cid}")
    return errors, labels


def mutations(fixture, raw):
    results = {}
    omitted = copy.deepcopy(fixture)
    omitted["cases"][0]["failure"]["condition"] = "focus:canvas"
    results["omit_blocker"] = any("not independently grounded" in e for e in fixture_errors(omitted))
    baseline_errors, _ = audit(fixture, raw)
    assert not baseline_errors, "unmutated baseline must audit before mutation checks"
    def corrupt_scoped(case_id, reason):
        changed = copy.deepcopy(raw)
        row = next(r for r in changed["rows"] if r["case"] == case_id and r["policy"] == "SCOPED_NOGOOD")
        row["selected"], row["outcome"] = None, "NO_PLAN"
        row["rows"].append({"event": "pruned", "reason": reason, "plan": "mutated-alternative"})
        return changed
    generalized_raw = corrupt_scoped("occluded-with-rearrangement", "global_blacklist")
    results["global_overgeneralization"] = any("pruned feasible alternatives" in e for e in audit(fixture, generalized_raw)[0])
    stale_raw = corrupt_scoped("transient-stale-then-feasible", "stale_scoped_nogood")
    results["reuse_after_generation_change"] = any("pruned feasible alternatives" in e for e in audit(fixture, stale_raw)[0])
    timeout = copy.deepcopy(fixture)
    timeout["controls"]["unknown"]["promote_to_impossible"] = True
    timeout_raw = corrupt_scoped("occluded-with-rearrangement", "timeout")
    results["timeout_as_infeasible"] = any("unknown promoted" in e for e in fixture_errors(timeout)) and any("timeout treated" in e for e in audit(fixture, timeout_raw)[0])
    fake = copy.deepcopy(raw)
    for row in fake["rows"]:
        if row["case"] == "occluded-with-rearrangement" and row["policy"] == "SCOPED_NOGOOD":
            row["selected"], row["outcome"] = None, "NO_PLAN"
    results["delete_available_alternative"] = any("pruned feasible" in e for e in audit(fixture, fake)[0])
    return results


def main(fixture_path, raw_path, output_path):
    fixture = json.load(open(fixture_path, encoding="utf-8"))
    raw = json.load(open(raw_path, encoding="utf-8"))
    errors, labels = audit(fixture, raw)
    mutation_results = mutations(fixture, raw)
    if not all(mutation_results.values()):
        errors.append("mutation control failed")
    report = {"schema": "scoped-infeasibility-audit-v1", "passed": not errors, "errors": errors,
              "fixture_sha256": hashlib.sha256(open(fixture_path, "rb").read()).hexdigest(),
              "raw_sha256": hashlib.sha256(open(raw_path, "rb").read()).hexdigest(),
              "case_count": len(fixture["cases"]), "policy_rows": len(raw["rows"]),
              "oracle_feasible_plans": labels, "mutation_controls": mutation_results}
    with open(output_path, "w", encoding="utf-8") as out:
        json.dump(report, out, sort_keys=True, indent=2)
        out.write("\n")
    print(json.dumps({"passed": report["passed"], "errors": errors, "case_count": report["case_count"], "mutation_controls": mutation_results}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2], sys.argv[3]))
