import itertools
import json
import sys

RUNNER_SHA256 = "a597112f467fd198eb2d3a75611dfa79ccb0bdf48b724e4b92c988dcf230e921"

def oracle(phase, owner, command, generation_match, safe_point, in_bounds):
    if not generation_match:
        return "STALE_GENERATION"
    terminal = phase in ("REVOKED", "YIELDED")
    if command == "REVOKE":
        return "TERMINAL_PROGRAM" if terminal else "REVOKED_IMMEDIATE"
    if terminal:
        return "TERMINAL_PROGRAM"
    if command == "UNKNOWN":
        return "UNKNOWN_COMMAND"
    if command == "BOUNDED_UPDATE":
        if phase != "RUNNING":
            return "NOT_RUNNING"
        if not in_bounds:
            return "PARAM_OUT_OF_BOUNDS"
        if safe_point:
            return "UPDATE_APPLIED"
        return "UPDATE_QUEUED_SAFE_POINT"
    if command == "PARALLEL_ONESHOT":
        if phase != "RUNNING":
            return "NOT_RUNNING"
        if owner == "FREE":
            return "PARALLEL_ACCEPTED"
        return "RESOURCE_BUSY"
    if command == "SAME_RESOURCE_ONESHOT":
        if phase != "RUNNING":
            return "NOT_RUNNING"
        if owner == "EXTERNAL":
            return "RESOURCE_BUSY"
        if owner == "RESIDENT":
            return "HANDOFF_READY" if safe_point else "HANDOFF_QUEUED_SAFE_POINT"
        return "SAME_RESOURCE_ACCEPTED"
    if command == "RESUME":
        if phase != "PAUSED":
            return "NOT_PAUSED"
        if not safe_point:
            return "RESUME_QUEUED_SAFE_POINT"
        return "RESUMED" if owner == "FREE" else "RESOURCE_BUSY"
    raise AssertionError(command)

def audit(obj):
    errors=[]
    if obj.get("schema") != "resident_async_steering_contract_v1":
        errors.append("schema")
    if obj.get("source_sha256") != RUNNER_SHA256:
        errors.append("runner_source_sha256")
    phases=("RUNNING","PAUSED","REVOKED","YIELDED")
    owners=("FREE","RESIDENT","EXTERNAL")
    commands=("BOUNDED_UPDATE","PARALLEL_ONESHOT","SAME_RESOURCE_ONESHOT","RESUME","REVOKE","UNKNOWN")
    expected=list(itertools.product(phases,owners,commands,(False,True),(False,True),(False,True)))
    rows=obj.get("rows",[])
    if len(rows)!=576:
        errors.append("row_count")
        return {"audit":"FAIL","errors":errors}
    seen=set()
    counts={}
    for row in rows:
        key=tuple(row[:6])
        if key in seen:
            errors.append("duplicate_case")
            break
        seen.add(key)
        want=oracle(*key)
        if row[6]!=want:
            errors.append("oracle_mismatch")
            break
        counts[want]=counts.get(want,0)+1
    if seen!=set(expected):
        errors.append("cartesian_coverage")
    if counts!=obj.get("outcome_counts"):
        errors.append("outcome_counts")
    if obj.get("state_space",{}).get("expected_rows")!=576:
        errors.append("state_space_manifest")

    traces=obj.get("stateful_traces",{})
    ev=traces.get("events",[])
    expected_names=["update","update","parallel_keyboard","same_pointer","same_pointer",
                    "update","update","revoke","revoke","after_revoke"]
    if [e[0] for e in ev]!=expected_names:
        errors.append("trace_event_order")
    if len(ev)==10:
        wanted=["UPDATE_QUEUED_SAFE_POINT","UPDATE_APPLIED","PARALLEL_ACCEPTED",
                "HANDOFF_QUEUED_SAFE_POINT","HANDOFF_READY","STALE_GENERATION",
                "PARAM_OUT_OF_BOUNDS","STALE_GENERATION","REVOKED_IMMEDIATE",
                "TERMINAL_PROGRAM"]
        actual=[e[4] if e[0]=="update" else e[2] if e[0]=="parallel_keyboard" else
                e[3] if e[0]=="same_pointer" else e[3] if e[0]=="revoke" else e[2] for e in ev]
        if actual!=wanted:
            errors.append("trace_outcomes")
    final=traces.get("final_state",{})
    if final!={"generation":2,"phase":"REVOKED","pointer":"FREE","keyboard":"FREE","gain":2}:
        errors.append("trace_final_state")
    if traces.get("handoff_owner_timeline")!=["RESIDENT","FREE","EXTERNAL","FREE","RESIDENT"]:
        errors.append("handoff_timeline")
    if not all(traces.get("checks",{}).values()) or len(traces.get("checks",{}))!=8:
        errors.append("trace_invariants")

    neg=obj.get("negative_controls",{})
    if neg!={"stale_generation_admitted":True,
             "same_resource_off_safe_point_overlaps":True,
             "revoke_waits_for_safe_point":True}:
        errors.append("negative_controls")
    return {"audit":"PASS" if not errors else "FAIL","errors":errors,
            "rows_recomputed":len(rows),"unique_cases":len(seen),
            "outcome_counts":counts,
            "stateful_trace_events":len(ev),"decision":"PASS_ASYNC_STEERING_CONTRACT_SCOPED" if not errors else "HOLD"}

def main():
    result=audit(json.load(sys.stdin))
    print(json.dumps(result,separators=(",",":"),sort_keys=True))
    if result["audit"]!="PASS":
        raise SystemExit(2)

if __name__=="__main__":
    main()
