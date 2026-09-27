"""Independent reconstruction. Does not import the runner or worker implementation."""
import argparse
import base64
import copy
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
import statistics
import tempfile

SCENARIOS = ("ready", "generation_changed", "predecessor_failed", "cancelled", "expired",
             "competing_requests", "independent_resources", "completed_request_restart", "claimed_process_crash")
POLICIES = ("PRECHECK_ONLY", "ATOMIC_CLAIM")
ROOT = Path(__file__).resolve().parent


def same(a, b):
    # JSON equality rather than Python's True == 1 convenience.
    return json.dumps(a, sort_keys=True, separators=(",", ":")) == json.dumps(b, sort_keys=True, separators=(",", ":"))


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def integer(value):
    return type(value) is int and value >= 0


def expected_schedule(s, policy):
    chain = [("spawn", "w1"), ("prepare", "w1")]
    changed = s in SCENARIOS[1:5]
    if changed:
        chain.append(("transition", s))
    if s in ("competing_requests", "independent_resources"):
        chain += [("spawn", "w2"), ("prepare", "w2")]
    chain.append(("start", "w1"))
    if s in ("competing_requests", "independent_resources"):
        chain += [("start", "w2"), ("overlap_barrier", "") , ("work", "w1")]
        if s == "independent_resources" or policy == "PRECHECK_ONLY":
            chain.append(("work", "w2"))
        chain += [("shutdown", "w1"), ("exit", "w1"), ("shutdown", "w2"), ("exit", "w2")]
    elif s in ("completed_request_restart", "claimed_process_crash"):
        if s == "completed_request_restart":
            chain += [("work", "w1"), ("shutdown", "w1")]
        chain += [("exit", "w1"), ("spawn", "w2"), ("prepare", "w2"), ("start", "w2")]
        if policy == "PRECHECK_ONLY":
            chain.append(("work", "w2"))
        chain += [("shutdown", "w2"), ("exit", "w2")]
    else:
        if not changed or policy == "PRECHECK_ONLY":
            chain.append(("work", "w1"))
        chain += [("shutdown", "w1"), ("exit", "w1")]
    return chain


def audit_case(row, worker_hash):
    s, policy, rep = row["scenario"], row["policy"], row["rep"]
    cid = row["case_id"]
    require(type(rep) is int, "rep_type")
    require(cid == f"{s}-{rep}-{policy.lower()}", "case_identity")
    chain = [(e.get("op", e["kind"]), e.get("name", e.get("transition", ""))) for e in row["events"]]
    require(chain == expected_schedule(s, policy), "event_schedule")
    truth = copy.deepcopy(row["initial"])
    require(set(truth) == {"state", "admissions", "claims", "effects"}, "initial_schema")
    require(len(truth["state"]) == 1, "state_count")
    state = truth["state"][0]
    require(same(state, {"session": cid, "generation": 1, "predecessor_ok": 1,
                         "cancelled": 0, "deadline_ns": state["deadline_ns"]}), "initial_state")
    require(integer(state["deadline_ns"]), "deadline_type")
    require(not any(truth[k] for k in ("admissions", "claims", "effects")), "initial_records")
    workers, prepared, exits = {}, {}, []
    unsafe, start_count, refusals = 0, 0, 0
    durations = []
    last_time = 0
    for idx, e in enumerate(row["events"]):
        require(type(e["seq"]) is int and e["seq"] == idx, "event_sequence")
        if e["kind"] == "overlap_barrier":
            require(integer(e["time_ns"]) and e["time_ns"] >= last_time, "barrier_clock")
            require(same(e["snapshot"], truth), "barrier_snapshot")
            active = [a for a in truth["admissions"] if a["phase"] == "ACTIVE"]
            count = 2 if s == "independent_resources" or policy == "PRECHECK_ONLY" else 1
            require(len(active) == count and not truth["effects"], "active_overlap_gate")
            require(len(workers) == 2, "overlap_workers")
            last_time = e["time_ns"]
            continue
        require(integer(e["send_ns"]) and integer(e["recv_ns"]), "timestamp_type")
        require(last_time <= e["send_ns"] <= e["recv_ns"], "event_clock_order")
        last_time = e["recv_ns"]
        if "before" in e:
            require(same(e["before"], truth), "independent_before")
        if e["kind"] == "spawn":
            reply = json.loads(e["response"])
            require(e["response"].endswith("\n"), "hello_framing")
            require(type(e["pid"]) is int and e["pid"] > 0, "pid_type")
            require(e["worker"] == cid + "." + e["name"], "worker_identity")
            require(same(reply, {"event": "hello", "pid": e["pid"], "worker": e["worker"],
                                 "source_sha256": worker_hash}), "worker_source")
            require(e["name"] not in workers, "duplicate_process_name")
            require(e["argv"][-2:] == [policy, e["worker"]] and e["argv"][1] == "-I", "worker_command")
            workers[e["name"]] = {"pid": e["pid"], "worker": e["worker"]}
        elif e["kind"] == "transition":
            st = truth["state"][0]
            field = {"generation_changed": ("generation", 2), "predecessor_failed": ("predecessor_ok", 0),
                     "cancelled": ("cancelled", 1)}
            if s == "expired":
                require(e["recv_ns"] > st["deadline_ns"], "expiry_wait")
            else:
                key, value = field[s]
                st[key] = value
        elif e["kind"] == "command":
            name, op = e["name"], e["op"]
            owner = workers[name]
            require(e["worker"] == owner["worker"], "command_owner")
            require(e["request"].endswith("\n") and e["response"].endswith("\n"), "command_framing")
            cmd, reply = json.loads(e["request"]), json.loads(e["response"])
            require(cmd["op"] == op and reply["worker"] == owner["worker"] and type(reply["pid"]) is int
                    and reply["pid"] == owner["pid"], "request_reply_identity")
            if op == "shutdown":
                require(same(reply, {"event": "shutdown", **owner}), "shutdown_response")
            else:
                for k in ("entered_ns", "returned_ns", "time_ns"):
                    require(integer(reply[k]), "worker_timestamp_type")
                require(e["send_ns"] <= reply["entered_ns"] <= reply["time_ns"] <= reply["returned_ns"] <= e["recv_ns"], "worker_clock_order")
                now = reply["time_ns"]
                st = truth["state"][0]
                if op == "prepare":
                    request = "request-1" if name == "w1" or "restart" in s or s == "claimed_process_crash" else "request-2"
                    resource = "resource-2" if name == "w2" and s == "independent_resources" else "resource-1"
                    require(same(cmd, {"op": "prepare", "request": request, "resource": resource}), "prepare_request")
                    require(same(reply["observed"], st), "prepare_observation")
                    expected = {"request": request, "resource": resource, "generation": st["generation"],
                                "session": st["session"], "deadline_ns": st["deadline_ns"],
                                "ready": st["predecessor_ok"] == 1 and st["cancelled"] == 0 and now < st["deadline_ns"]}
                    require(expected["ready"] is True and same(expected, reply["prepared"]), "prepare_readiness")
                    require(reply["event"] == "prepared", "prepare_event")
                    prepared[name] = expected
                elif op == "start":
                    require(same(cmd, {"op": "start"}) and reply["event"] == "start", "start_request")
                    require(same(reply["observed"], truth), "start_observation")
                    p = prepared[name]
                    reasons = []
                    if (st["session"], st["generation"]) != (p["session"], p["generation"]): reasons.append("STALE_GENERATION")
                    if st["predecessor_ok"] != 1: reasons.append("PREDECESSOR_FAILED")
                    if st["cancelled"] != 0: reasons.append("CANCELLED")
                    if now >= min(st["deadline_ns"], p["deadline_ns"]): reasons.append("EXPIRED")
                    if any(a["request"] == p["request"] for a in truth["admissions"]): reasons.append("DUPLICATE_OR_UNRESOLVED")
                    if any(a["resource"] == p["resource"] and a["phase"] == "ACTIVE" for a in truth["admissions"]): reasons.append("RESOURCE_BUSY")
                    expected = (reasons[0] if reasons else "STARTED") if policy == "ATOMIC_CLAIM" else "STARTED"
                    require(reply["decision"] == expected, "admission_decision")
                    durations.append(reply["returned_ns"] - reply["entered_ns"])
                    if expected == "STARTED":
                        unsafe += bool(reasons); start_count += 1
                        attempt = owner["worker"] + ":attempt"
                        require(reply["attempt"] == attempt, "attempt_identity")
                        truth["admissions"].append({"attempt": attempt, "request": p["request"], "resource": p["resource"],
                            "worker": owner["worker"], "pid": owner["pid"], "prepared_generation": p["generation"],
                            "start_ns": now, "end_ns": None, "phase": "ACTIVE", "observed_generation": st["generation"]})
                        if policy == "ATOMIC_CLAIM":
                            truth["claims"].append({"resource": p["resource"], "request": p["request"], "attempt": attempt})
                    else:
                        refusals += 1
                        require(reply["attempt"] is None, "refused_attempt")
                elif op == "work":
                    require(same(cmd, {"op": "work"}) and reply["event"] == "work", "work_request")
                    attempt = owner["worker"] + ":attempt"
                    matches = [a for a in truth["admissions"] if a["attempt"] == attempt and a["phase"] == "ACTIVE"]
                    require(len(matches) == 1, "work_admission")
                    a = matches[0]
                    require(type(reply["value"]) is int and reply["value"] == 1 and reply["attempt"] == attempt, "effect_value")
                    truth["effects"].append({"attempt": attempt, "request": a["request"], "resource": a["resource"],
                                             "pid": owner["pid"], "value": 1, "time_ns": now})
                    a["phase"], a["end_ns"] = "DONE", now
                    truth["claims"] = [c for c in truth["claims"] if c["attempt"] != attempt]
                else:
                    raise ValueError("unknown_operation")
        elif e["kind"] == "exit":
            owner = workers.pop(e["name"])
            killed = s == "claimed_process_crash" and e["name"] == "w1"
            require(e["worker"] == owner["worker"] and type(e["pid"]) is int and e["pid"] == owner["pid"], "exit_identity")
            require(type(e["killed"]) is bool and e["killed"] == killed, "kill_control")
            require(type(e["returncode"]) is int and e["returncode"] == (-9 if killed else 0), "exit_status")
            require(e["stderr"] == "" and e["extra_stdout"] == "", "extra_process_output")
            exits.append({k: e[k] for k in ("worker", "pid", "returncode", "killed", "extra_stdout", "stderr", "send_ns", "recv_ns")})
        else:
            raise ValueError("unknown_event")
        if "after" in e:
            require(same(truth, e["after"]), "independent_after")
    require(not workers and same(exits, row["processes"]), "process_accounting")
    require(same(truth, row["final"]), "final_snapshot")
    journal = b"".join((json.dumps(e, sort_keys=True, separators=(",", ":")) + "\n").encode() for e in row["events"])
    require(hashlib.sha256(journal).hexdigest() == row["journal_sha256"], "journal_hash")
    raw_db = gzip.decompress(base64.b64decode(row["database_gzip_b64"], validate=True))
    require(len(raw_db) <= 1_000_000 and hashlib.sha256(raw_db).hexdigest() == row["database_sha256"], "database_hash")
    with tempfile.TemporaryDirectory(prefix="claim-audit-") as tmp:
        file = Path(tmp) / "readback.sqlite3"
        file.write_bytes(raw_db)
        with sqlite3.connect("file:" + str(file) + "?mode=ro", uri=True) as db:
            db.row_factory = sqlite3.Row
            require(db.execute("PRAGMA integrity_check").fetchone()[0] == "ok", "database_integrity")
            actual = {n: [dict(r) for r in db.execute(f"SELECT * FROM {n} ORDER BY rowid")]
                      for n in ("state", "admissions", "claims", "effects")}
            require(same(actual, truth), "database_reconstruction")
    if s == "claimed_process_crash" and policy == "ATOMIC_CLAIM":
        require(len(truth["claims"]) == 1 and len(truth["admissions"]) == 1 and not truth["effects"], "unresolved_claim")
    else:
        require(not truth["claims"], "released_claims")
    return {"unsafe": unsafe, "starts": start_count, "refusals": refusals, "effects": len(truth["effects"]),
            "processes": len(exits), "start_durations_ns": durations}


def audit_rows(rows, repetitions, worker_hash):
    expected = []
    for scenario in SCENARIOS:
        for rep in range(repetitions):
            for policy in (POLICIES if rep % 2 == 0 else tuple(reversed(POLICIES))):
                expected.append(f"{scenario}-{rep}-{policy.lower()}")
    errors, totals = [], {p: {"starts": 0, "unsafe": 0, "refusals": 0, "effects": 0, "processes": 0,
                             "start_durations_ns": []} for p in POLICIES}
    if [r.get("case_id") for r in rows] != expected:
        errors.append("case_denominator_or_order")
    for r in rows:
        try:
            result = audit_case(r, worker_hash)
            for k, v in result.items():
                if isinstance(v, list): totals[r["policy"]][k].extend(v)
                else: totals[r["policy"]][k] += v
        except (ValueError, KeyError, TypeError, IndexError, sqlite3.Error, OSError, EOFError) as error:
            errors.append(r.get("case_id", "?") + ":" + str(error))
    targets = {"PRECHECK_ONLY": (13, 7, 0, 12, 13), "ATOMIC_CLAIM": (6, 0, 7, 5, 13)}
    for p, target in targets.items():
        actual = tuple(totals[p][k] for k in ("starts", "unsafe", "refusals", "effects", "processes"))
        if actual != tuple(v * repetitions for v in target):
            errors.append(p + ":aggregate_gate")
        ts = totals[p].pop("start_durations_ns")
        totals[p]["start_call_median_ns_diagnostic"] = statistics.median(ts) if ts else None
        totals[p]["start_call_max_ns_diagnostic"] = max(ts) if ts else None
    return {"decision": "PASS_PROCESS_START_CLAIM_BOUNDARY_SCOPED" if not errors else "FAIL_AUDIT_OR_GATE",
            "precheck_policy": "FAIL_PRECHECK_ADMISSION_POLICY" if totals["PRECHECK_ONLY"]["unsafe"] else "NO_WITNESS",
            "errors": errors, "cases": len(rows), "totals": totals}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root"); ap.add_argument("--construction", action="store_true")
    args = ap.parse_args()
    root = Path(args.root)
    if not args.construction:
        freeze = json.loads((ROOT / "FREEZE.json").read_text())
        for path, h in freeze["sha256"].items():
            require(hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == h, "source:" + path)
    raw = (root / "RAW.jsonl").read_bytes()
    execution = json.loads((root / "EXECUTION.json").read_text())
    require(hashlib.sha256(raw).hexdigest() == execution["raw_sha256"], "raw_digest")
    require(execution["execution"] == "COMPLETED" and type(execution["cases"]) is int, "execution_complete")
    rows = [json.loads(line) for line in raw.splitlines()]
    require(execution["cases"] == len(rows), "execution_denominator")
    answer = audit_rows(rows, 1 if args.construction else 3, hashlib.sha256((ROOT / "worker.py").read_bytes()).hexdigest())
    answer["raw_sha256"] = hashlib.sha256(raw).hexdigest()
    print(json.dumps(answer, sort_keys=True))
    raise SystemExit(bool(answer["errors"]))


if __name__ == "__main__":
    main()
