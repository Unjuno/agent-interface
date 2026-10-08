#!/usr/bin/env python3
"""Deterministic one-operation-per-tick scheduler comparison for Issue #2868."""
from __future__ import annotations
import argparse, hashlib, heapq, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
POLICIES = ("FIFO_HEAD", "STABLE_LIST", "ELIGIBLE_HEAP")
REPEATS = (0, 1)

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def load_contract():
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    fixture_bytes = (ROOT / "scenarios.json").read_bytes()
    if sha(fixture_bytes) != freeze["source_sha256"]["scenarios.json"]:
        raise RuntimeError("FIXTURE_SHA256_MISMATCH")
    for name in ("runner.py", "audit.py", "test_protocol.py"):
        if sha((ROOT / name).read_bytes()) != freeze["source_sha256"][name]:
            raise RuntimeError("SOURCE_SHA256_MISMATCH:" + name)
    fixture = json.loads(fixture_bytes)
    if fixture.get("schema") != "scheduler-selection-scenarios-v1" or len(fixture.get("scenarios", [])) != 8:
        raise RuntimeError("FIXTURE_CONTRACT_MISMATCH")
    return freeze, fixture

def priority_key(op):
    return (-op["priority"], op["deadline"], op["seq"], op["id"])

def blocked_reason(op, tick, completed, locks):
    if op["release"] > tick: return "not_released"
    if op["ready_at"] > tick: return "not_before"
    if any(dep not in completed for dep in op["deps"]): return "dependency"
    if op["resource"] is not None and locks.get(op["resource"], -1) > tick: return "resource"
    return None

def worker(scenario, policy, repeat, fixture):
    spec = next(x for x in fixture["scenarios"] if x["id"] == scenario)
    ops = {x["id"]: dict(x, state="pending", version=0, wait_ticks=0) for x in spec["operations"]}
    completed, trace, stale = set(), [], 0
    heap = []
    horizon = spec.get("horizon", fixture["horizon"])
    events = {e["tick"]: [] for e in spec.get("events", [])}
    for e in spec.get("events", []): events[e["tick"]].append(e)
    for tick in range(horizon):
        for op in ops.values():
            if op["state"] == "pending" and op["release"] <= tick:
                op["state"] = "waiting"
                if policy == "ELIGIBLE_HEAP": heapq.heappush(heap, (*priority_key(op), op["version"]))
            if op["state"] == "waiting" and op["deadline"] < tick:
                op["state"] = "expired"
        for event in events.get(tick, []):
            op = ops[event["id"]]
            if op["state"] != "waiting": continue
            op["version"] += 1
            if event["kind"] == "cancel": op["state"] = "cancelled"
            elif event["kind"] == "reprioritize":
                op["priority"] = event["priority"]
                if policy == "ELIGIBLE_HEAP": heapq.heappush(heap, (*priority_key(op), op["version"]))
            else: raise RuntimeError("UNKNOWN_EVENT")

        eligible = [op for op in ops.values() if op["state"] == "waiting" and
                    op["deadline"] >= tick and blocked_reason(op, tick, completed, fixture["locks_until"]) is None]
        selected, reason = None, "no_eligible_candidate"
        if policy == "FIFO_HEAD":
            waiting = sorted((x for x in ops.values() if x["state"] == "waiting"), key=lambda x: (x["seq"], x["id"]))
            if waiting:
                head = waiting[0]
                reason = blocked_reason(head, tick, completed, fixture["locks_until"]) or "fifo_head"
                if head in eligible: selected = head
        elif policy == "STABLE_LIST":
            if eligible: selected = min(eligible, key=priority_key); reason = "priority_deadline_stable_seq"
        elif policy == "ELIGIBLE_HEAP":
            deferred, selected = [], None
            while heap:
                entry = heapq.heappop(heap)
                op_id, version = entry[3], entry[4]
                op = ops[op_id]
                if op["state"] != "waiting" or op["version"] != version:
                    stale += 1; continue
                if op not in eligible:
                    deferred.append(entry); continue
                selected = op; reason = "priority_deadline_stable_seq"; break
            for entry in deferred: heapq.heappush(heap, entry)
        else: raise RuntimeError("UNKNOWN_POLICY")

        avoidable_idle = selected is None and bool(eligible)
        if selected is None:
            for op in ops.values():
                if op["state"] == "waiting": op["wait_ticks"] += 1
            trace.append({"tick": tick, "selected": None, "reason": reason, "eligible_while_idle": avoidable_idle})
            continue
        if any(dep not in completed for dep in selected["deps"]): raise RuntimeError("DEPENDENCY_VIOLATION")
        if selected["resource"] is not None and fixture["locks_until"].get(selected["resource"], -1) > tick:
            raise RuntimeError("RESOURCE_VIOLATION")
        selected["state"] = "completed"; selected["completed_tick"] = tick
        completed.add(selected["id"])
        trace.append({"tick": tick, "selected": selected["id"], "reason": reason, "eligible_while_idle": False})
        for op in ops.values():
            if op["state"] == "waiting": op["wait_ticks"] += 1
    states = {k: {"state": v["state"], "completed_tick": v.get("completed_tick"), "priority": v["priority"], "seq": v["seq"], "wait_ticks": v["wait_ticks"]} for k,v in ops.items()}
    return {"schema":"scheduler-worker-row-v1", "scenario":scenario, "policy":policy, "repeat":repeat,
            "trace":trace, "states":states, "idle_ticks":sum(x["selected"] is None for x in trace),
            "avoidable_idle_ticks":sum(x["eligible_while_idle"] for x in trace),
            "stale_heap_entries_discarded":stale}

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--worker", nargs=3); parser.add_argument("--out")
    args=parser.parse_args(); freeze,fixture=load_contract()
    if args.worker:
        row=worker(args.worker[0], args.worker[1], int(args.worker[2]), fixture)
        print(json.dumps(row,sort_keys=True,separators=(",",":"))); return
    if not args.out: raise SystemExit("--out required")
    rows=[]
    for scenario in fixture["scenarios"]:
        for policy in POLICIES:
            for repeat in REPEATS:
                run=subprocess.run([sys.executable,"-B",str(Path(__file__).resolve()),"--worker",scenario["id"],policy,str(repeat)],
                    check=True,capture_output=True,text=True,timeout=10)
                row=json.loads(run.stdout)
                row["worker_exit_code"]=run.returncode
                rows.append(row)
    raw={"schema":"scheduler-selection-raw-v1","issue":2868,"allocation":freeze["allocation"],
         "freeze_parent_commit":freeze["freeze_parent_commit"],"freeze_sha256":sha((ROOT/"FREEZE.json").read_bytes()),
         "source_sha256":freeze["source_sha256"],
         "fixture_sha256":sha((ROOT/"scenarios.json").read_bytes()),"runtime":{"python":sys.version,"platform":sys.platform},
         "worker_processes":len(rows),"scenarios":len(fixture["scenarios"]),"policies":list(POLICIES),"rows":rows}
    dest=Path(args.out); dest.mkdir(parents=True,exist_ok=True)
    data=(json.dumps(raw,sort_keys=True,separators=(",",":"))+"\n").encode()
    (dest/"raw.json").write_bytes(data); (dest/"raw.sha256").write_text(sha(data)+"  raw.json\n",encoding="ascii")
    print(json.dumps({"raw_sha256":sha(data),"rows":len(rows),"workers":len(rows),"output_bytes":len(data)},sort_keys=True))
if __name__=="__main__": main()
