"""Raw-only audit. Does not import candidate or oracle code."""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def audit(path):
    doc=json.loads(Path(path).read_text()); errors=[]
    expected_ids={"positive_bound_effect","state_only","effect_without_actuation","viewport_as_effect",
        "hud_as_effect","terminal_as_effect","run_total_as_effect","effect_before_down","mismatched_plan",
        "mismatched_actuation","scorer_not_independent","controller_scorer","unrelated_clock"}
    rows=doc.get("cases",[])
    ids=[r.get("case_id") for r in rows]
    if doc.get("schema")!="map01-task-effect-contract-result-v1": errors.append("schema")
    if doc.get("input_authority") is not False or doc.get("live_calls")!=0: errors.append("scope")
    if set(ids)!=expected_ids or len(ids)!=len(expected_ids): errors.append("case_inventory")
    if len(rows)!=13: errors.append("case_count")
    for r in rows:
        raw=r.get("raw",{}); c=r.get("candidate",{}); o=r.get("oracle",{})
        if c!=o: errors.append("candidate_oracle:"+str(r.get("case_id")))
        if c.get("grants_input_authority") is not False or c.get("grants_task_authority") is not False: errors.append("authority")
        # Independently reconstruct the evidence-role decision from raw bytes.
        p=raw.get("physical",{}); d=p.get("down",{}); u=p.get("up",{})
        phys_ok=(raw.get("clock_axis_attested") is True and p.get("owner_id") is not None
            and p.get("empty_release_verified") is True and all(x.get(k)==raw.get(k2) for x in (d,u)
                for k,k2 in (("session_id","session_id"),("plan_id","plan_id"),("actuation_id","actuation_id")))
            and all(x.get("owner_id")==p.get("owner_id") for x in (d,u))
            and isinstance(d.get("key"),str) and d.get("key")==u.get("key")
            and all(type(x.get(k)) is int for x in (d,u) for k in ("lower_ns","upper_ns"))
            and 0<=d.get("lower_ns",-1)<=d.get("upper_ns",-1)<=u.get("lower_ns",-1)<=u.get("upper_ns",-1))
        if c.get("physical_actuation")!=("PHYSICAL_ACTUATION_SCOPED" if phys_ok else "UNRESOLVED"):
            errors.append("physical_reconstruction:"+str(r.get("case_id")))
        expected_effect="UNRESOLVED_NO_TASK_EFFECT"
        es=raw.get("task_effects",[])
        if es:
            qualifying=[]
            for e in es:
                valid=(phys_ok and e.get("session_id")==raw.get("session_id") and e.get("plan_id")==raw.get("plan_id")
                    and e.get("actuation_id")==raw.get("actuation_id") and e.get("scored") is True
                    and e.get("scorer_independent") is True and e.get("controller_visible") is False
                    and e.get("scorer_source")=="independent_progress_clock_v2"
                    and e.get("kind") in ("KILL_COUNT_INCREASE","DEATH_COUNT_INCREASE","MAP_EXIT","PROGRESS")
                    and e.get("polarity") in ("useful","harmful") and type(e.get("observed_ns")) is int
                    and e.get("observed_ns",-1)>=d.get("upper_ns",0) and isinstance(e.get("effect_id"),str) and e.get("effect_id"))
                if valid: qualifying.append(e)
            expected_effect="TASK_EFFECT_SCOPED" if len(qualifying)==1 and len(es)==1 else "UNRESOLVED_UNBOUND_OR_INVALID_EFFECT"
            if len(qualifying)>1: expected_effect="UNRESOLVED_DUPLICATE_EFFECT"
        if c.get("task_effect")!=expected_effect: errors.append("effect_reconstruction:"+str(r.get("case_id")))
        if c.get("task_effect")!=r.get("expected_task_effect"): errors.append("frozen_gate:"+str(r.get("case_id")))
        if c.get("state_feedback") and c.get("task_effect")=="TASK_EFFECT_SCOPED":
            if any(x.get("authority") is not False for x in c["state_feedback"]): errors.append("state_authority")
    return {"status":"PASS_MAP01_TASK_EFFECT_CONTRACT_SCOPED" if not errors else "FAIL_CONTRACT_AUDIT",
            "errors":errors,"result_sha256":sha(path),"cases":len(rows),"formal_allocations":1,"live_allocations":0}


if __name__=="__main__":
    result=audit(sys.argv[1] if len(sys.argv)>1 else Path(__file__).with_name("result.json"))
    Path(__file__).with_name("audit_result.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps(result,sort_keys=True)); raise SystemExit(0 if result["status"].startswith("PASS") else 1)
