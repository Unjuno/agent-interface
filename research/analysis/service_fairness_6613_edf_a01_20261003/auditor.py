#!/usr/bin/env python3
"""Independent raw-only replay and five mutation controls; imports no candidate."""
import hashlib
import json
import sys
from pathlib import Path

ALLOCATION = "SERVICE-FAIRNESS-6613-EDF-A01-20261003"
POLICIES = ("fifo", "shortest_service", "edf")


def canon(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def choose(queue, policy):
    critical = [j for j in queue if j["mandatory"]]
    if critical:
        return min(critical, key=lambda j: (j["arrival"], j["id"]))
    if policy == "fifo":
        key = lambda j: (j["arrival"], j["id"])
    elif policy == "shortest_service":
        key = lambda j: (j["service"], j["arrival"], j["id"])
    elif policy == "edf":
        key = lambda j: (j["deadline"], j["arrival"], j["id"])
    else:
        raise AssertionError("unknown frozen policy")
    return min(queue, key=key)


def replay(trace, policy):
    waiting = {j["id"]: dict(j) for j in trace["tasks"]}
    terminal = []
    clock = 0
    while waiting:
        arrived = [j for j in waiting.values() if j["arrival"] <= clock]
        for job in arrived:
            expiry = job["eligible_until"]
            if expiry is not None and clock + job["service"] > expiry:
                terminal.append({"id": job["id"], "principal": job["principal"],
                                 "status": "expired_not_dispatched", "arrival": job["arrival"],
                                 "terminal_tick": expiry, "wait_to_dispatch": None,
                                 "on_time": False, "mandatory": job["mandatory"]})
                waiting.pop(job["id"])
        queue = [j for j in waiting.values() if j["arrival"] <= clock]
        if not waiting:
            break
        if not queue:
            clock = min(j["arrival"] for j in waiting.values())
            continue
        job = choose(queue, policy)
        began = clock
        ended = began + job["service"]
        if job["eligible_until"] is not None and ended > job["eligible_until"]:
            raise AssertionError("independent replay found expired dispatch")
        terminal.append({"id": job["id"], "principal": job["principal"], "status": "completed",
                         "arrival": job["arrival"], "start": began, "finish": ended,
                         "wait_to_dispatch": began - job["arrival"],
                         "on_time": ended <= job["deadline"], "mandatory": job["mandatory"]})
        waiting.pop(job["id"])
        clock = ended
    terminal.sort(key=lambda d: (d.get("start", d.get("terminal_tick", 0)), d["id"]))
    by_principal = {}
    for who in ("A", "B"):
        done = [d for d in terminal if d["principal"] == who and d["status"] == "completed"]
        gone = [d for d in terminal if d["principal"] == who and d["status"] == "expired_not_dispatched"]
        waits = [d["wait_to_dispatch"] for d in done]
        by_principal[who] = {
            "completed": len(done), "on_time": sum(d["on_time"] for d in done),
            "expired_not_dispatched": len(gone),
            "mean_wait_served": sum(waits) / len(waits) if waits else None,
            "max_wait_served": max(waits) if waits else None,
        }
    optional = [d for d in terminal if d["principal"] in ("A", "B")]
    return {"decisions": terminal,
            "summary": {"optional_completed": sum(d["status"] == "completed" for d in optional),
                        "optional_on_time": sum(d["status"] == "completed" and d["on_time"] for d in optional),
                        "optional_expired": sum(d["status"] == "expired_not_dispatched" for d in optional),
                        "mandatory_completed": sum(d["mandatory"] and d["status"] == "completed" for d in terminal),
                        "by_principal": by_principal}}


def expected_rows(fixture):
    return [{"seed": trace["seed"], "stratum": trace["stratum"], "policy": policy,
             **replay(trace, policy)}
            for trace in fixture["traces"] for policy in POLICIES]


def valid(payload, fixture, fixture_bytes, expected):
    return (payload.get("allocation_id") == ALLOCATION and
            payload.get("fixture_sha256") == hashlib.sha256(fixture_bytes).hexdigest() and
            payload.get("rows") == expected and
            payload.get("scope") == "finite authored synthetic method-only result; not a live fairness claim")


def evaluate(rows):
    primary = [r for r in rows if r["stratum"] == "asymmetric_deadlines"]
    means = {p: sum(r["summary"]["optional_on_time"] for r in primary if r["policy"] == p) / 40
             for p in POLICIES}
    other = {}
    for stratum in ("burst_recovery", "revocation_mandatory"):
        subset = [r for r in rows if r["stratum"] == stratum]
        other[stratum] = {p: sum(r["summary"]["optional_on_time"] for r in subset if r["policy"] == p) / 40
                          for p in POLICIES}
    gates = {"edf_minus_fifo_ge_0_5": means["edf"] - means["fifo"] >= 0.5,
             "edf_minus_sjf_ge_0_5": means["edf"] - means["shortest_service"] >= 0.5,
             "other_strata_edf_minus_fifo_ge_minus_0_5": all(
                 vals["edf"] - vals["fifo"] >= -0.5 for vals in other.values())}
    mandatory_ok = all(r["summary"]["mandatory_completed"] == 1
                       for r in rows if r["stratum"] == "revocation_mandatory")
    return {"asymmetric_mean_optional_on_time": means, "other_strata_means": other,
            "performance_gates": gates, "mandatory_tasks_all_completed": mandatory_ok,
            "hypothesis_pass": all(gates.values())}


def mutations_rejected(payload, fixture, fixture_bytes, expected):
    mutators = []
    def change(fn):
        clone = json.loads(json.dumps(payload))
        fn(clone)
        mutators.append(clone)
    change(lambda p: p["rows"].append(p["rows"][0]))
    change(lambda p: p["rows"][0].__setitem__("seed", -1))
    def corrupt_start(p):
        next(d for d in p["rows"][0]["decisions"] if d["status"] == "completed")["start"] += 1
    change(corrupt_start)
    def omit_release(p):
        row = next(r for r in p["rows"] if r["stratum"] == "revocation_mandatory")
        row["decisions"] = [d for d in row["decisions"] if d["id"] != "SYS-release"]
    change(omit_release)
    change(lambda p: p.__setitem__("fixture_sha256", "0" * 64))
    return sum(not valid(candidate, fixture, fixture_bytes, expected) for candidate in mutators)


def main():
    root = Path(__file__).resolve().parent
    fixture_path, raw_path, audit_path = (root / "fixture.json", root / "candidate_raw.json", root / "audit.json")
    if audit_path.exists():
        raise FileExistsError(f"refusing to overwrite audit output: {audit_path}")
    fixture_bytes = fixture_path.read_bytes()
    fixture = json.loads(fixture_bytes)
    raw_bytes = raw_path.read_bytes()
    payload = json.loads(raw_bytes)
    if fixture.get("allocation_id") != ALLOCATION or len(fixture.get("traces", [])) != 120:
        raise SystemExit("FAIL_METHOD: fixture identity/count mismatch")
    expected = expected_rows(fixture)
    if not valid(payload, fixture, fixture_bytes, expected):
        raise SystemExit("FAIL_METHOD: raw-only independent replay mismatch")
    mutations = mutations_rejected(payload, fixture, fixture_bytes, expected)
    if mutations != 5:
        raise SystemExit("FAIL_METHOD: corruption controls were not all rejected")
    outcome = evaluate(expected)
    integrity = outcome["mandatory_tasks_all_completed"]
    disposition = ("FAIL_METHOD" if not integrity else
                   "PASS_METHOD_SCOPED" if outcome["hypothesis_pass"] else "FAIL_HYPOTHESIS")
    audit = {"allocation_id": ALLOCATION, "disposition": disposition,
             "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(), "rows_replayed": len(expected),
             "independent_replay": "PASS_RAW_REPLAY", "mutation_rejections": mutations,
             "evaluation": outcome,
             "scope": "finite authored synthetic method-only result; not a live fairness claim"}
    audit_bytes = (canon(audit) + "\n").encode()
    with audit_path.open("xb") as stream:
        stream.write(audit_bytes)
    print(canon(audit))


if __name__ == "__main__":
    main()
