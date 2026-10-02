#!/usr/bin/env python3
"""One-shot EDF/FIFO/SJF candidate; writes raw schedules once, create-only."""
import hashlib
import json
from pathlib import Path

ALLOCATION = "SERVICE-FAIRNESS-6613-EDF-A01-20261003"
POLICIES = ("fifo", "shortest_service", "edf")
HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixture.json"
RAW = HERE / "candidate_raw.json"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def order_key(job, policy):
    if job["mandatory"]:
        return (0, job["arrival"], job["id"])
    if policy == "fifo":
        return (1, job["arrival"], job["id"])
    if policy == "shortest_service":
        return (1, job["service"], job["arrival"], job["id"])
    if policy == "edf":
        return (1, job["deadline"], job["arrival"], job["id"])
    raise ValueError(policy)


def simulate(trace, policy):
    pending = [dict(job) for job in trace["tasks"]]
    decisions = []
    now = 0
    while pending:
        for job in list(pending):
            if job["arrival"] <= now and job["eligible_until"] is not None:
                if now + job["service"] > job["eligible_until"]:
                    decisions.append({"id": job["id"], "principal": job["principal"],
                                      "status": "expired_not_dispatched", "arrival": job["arrival"],
                                      "terminal_tick": job["eligible_until"], "wait_to_dispatch": None,
                                      "on_time": False, "mandatory": job["mandatory"]})
                    pending.remove(job)
        ready = [job for job in pending if job["arrival"] <= now]
        if not pending:
            break
        if not ready:
            now = min(job["arrival"] for job in pending)
            continue
        # A mandatory release/event wins every free-server decision boundary.
        chosen = min(ready, key=lambda j: order_key(j, policy))
        start = now
        finish = start + chosen["service"]
        if chosen["eligible_until"] is not None and finish > chosen["eligible_until"]:
            raise AssertionError("candidate selected a task outside its hard eligibility horizon")
        decisions.append({"id": chosen["id"], "principal": chosen["principal"],
                          "status": "completed", "arrival": chosen["arrival"],
                          "start": start, "finish": finish,
                          "wait_to_dispatch": start - chosen["arrival"],
                          "on_time": finish <= chosen["deadline"],
                          "mandatory": chosen["mandatory"]})
        pending.remove(chosen)
        now = finish
    by_principal = {}
    for principal in ("A", "B"):
        served = [d for d in decisions if d["principal"] == principal and d["status"] == "completed"]
        expired = [d for d in decisions if d["principal"] == principal and d["status"] == "expired_not_dispatched"]
        by_principal[principal] = {
            "completed": len(served),
            "on_time": sum(d["on_time"] for d in served),
            "expired_not_dispatched": len(expired),
            "mean_wait_served": (sum(d["wait_to_dispatch"] for d in served) / len(served)) if served else None,
            "max_wait_served": max((d["wait_to_dispatch"] for d in served), default=None),
        }
    optional = [d for d in decisions if d["principal"] in ("A", "B")]
    return {
        "decisions": sorted(decisions, key=lambda d: (d.get("start", d.get("terminal_tick", 0)), d["id"])),
        "summary": {
            "optional_completed": sum(d["status"] == "completed" for d in optional),
            "optional_on_time": sum(d["status"] == "completed" and d["on_time"] for d in optional),
            "optional_expired": sum(d["status"] == "expired_not_dispatched" for d in optional),
            "mandatory_completed": sum(d["mandatory"] and d["status"] == "completed" for d in decisions),
            "by_principal": by_principal,
        },
    }


def main():
    fixture_bytes = FIXTURE.read_bytes()
    fixture = json.loads(fixture_bytes)
    if fixture["allocation_id"] != ALLOCATION or len(fixture["traces"]) != 120:
        raise ValueError("frozen fixture identity/count mismatch")
    if RAW.exists():
        raise FileExistsError(f"refusing to overwrite first outcome: {RAW}")
    rows = []
    for trace in fixture["traces"]:
        for policy in POLICIES:
            rows.append({"seed": trace["seed"], "stratum": trace["stratum"], "policy": policy,
                         **simulate(trace, policy)})
    primary = [r for r in rows if r["stratum"] == "asymmetric_deadlines"]
    means = {p: sum(r["summary"]["optional_on_time"] for r in primary if r["policy"] == p) / 40
             for p in POLICIES}
    other_strata = {}
    for stratum in ("burst_recovery", "revocation_mandatory"):
        group = [r for r in rows if r["stratum"] == stratum]
        other_strata[stratum] = {
            p: sum(r["summary"]["optional_on_time"] for r in group if r["policy"] == p) / 40
            for p in POLICIES
        }
    thresholds = {
        "asymmetric_edf_minus_fifo_at_least": 0.5,
        "asymmetric_edf_minus_shortest_at_least": 0.5,
        "other_strata_edf_minus_fifo_at_least": -0.5,
    }
    hypothesis_pass = (means["edf"] - means["fifo"] >= 0.5 and
                       means["edf"] - means["shortest_service"] >= 0.5 and
                       all(v["edf"] - v["fifo"] >= -0.5 for v in other_strata.values()))
    raw = {
        "allocation_id": ALLOCATION,
        "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
        "rows": rows,
        "preregistered_summary": {"asymmetric_deadlines_mean_optional_on_time": means,
                                  "other_strata_means": other_strata,
                                  "thresholds": thresholds,
                                  "candidate_hypothesis_gate": "PASS" if hypothesis_pass else "FAIL_HYPOTHESIS"},
        "scope": "finite authored synthetic method-only result; not a live fairness claim",
    }
    data = (canonical(raw) + "\n").encode()
    with RAW.open("xb") as stream:
        stream.write(data)
    print(json.dumps({"allocation_id": ALLOCATION, "rows": len(rows), "bytes": len(data),
                      "raw_sha256": hashlib.sha256(data).hexdigest()}, sort_keys=True))


if __name__ == "__main__":
    main()
