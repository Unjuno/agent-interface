#!/usr/bin/env python3
"""Finite integer-tick reservation/inheritance candidate for Issue #7944."""
import copy
import argparse
import hashlib
import json
from pathlib import Path


POLICIES = {"NONE", "PI_HOME_CHARGED", "BWI"}


def _edge_eligible(job, now):
    edge = job.get("edge", {})
    return (edge.get("authenticated") is True
            and edge.get("current") is True
            and edge.get("complete") is True
            and edge.get("resource_preemptible") is True
            and now < edge.get("expires", -1))


def _owner_of(resource, jobs):
    owners = [j for j in jobs.values() if resource in j["holds"] and not j["done"]]
    if len(owners) == 1:
        return owners[0]
    if len(owners) > 1:
        return {"id": "<ambiguous-owner>", "ambiguous": True}
    return None


def _dependency_leaf(waiter, jobs):
    """Return (runnable leaf owner, refusal reason) for a dependency chain."""
    resource = waiter.get("waits_for")
    seen = {waiter["id"]}
    leaf = None
    while resource:
        owner = _owner_of(resource, jobs)
        if owner is None:
            return None, "OWNER_MISSING_OR_AMBIGUOUS"
        if owner.get("ambiguous"):
            return None, "OWNER_MISSING_OR_AMBIGUOUS"
        if owner["id"] in seen:
            return None, "DEPENDENCY_CYCLE"
        seen.add(owner["id"])
        leaf = owner
        resource = owner.get("waits_for")
    return leaf, None


def simulate(case, policy):
    """Execute one deterministic, preemptive, one-CPU finite trace."""
    if policy not in POLICIES:
        raise ValueError("unknown policy")
    servers = {s["id"]: {**s, "remaining": s["budget"],
                         "next_replenishment": s["deadline"], "ticks": 0}
               for s in case["servers"]}
    jobs = {}
    for raw in case["jobs"]:
        j = copy.deepcopy(raw)
        j["id"] = raw["id"]
        j["initial_waits_for"] = raw.get("waits_for")
        j["remaining"] = raw["work"]
        j["done"] = raw["work"] == 0
        j["completion"] = raw.get("release", 0) if j["done"] else None
        j["holds"] = list(raw.get("holds", []))
        jobs[j["id"]] = j

    events = []
    decisions = []
    inherited_ticks = 0
    for now in range(case["horizon"]):
        for job in jobs.values():
            if (not job["done"] and job.get("cancel_at") is not None
                    and now >= job["cancel_at"]):
                job["cancelled"] = True
                job["done"] = True
                job["completion"] = None
                job["holds"] = []
        for server in servers.values():
            if server["remaining"] == 0 and now >= server["next_replenishment"]:
                server["remaining"] = server["q"]
                server["deadline"] += server["p"]
                server["next_replenishment"] = server["deadline"]

        blocked = {}
        for job in jobs.values():
            if job["done"] or job.get("cancelled") or now < job.get("release", 0):
                continue
            resource = job.get("waits_for")
            if resource:
                owner = _owner_of(resource, jobs)
                if owner is None:
                    job["waits_for"] = None
                else:
                    blocked[job["id"]] = resource

        runnable = [j for j in jobs.values()
                    if not j["done"] and not j.get("cancelled")
                    and now >= j.get("release", 0)
                    and j["id"] not in blocked]
        options = []
        for job in runnable:
            home = servers[job["server"]]
            if home["remaining"] > 0:
                options.append((home["deadline"], home.get("tie_rank", 1), job["id"],
                                job["server"], "home", job, home, False, None))

        donors = []
        for job_id in sorted(blocked):
            job = jobs[job_id]
            edge = job.get("edge", {})
            if not edge.get("authenticated"):
                reason = "UNAUTHENTICATED_EDGE"
            elif not edge.get("current"):
                reason = "STALE_EDGE"
            elif not edge.get("complete"):
                reason = "INCOMPLETE_EDGE"
            elif not edge.get("resource_preemptible"):
                reason = "UNSUPPORTED_RESOURCE"
            elif now >= edge.get("expires", -1):
                reason = "EXPIRED_EDGE"
            else:
                reason = None
            leaf, chain_refusal = _dependency_leaf(job, jobs) if reason is None else (None, None)
            if reason is None and chain_refusal:
                reason = chain_refusal
            decisions.append({"time": now, "waiter": job_id,
                              "eligible": reason is None,
                              "reason": reason or "ELIGIBLE", "leaf": leaf["id"] if leaf else None})
            if reason is None:
                donors.append(job)
        donors.sort(key=lambda j: (j["deadline"], j["server"], j["id"]))
        if policy != "NONE":
            for donor in donors:
                leaf, _ = _dependency_leaf(donor, jobs)
                if leaf is None:
                    continue
                home = servers[leaf["server"]]
                if policy == "PI_HOME_CHARGED":
                    if home["remaining"] > 0:
                        options.append((donor["deadline"], servers[donor["server"]].get("tie_rank", 0), leaf["id"],
                                        leaf["server"], "priority-inheritance", leaf, home,
                                        False, donor["id"]))
                else:
                    inherited = servers[donor["server"]]
                    if home["remaining"] == 0 and inherited["remaining"] > 0:
                        options.append((donor["deadline"], inherited.get("tie_rank", 0), leaf["id"],
                                        donor["server"], "bandwidth-inheritance", leaf, inherited,
                                        True, donor["id"]))

        if not options:
            continue
        _, _, _, charge_id, reason, job, charge_server, inherited, donor_id = min(options)
        before = charge_server["remaining"]
        charge_server["remaining"] -= 1
        charge_server["ticks"] += 1
        job["remaining"] -= 1
        if inherited:
            inherited_ticks += 1
        events.append({
            "time": now, "job": job["id"], "server_charged": charge_id,
            "budget_before": before, "budget_after": charge_server["remaining"],
            "inherited": inherited, "reason": reason, "donor": donor_id,
        })
        if job["remaining"] == 0:
            job["done"] = True
            job["completion"] = now + 1
            job["holds"] = []

    completions = {j["id"]: j["completion"] for j in jobs.values()}
    misses = sorted(j["id"] for j in jobs.values()
                    if not j.get("cancelled")
                    and (j["completion"] > j["deadline"]
                         if j["completion"] is not None
                         else j["deadline"] <= case["horizon"]))
    return {
        "case_id": case["case_id"], "policy": policy,
        "job_completion": completions, "deadline_misses": misses,
        "server_ticks": {key: value["ticks"] for key, value in sorted(servers.items())},
        "inherited_ticks": inherited_ticks, "events": events, "decisions": decisions,
        "cancelled_jobs": sorted(j["id"] for j in jobs.values() if j.get("cancelled")),
        "pending_jobs": sorted(j["id"] for j in jobs.values()
                                if not j["done"] and not j.get("cancelled")),
        "freshness": {j["id"]: ("CANCELLED" if j.get("cancelled") else
                                   "ADMITTED_FRESH" if j["completion"] is not None
                                   and j["completion"] <= j["deadline"] else
                                   "UNKNOWN_STALE" if j["deadline"] <= case["horizon"] else "PENDING")
                      for j in jobs.values() if j.get("initial_waits_for")},
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    fixture_bytes = (root / "fixture.json").read_bytes()
    freeze = json.loads((root / "FREEZE.json").read_text())
    frozen_hashes = freeze["sha256"]
    observed = {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                for name in frozen_hashes}
    if observed != frozen_hashes:
        raise SystemExit("frozen source hash mismatch")
    fixture = json.loads(fixture_bytes)
    runs = []
    for case in fixture["cases"]:
        for policy in ("NONE", "PI_HOME_CHARGED", "BWI"):
            runs.append(simulate(case, policy))
    raw = {
        "schema": "issue7944-bwi-t0-a01-raw-v1",
        "allocation_id": freeze["allocation_id"],
        "base_main": freeze["base_main"],
        "formal_candidate_invocations": 1,
        "formal_auditor_invocations": 0,
        "retry_count": 0,
        "freeze_sha256": hashlib.sha256((root / "FREEZE.json").read_bytes()).hexdigest(),
        "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
        "frozen_source_sha256": frozen_hashes,
        "policy_order": ["NONE", "PI_HOME_CHARGED", "BWI"],
        "runs": runs,
    }
    Path(args.output).write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
