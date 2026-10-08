"""Saved-only scope/death/receipt oracle. No native producer imports."""
import argparse
import hashlib
import json
from pathlib import Path
def need(value,message):
    if not value: raise ValueError(message)
def states(sample,codes):
    need(type(sample["query_started_ns"])is int and type(sample["at_ns"])is int and sample["query_started_ns"]<=sample["at_ns"],"query bracket")
    bits=bytes.fromhex(sample["keymap"]); allowed=bytearray(32)
    need(len(bits)==32 and sample["buttons"]==0,"whole keymap/button shape")
    for code in codes.values(): allowed[code//8]|=1<<(code%8)
    need(not any(b & ~a for b,a in zip(bits,allowed)),"undeclared logical input")
    return {k for k,c in codes.items() if bits[c//8] & (1<<(c%8))}
def neutral(r):
    return r.get("verified")is True and r.get("keys_down")==[] and r.get("buttons_down")==[]
def audit(rows,plan):
    expected={x["id"]:x for x in plan["cells"]}
    need(len(rows)==len(expected)==18 and len({r["id"]for r in rows})==18,"cell membership")
    summaries=[]; baseline_down=0; reference_unconfirmed=0; authority_failure=False
    for row in rows:
        need({k:row[k]for k in ("id","repeat","policy","context")}==expected.get(row["id"]),"assignment")
        need(row["error"]is None and row["auto_repeat_disabled"]is True and row["xvfb_exit"]in(0,-15),"valid exposure/teardown")
        codes=row["keycodes"]; need(set(codes)=={"F8","F9"} and all(type(c)is int and 8<=c<=255 for c in codes.values()) and codes["F8"]!=codes["F9"],"key identities")
        crash=row["context"]!="healthy"; bystander=row["context"]=="crash_bystander"; ref=row["policy"]=="prearmed_scope"
        times=row["times"]; owner=row["owner"]; supervisor=row["supervisor"]; cap=row["capability"]
        registered=supervisor["registered"]; helper=supervisor["result"]
        need(cap["cell_id"]==row["id"] and cap["owner_pid"]==owner["pid"] and cap["owner_nonce"]==owner["nonce"] and cap["keys"]=={"F8":codes["F8"]} and cap==registered["capability"],"prearmed owner/scope identity")
        need(row["display_generation"]=={"pid":cap["display_pid"],"start_ticks":cap["display_start_ticks"],"window_id":cap["window_id"]},"display generation")
        need(cap["registered_ns"]<=registered["at_ns"]<=times["task_go"]<=times["owner_ready"] and registered["held"]=={} and registered["emissions"]==0 and supervisor["pid"]!=owner["pid"],"prepress registration/fresh scope")
        need(supervisor["returncode"]==0 and helper["death_state"]in("Z","missing") and helper["eof_ns"]<=helper["dead_ns"]<=helper["before"]["query_started_ns"],"EOF and observed owner death")
        need(owner["returncode"]==(-9 if crash else 0),"owner process terminal")
        need(type(cap["owner_start_ticks"])is int and cap["owner_start_ticks"]>0 and (helper["death_start_ticks"]==cap["owner_start_ticks"]if helper["death_state"]=="Z"else helper["death_start_ticks"]is None),"original owner process generation")
        need(row["final_emergency"]["emissions"]==0 and neutral(row["final_emergency"]["receipt"]) and not any(k in row for k in ("cleanup_actor_error","cleanup_input_error","sampler_error")),"no hidden terminal repair/error")
        ready=owner["ready"]
        need(ready["at_ns"]==times["owner_ready"] and ready["held"]==cap["keys"] and ready["emissions"]==1 and all(k in ready["stack"]for k in ("dispatch","execute","wait_gate")),"actual public wait/source path")
        program=owner["program_input"]
        need(ready["program_input"]==program,"ready/public source program join")
        need(program["schema"]=="agent-interface/program-v1" and program["program_id"]==row["id"] and program["source"]=={"observation_seq":1,"binding_revision":0} and program["terminal"]=={"release_all_required":True} and program["authority"]["lease_id"]=="owned-7024" and program["authority"]["expires_at_ns"]>times["owner_ready"],"public program identity/lease")
        need(program["ops"]==[{"op":"focus","target":"owned"},{"op":"key_state","key":"F8","down":True},{"op":"wait_update","timeout_ms":plan["wait_ms"]},{"op":"release_all"}],"public operations")
        calls=owner["native_calls"]; want=[("press",codes["F8"])]+([]if crash else[("release",codes["F8"])])
        need([(c["kind"],c["code"])for c in calls]==want and calls[0]["returned_ns"]<=times["owner_ready"] and all(c["started_ns"]<=c["returned_ns"]for c in calls),"owner native program prefix")
        if crash:
            need(owner["completed"]is None and times["kill_sent"]>=times["owner_ready"]+plan["kill_after_ready_ns"] and times["kill_sent"]==times["checkpoint_anchor"] and times["kill_sent"]<=helper["eof_ns"],"crash cut")
        else:
            result=owner["completed"]
            waits=result["execution"]["waits"]
            need(len(waits)==1 and waits[0]["operation_index"]==2 and waits[0]["requested_ms"]==plan["wait_ms"] and waits[0]["completed"]is True and waits[0]["started_ns"]<=times["owner_ready"] and waits[0]["ended_ns"]>=times["owner_ready"]+plan["wait_ms"]*1000000 and waits[0]["ended_ns"]<=calls[1]["started_ns"],"complete public wait gate")
            need(times["kill_sent"]is None and times["checkpoint_anchor"]==times["owner_ready"] and result["status"]=="completed" and result["admission"]=="accepted" and result["execution"]["completed_ops"]==[0,1,2,3] and result["execution"]["program_emissions"]==2 and len(result["execution"]["releases"])==1 and neutral(result["execution"]["releases"][0]) and result["execution"]["releases"][0]["monotonic_ns"]<=helper["eof_ns"],"healthy public completion")
        samples=row["samples"]; shape=[states(s,codes)for s in samples]
        need(all(a["at_ns"]<=b["query_started_ns"]for a,b in zip(samples,samples[1:])),"sequential query intervals")
        held=[(s,v)for s,v in zip(samples,shape)if s["tag"]=="held"]; checks=[(s,v)for s,v in zip(samples,shape)if s["tag"]=="checkpoint"]; ends=[(s,v)for s,v in zip(samples,shape)if s["tag"]=="terminal"]
        need(len(held)==len(checks)==len(ends)==1 and held[0][1]==({"F8","F9"}if bystander else{"F8"}) and held[0][0]["query_started_ns"]>=times["owner_ready"],"held independent observation")
        checkpoint,checkstate=checks[0]; deadline=plan["crash_checkpoint_after_kill_ns"]if crash else plan["healthy_checkpoint_after_ready_ns"]
        need(checkpoint["query_started_ns"]>=times["checkpoint_anchor"]+deadline and checkpoint["at_ns"]==times["checkpoint"] and checkpoint["at_ns"]<times["recovery_started"],"checkpoint full bracket before fixture recovery")
        need(not ends[0][1] and ends[0][0]["query_started_ns"]>=times["recovery_started"] and neutral(row["fixture_recovery"]["receipt"]),"whole terminal neutral")
        need(row["checkpoint_owner_alive"]is(not crash) and type(row["checkpoint_supervisor_pending"])is bool,"owner/supervisor lifecycle at checkpoint")
        before=states(helper["before"],codes); after=states(helper["after"],codes); imported=ref and "F8"in before
        need(helper["scope"]==(cap["keys"]if imported else{}) and helper["before"]["at_ns"]<=helper["release_started_ns"]<=helper["release_returned_ns"]<=helper["after"]["query_started_ns"],"scope and release/query chronology")
        hcalls=helper["native_calls"]
        need(type(helper["emissions"])is int and helper["emissions"]==len(hcalls) and all(helper["release_started_ns"]<=c["started_ns"]<=c["returned_ns"]<=helper["release_returned_ns"]for c in hcalls),"supervisor emission/time join")
        if any(c["kind"]!="release"or c["code"]!=codes["F8"]for c in hcalls): authority_failure=True
        need(len(hcalls)==(1 if imported else 0),"one scoped release/no empty emission")
        receipt=helper["receipt"]; owed=["F8"]if imported and "F8"in after else[]
        need(receipt["keys_down"]==owed and receipt["buttons_down"]==[] and receipt["verified"]is(not owed) and helper["release_started_ns"]<=receipt["monotonic_ns"]<=helper["release_returned_ns"],"public receipt is scoped, not whole keymap")
        if not crash:
            need("F8"in checkstate and row["checkpoint_supervisor_pending"]is True and helper["eof_ns"]>=checkpoint["at_ns"] and not hcalls and not before and row["fixture_recovery"]["emissions"]==0,"no live-owner intervention/healthy parity")
        else:
            if not ref:
                need(neutral(receipt)and not hcalls,"legitimate empty-scope receipt"); baseline_down+=int("F8"in checkstate)
            elif "F8"in checkstate or helper["release_returned_ns"]>checkpoint["query_started_ns"]: reference_unconfirmed+=1
            else: need(any(s["query_started_ns"]>=helper["dead_ns"]and s["at_ns"]<=checkpoint["query_started_ns"]and "F8"not in v for s,v in zip(samples,shape)),"independent early owned release")
            if bystander:
                if any("F9"not in v for s,v in zip(samples,shape)if held[0][0]["query_started_ns"]<=s["query_started_ns"]<=checkpoint["query_started_ns"]): authority_failure=True
                if "F9"not in before or "F9"not in after: authority_failure=True
            else: need(all("F9"not in v for v in shape),"no unassigned F9")
            post=[(s,v)for s,v in zip(samples,shape)if s["tag"]=="after_supervisor"]
            need(len(post)==1 and post[0][0]["query_started_ns"]>=helper["after"]["at_ns"] and row["fixture_recovery"]["emissions"]==int("F8"in post[0][1]),"postmeasure recovery separate")
        events=row["app_events"]; need(all(a["at_ns"]<=b["at_ns"]for a,b in zip(events,events[1:])),"app receipt order")
        need([(e["kind"],e["code"])for e in events]==([("press",codes["F9"])]if bystander else[])+[("press",codes["F8"]),("release",codes["F8"])]+([("release",codes["F9"])]if bystander else[]),"exact owned/bystander app events")
        up=next(e["at_ns"]for e in events if e["kind"]=="release"and e["code"]==codes["F8"])
        if crash and not ref and "F8"in checkstate: need(up>=times["recovery_started"],"baseline up is postmeasurement, not success")
        if bystander: need(events[-1]["at_ns"]>=times["recovery_started"]and row["bystander_calls"]==[{"kind":"press","code":codes["F9"]},{"kind":"release","code":codes["F9"]}],"bystander only fixture-owned release")
        else: need(row["bystander_calls"]==[],"no bystander actor")
        summaries.append({"id":row["id"],"checkpoint_f8_down":"F8"in checkstate,"checkpoint_f9_down":"F9"in checkstate,"helper_emissions":helper["emissions"],"scoped_verified":receipt["verified"]})
    status=("FAIL_REFERENCE_COLLATERAL_OR_AUTHORITY"if authority_failure else "FAIL_REFERENCE_RELEASE_UNCONFIRMED"if reference_unconfirmed else "FAIL_EMPTY_SCOPE_AS_OWNER_RELEASE_EVIDENCE"if baseline_down==6 else "HOLD_NO_CRASH_PERSISTENCE_DISCRIMINATOR"if baseline_down==0 else "HOLD_MIXED_CRASH_DISCRIMINATOR")
    return {"status":status,"reference":"SUPPORTED_PREARMED_OWNER_SCOPE_TRANSFER_SCOPED"if not authority_failure and not reference_unconfirmed else "NOT_SUPPORTED","n":18,"baseline_crash_still_down":baseline_down,"reference_unconfirmed":reference_unconfirmed,"rows":summaries,"public_api_regression_established":False,"production_recovery_integrated":False}
def main():
    p=argparse.ArgumentParser();p.add_argument("raw");p.add_argument("plan");p.add_argument("out");a=p.parse_args()
    try:
        raw=Path(a.raw).read_bytes();rows=[json.loads(s)for s in raw.splitlines()]
        result=audit(rows,json.loads(Path(a.plan).read_text()))
        artifacts={}
        for row in rows:
            for role in ("owner","supervisor"):
                actor=row[role];packets=actor["packets"]
                path=Path(a.raw).parent/"cases"/row["id"]/role/"stdout.jsonl"
                saved=path.read_bytes()
                need([json.loads(s)for s in saved.splitlines()]==packets,"saved actor stream join")
                need(not any(p["event"]=="error"for p in packets),"actor error stream")
                native=[p["call"]for p in packets if p["event"]=="native"]
                if role=="owner":
                    init=[p for p in packets if p["event"]=="init"]
                    ready=[{k:v for k,v in p.items()if k!="event"}for p in packets if p["event"]=="ready"]
                    completed=[p for p in packets if p["event"]=="completed"]
                    need(len(init)==1 and init[0]["pid"]==actor["pid"] and init[0]["nonce"]==actor["nonce"] and init[0]["keycode"]==row["keycodes"]["F8"] and init[0]["held"]=={} and init[0]["emissions"]==0 and ready==[actor["ready"]] and native==actor["native_calls"],"owner stream/source identity")
                    need([p["result"]for p in completed]==([]if actor["completed"]is None else[actor["completed"]]),"owner completion stream")
                else:
                    need([{k:v for k,v in p.items()if k!="event"}for p in packets if p["event"]=="registered"]==[actor["registered"]] and [{k:v for k,v in p.items()if k!="event"}for p in packets if p["event"]=="result"]==[actor["result"]] and native==actor["result"]["native_calls"],"helper stream/source join")
                artifacts[str(path.relative_to(Path(a.raw).parent))]=hashlib.sha256(saved).hexdigest()
        result["actor_stream_sha256"]=artifacts
        result["raw_sha256"]=hashlib.sha256(raw).hexdigest();code=0
    except Exception as e: result={"status":"STOP_INVALID_EXPOSURE","error":repr(e)};code=1
    with Path(a.out).open("x")as f:json.dump(result,f,indent=2);f.write("\n")
    print(json.dumps(result));raise SystemExit(code)
if __name__=="__main__":main()
