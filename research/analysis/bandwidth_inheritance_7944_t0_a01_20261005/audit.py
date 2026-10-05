#!/usr/bin/env python3
"""Raw-only independent reconstruction for Issue #7944 T0 A01."""
import argparse
import copy
import hashlib
import json
from pathlib import Path


POLICIES = ("NONE", "PI_HOME_CHARGED", "BWI")


def owner_list(resource, state):
    return [job for job in state.values()
            if resource in job["locks"] and not job["finished"]]


def chain_for(waiter, state):
    chain = []
    visited = {waiter["name"]}
    resource = waiter.get("blocked_on")
    while resource:
        owners = owner_list(resource, state)
        if len(owners) != 1:
            return None, "OWNER_MISSING_OR_AMBIGUOUS"
        current = owners[0]
        if current["name"] in visited:
            return None, "DEPENDENCY_CYCLE"
        visited.add(current["name"])
        chain.append(current)
        resource = current.get("blocked_on")
    return chain, None


def edge_problem(edge, tick):
    if edge.get("authenticated") is not True:
        return "UNAUTHENTICATED_EDGE"
    if edge.get("current") is not True:
        return "STALE_EDGE"
    if edge.get("complete") is not True:
        return "INCOMPLETE_EDGE"
    if edge.get("resource_preemptible") is not True:
        return "UNSUPPORTED_RESOURCE"
    if tick >= edge.get("expires", -1):
        return "EXPIRED_EDGE"
    return None


def reconstruct(case, policy):
    """Rebuild an arm from the frozen inputs; candidate code is never imported."""
    servers = {}
    for source in case["servers"]:
        servers[source["id"]] = {
            "q": source["q"], "p": source["p"], "budget": source["budget"],
            "deadline": source["deadline"], "next": source["deadline"],
            "tie": source.get("tie_rank", 1), "used": 0,
        }
    state = {}
    for source in case["jobs"]:
        state[source["id"]] = {
            "name": source["id"], "server": source["server"],
            "release": source.get("release", 0), "remaining": source["work"],
            "deadline": source["deadline"], "locks": list(source.get("holds", [])),
            "blocked_on": source.get("waits_for"), "original_blocked_on": source.get("waits_for"),
            "edge": copy.deepcopy(source.get("edge", {})),
            "cancel_at": source.get("cancel_at"), "cancelled": False,
            "finished": source["work"] == 0,
            "done_at": source.get("release", 0) if source["work"] == 0 else None,
        }

    trace = []
    decisions = []
    donated = 0
    for tick in range(case["horizon"]):
        for task in state.values():
            if (not task["finished"] and task["cancel_at"] is not None
                    and tick >= task["cancel_at"]):
                task["cancelled"] = True
                task["finished"] = True
                task["locks"] = []
        for server in servers.values():
            if server["budget"] == 0 and tick >= server["next"]:
                server["budget"] = server["q"]
                server["deadline"] += server["p"]
                server["next"] = server["deadline"]

        blocked_now = {}
        for task in state.values():
            if task["finished"] or tick < task["release"] or not task["blocked_on"]:
                continue
            owners = owner_list(task["blocked_on"], state)
            if not owners:
                task["blocked_on"] = None
            else:
                blocked_now[task["name"]] = task["blocked_on"]

        choices = []
        for task in state.values():
            if (task["finished"] or tick < task["release"]
                    or task["name"] in blocked_now):
                continue
            server = servers[task["server"]]
            if server["budget"]:
                choices.append((server["deadline"], server["tie"], task["name"],
                                task["server"], "home", task, server, False, None))

        valid_waiters = []
        for name in sorted(blocked_now):
            waiter = state[name]
            reason = edge_problem(waiter["edge"], tick)
            chain, chain_error = (None, None) if reason else chain_for(waiter, state)
            if reason is None and chain_error:
                reason = chain_error
            decisions.append({"time": tick, "waiter": name, "eligible": reason is None,
                              "reason": reason or "ELIGIBLE",
                              "leaf": chain[-1]["name"] if chain else None})
            if reason is None:
                valid_waiters.append((waiter, chain))

        if policy != "NONE":
            valid_waiters.sort(key=lambda pair: (pair[0]["deadline"],
                                                  pair[0]["server"], pair[0]["name"]))
            for waiter, chain in valid_waiters:
                leaf = chain[-1]
                home_server = servers[leaf["server"]]
                if policy == "PI_HOME_CHARGED":
                    if home_server["budget"]:
                        donor_tie = servers[waiter["server"]]["tie"]
                        choices.append((waiter["deadline"], donor_tie, leaf["name"],
                                        leaf["server"], "priority-inheritance", leaf,
                                        home_server, False, waiter["name"]))
                else:
                    donor_server = servers[waiter["server"]]
                    if home_server["budget"] == 0 and donor_server["budget"]:
                        choices.append((waiter["deadline"], donor_server["tie"],
                                        leaf["name"], waiter["server"], "bandwidth-inheritance",
                                        leaf, donor_server, True, waiter["name"]))

        if not choices:
            continue
        _, _, _, charged_id, mode, task, charged, via_donation, donor = min(choices)
        old_budget = charged["budget"]
        charged["budget"] -= 1
        charged["used"] += 1
        task["remaining"] -= 1
        if via_donation:
            donated += 1
        trace.append({"time": tick, "job": task["name"], "server_charged": charged_id,
                      "budget_before": old_budget, "budget_after": charged["budget"],
                      "inherited": via_donation, "reason": mode, "donor": donor})
        if task["remaining"] == 0:
            task["finished"] = True
            task["done_at"] = tick + 1
            task["locks"] = []

    completion = {name: task["done_at"] for name, task in state.items()}
    missed = sorted(name for name, task in state.items()
                    if not task["cancelled"] and
                    ((task["done_at"] is not None and task["done_at"] > task["deadline"])
                     or (task["done_at"] is None and task["deadline"] <= case["horizon"])))
    return {
        "case_id": case["case_id"], "policy": policy,
        "job_completion": completion, "deadline_misses": missed,
        "server_ticks": {name: data["used"] for name, data in sorted(servers.items())},
        "inherited_ticks": donated, "events": trace, "decisions": decisions,
        "cancelled_jobs": sorted(name for name, task in state.items() if task["cancelled"]),
        "pending_jobs": sorted(name for name, task in state.items()
                                if not task["finished"] and not task["cancelled"]),
        "freshness": {name: ("CANCELLED" if task["cancelled"] else
                             "ADMITTED_FRESH" if task["done_at"] is not None
                             and task["done_at"] <= task["deadline"] else
                             "UNKNOWN_STALE" if task["deadline"] <= case["horizon"] else "PENDING")
                      for name, task in state.items() if task["original_blocked_on"]},
    }


def _run_key(run):
    return (run.get("case_id"), run.get("policy"))


def validate_runs(raw, fixture):
    errors = []
    for case in fixture["cases"]:
        admitted = sum(server["q"] / server["p"] for server in case["servers"])
        if admitted > 1.0:
            errors.append("TOTAL_BANDWIDTH_OVER_ONE:" + case["case_id"])
    expected_keys = {(case["case_id"], policy)
                     for case in fixture["cases"] for policy in POLICIES}
    runs = raw.get("runs", [])
    keys = [_run_key(run) for run in runs]
    if len(keys) != len(set(keys)) or set(keys) != expected_keys:
        errors.append("RUN_MATRIX_INCOMPLETE_OR_DUPLICATED")
    lookup = {_run_key(run): run for run in runs}
    for case in fixture["cases"]:
        for policy in POLICIES:
            key = (case["case_id"], policy)
            actual = lookup.get(key)
            if actual is None:
                continue
            expected = reconstruct(case, policy)
            if actual != expected:
                errors.append("TRACE_RECONSTRUCTION:" + case["case_id"] + ":" + policy)
            times = [event["time"] for event in actual.get("events", [])]
            if len(times) != len(set(times)):
                errors.append("MULTIPLE_CPU_JOBS_PER_TICK:" + case["case_id"] + ":" + policy)
    return errors


def validate(raw, fixture, freeze, root):
    errors = validate_runs(raw, fixture)
    if raw.get("schema") != "issue7944-bwi-t0-a01-raw-v1":
        errors.append("RAW_SCHEMA")
    if raw.get("allocation_id") != freeze.get("allocation_id"):
        errors.append("ALLOCATION_ID")
    if raw.get("base_main") != freeze.get("base_main"):
        errors.append("BASE_MAIN")
    if raw.get("formal_candidate_invocations") != 1 or raw.get("retry_count") != 0:
        errors.append("CANDIDATE_INVOCATION_ACCOUNTING")
    if raw.get("policy_order") != list(POLICIES):
        errors.append("POLICY_SET")
    if raw.get("fixture_sha256") != hashlib.sha256((root / "fixture.json").read_bytes()).hexdigest():
        errors.append("FIXTURE_HASH")
    if raw.get("freeze_sha256") != hashlib.sha256((root / "FREEZE.json").read_bytes()).hexdigest():
        errors.append("FREEZE_HASH")
    hashes = {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
              for name in freeze.get("sha256", {})}
    if hashes != freeze.get("sha256") or raw.get("frozen_source_sha256") != hashes:
        errors.append("FROZEN_SOURCE_HASHES")
    return errors


def run_audit(raw, fixture, freeze, root):
    errors = validate(raw, fixture, freeze, root)
    mutation_results = []
    valid_run_index = next((i for i, run in enumerate(raw["runs"])
                            if run["case_id"] == "budget_inversion" and run["policy"] == "BWI"), None)
    missed_run_index = next((i for i, run in enumerate(raw["runs"])
                             if run["case_id"] == "budget_inversion" and run["policy"] == "NONE"), None)
    mutations = []
    if valid_run_index is not None:
        changed = copy.deepcopy(raw)
        changed["runs"][valid_run_index]["events"][0]["budget_after"] += 1
        mutations.append(("budget_refund", changed))
        changed = copy.deepcopy(raw)
        changed["runs"][valid_run_index]["events"].append(
            copy.deepcopy(changed["runs"][valid_run_index]["events"][0]))
        mutations.append(("duplicate_cpu_service", changed))
        changed = copy.deepcopy(raw)
        changed["runs"][valid_run_index]["events"][0]["server_charged"] = "H"
        mutations.append(("wrong_server_charge", changed))
    if missed_run_index is not None:
        changed = copy.deepcopy(raw)
        changed["runs"][missed_run_index]["freshness"]["verifier"] = "ADMITTED_FRESH"
        mutations.append(("stale_freshness_admission", changed))
    changed = copy.deepcopy(raw)
    if changed.get("runs"):
        changed["runs"].pop()
    mutations.append(("omitted_policy_case", changed))
    for name, damaged in mutations:
        caught = bool(validate(damaged, fixture, freeze, root))
        mutation_results.append({"mutation": name, "rejected": caught})
        if not caught:
            errors.append("MUTATION_SURVIVED:" + name)

    base_case = next(case for case in fixture["cases"]
                     if case["case_id"] == "budget_inversion")
    edge_controls = []
    for name, field, value in (
        ("forged_edge", "authenticated", False),
        ("stale_edge", "current", False),
        ("incomplete_edge", "complete", False),
        ("remote_nonpreemptible", "resource_preemptible", False),
        ("expired_edge", "expires", 0),
    ):
        damaged_case = copy.deepcopy(base_case)
        damaged_case["jobs"][1]["edge"][field] = value
        control = reconstruct(damaged_case, "BWI")
        rejected = (control["inherited_ticks"] == 0
                    and control["freshness"].get("verifier") == "UNKNOWN_STALE")
        edge_controls.append({"control": name, "rejected": rejected,
                              "inherited_ticks": control["inherited_ticks"],
                              "freshness": control["freshness"].get("verifier")})
        if not rejected:
            errors.append("EDGE_CONTROL_ACCEPTED:" + name)

    runs = {_run_key(run): run for run in raw.get("runs", [])}
    inversion_bwi = runs.get(("budget_inversion", "BWI"), {})
    inversion_pi = runs.get(("budget_inversion", "PI_HOME_CHARGED"), {})
    empty_arms = [runs.get(("no_contention", policy), {}) for policy in POLICIES]
    hypothesis_pass = (
        inversion_bwi.get("freshness", {}).get("verifier") == "ADMITTED_FRESH"
        and inversion_pi.get("freshness", {}).get("verifier") == "UNKNOWN_STALE"
        and len({arm.get("job_completion", {}).get("verifier") for arm in empty_arms}) == 1
        and all(arm.get("inherited_ticks") == 0 for arm in empty_arms)
    )
    disposition = "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD"
    return {
        "schema": "issue7944-bwi-t0-a01-audit-v1",
        "formal_auditor_invocations": 1,
        "disposition": disposition,
        "hypothesis_disposition": "H_PASS_SCOPED" if hypothesis_pass else "H_FAIL_SCOPED",
        "run_rows_reconstructed": sum(len(run.get("events", [])) for run in raw.get("runs", [])),
        "run_arms_reconstructed": len(raw.get("runs", [])),
        "errors": errors,
        "mutation_controls": mutation_results,
        "edge_controls": edge_controls,
        "limitations": [
            "same-author separate implementation, not independent human review",
            "integer-tick authored finite schedules only",
            "simplified CBS-like replenishment, not full CBS or host scheduling",
            "no application resource, GUI, user, model, latency, or physical-release claim",
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    raw = json.loads(Path(args.raw).read_text())
    fixture = json.loads((root / "fixture.json").read_text())
    freeze = json.loads((root / "FREEZE.json").read_text())
    audit = run_audit(raw, fixture, freeze, root)
    Path(args.output).write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    if audit["disposition"] != "PASS_METHOD_SCOPED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
