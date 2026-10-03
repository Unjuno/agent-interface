"""Saved-only logical-input/authority composition oracle; no producer imports."""
import argparse
import hashlib
import json
from pathlib import Path

def need(condition,message):
    if not condition: raise ValueError(message)

def keys(sample,codes):
    bits=bytes.fromhex(sample["keymap"])
    need(len(bits)==32 and sample["buttons"]==0,"logical query shape/button neutrality")
    allowed=bytearray(32)
    for code in codes.values(): allowed[code//8]|=1<<(code%8)
    need(not any(b & ~a for b,a in zip(bits,allowed)),"foreign logical input")
    return {name for name,code in codes.items() if bits[code//8] & (1<<(code%8))}

def neutral(receipt):
    return receipt.get("verified") is True and receipt.get("keys_down")==[] and receipt.get("buttons_down")==[]

def audit(rows, plan):
    expected={c["id"]:c for c in plan["cells"]}
    need(len(rows)==len(expected)==12 and len({r["id"] for r in rows})==12,"cell membership")
    summary=[]
    for row in rows:
        need({k:row[k] for k in ("id","repeat","policy","blocked")}==expected.get(row["id"]),"assignment")
        need(row["error"] is None and row["auto_repeat_disabled"] and row["xvfb_exit"] in (0,-15),"exposure/cleanup error")
        codes=row["keycodes"]; times=row["times"]; samples=row["samples"]
        need(set(codes)=={"F8","F9"} and all(type(x)is int and 8<=x<=255 for x in codes.values()) and codes["F8"]!=codes["F9"],"key identities")
        need(len(samples)>=3 and all(s["query_started_ns"]<=s["at_ns"] for s in samples)
             and all(a["at_ns"]<=b["at_ns"] for a,b in zip(samples,samples[1:])),"query brackets/order")
        states=[keys(s,codes) for s in samples]
        need(samples[0]["tag"]=="writer_entry" and states[0]=={"F8"},"initial held F8")
        checks=[(s,state) for s,state in zip(samples,states) if s["tag"]=="checkpoint"]
        ends=[s for s in samples if s["tag"]=="terminal"]
        need(len(checks)==1 and checks[0][0]["at_ns"]==times["checkpoint"]==row["checkpoint"]["sample_at_ns"]
             and not checks[0][1] and row["checkpoint"]["down"] is False,"neutral checkpoint join")
        need(len(ends)==1 and {k:ends[0][k] for k in ("keymap","buttons")}==row["terminal"]
             and not any(bytes.fromhex(row["terminal"]["keymap"])) and row["terminal"]["buttons"]==0,"terminal join/neutral")
        need(times["checkpoint"]>=times["checkpoint_anchor"]+plan["checkpoint_after_request_ns"],"checkpoint deadline")
        need(times["write_enter"]<=times["write_resume"]<=times["write_return"]<=times["program_return"],"write/program chronology")
        denied=row["blocked"] and row["policy"]=="before_positive_gate"
        program=row["program_input"]
        ops=[{"op":"focus","target":"owned"},{"op":"key_state","key":"F8","down":True},
             {"op":"observe","frame":"window_client","x":0,"y":0,"w":280,"h":180},
             {"op":"key_state","key":"F9","down":True},{"op":"wait_update","timeout_ms":plan["f9_hold_ms"]},{"op":"release_all"}]
        need(program["schema"]=="agent-interface/program-v1" and program["program_id"]==row["id"] and program["ops"]==ops
             and program["source"]=={"observation_seq":1,"binding_revision":0}
             and program["terminal"]=={"release_all_required":True} and program["authority"]["lease_id"]=="owned-7010"
             and program["authority"]["expires_at_ns"]>times["program_return"],"public program identity")
        result=row["program"]; ex=result["execution"]
        need(result["admission"]=="accepted" and result["recovery_required"] is False
             and result["status"]==("execution_failed" if denied else "completed")
             and ex["completed_ops"]==([0,1,2] if denied else [0,1,2,3,4,5])
             and ex["program_emissions"]==(2 if denied else 4),"public prefix/status/emissions")
        if denied: need(ex["failed_op"]==3 and "RESEARCH_ONLY_REVOKED_POSITIVE_INPUT" in ex["error"],"reference refusal boundary")
        need(ex["releases"] and all(neutral(r) for r in ex["releases"]),"public verified release")
        png=row["png"]; source=row["source_capture"]; pt=png["timing_ns"]
        need(len(ex["observations"])==1,"one actual observation")
        obs=ex["observations"][0]
        need(source=={k:obs[k] for k in ("sha256","capture_started_ns","capture_ended_ns","operation_index")}
             and {k:v for k,v in png.items() if k not in ("file","header")}==obs["artifact"],"observation/artifact joins")
        need(source["operation_index"]==2 and source["sha256"]==png["source_raw_sha256"]
             and source["capture_started_ns"]<=source["capture_ended_ns"]<=pt["started"],"capture source identity")
        need(row["png_write_payload"]=={k:png[k] for k in ("bytes","sha256","header")}
             and png["header"]=="89504e470d0a1a0a" and (png["width"],png["height"])==(280,180),"actual PNG payload")
        need(pt["started"]<=pt["converted"]<=pt["encoded"]<=times["write_enter"]<=times["write_return"]<=pt["written"]<=pt["hashed"],"writer source times")
        need("capture" in row["write_stack"] and row["write_stack"].count("write")>=2,"actual writer stack")
        calls=row["positive_input_calls"]
        need(len(calls)==2 and [c["key"] for c in calls]==["F8","F9"] and all(c["down"] is True
             and c["started_ns"]<=c["checked_ns"]<=c["returned_ns"] for c in calls),"positive input call sequence")
        need(calls[0]["native_called"] and not calls[0]["refused"] and not calls[0]["revoked_at_check"],"original F8 call")
        need(calls[1]["native_called"] is (not denied) and calls[1]["refused"] is bool(denied)
             and calls[1]["revoked_at_check"] is row["blocked"] and row["revoked"] is row["blocked"],"F9 guard call")
        releases=row["release_calls"]
        need(releases and all(neutral(c["result"]) and c["started_ns"]<=c["returned_ns"]
             and c["emissions_after"]>=c["emissions_before"] for c in releases),"release call trace")
        program_releases=[c["result"] for c in releases if c["thread"]=="program"]
        need(ex["releases"]==program_releases,"public release/call join")
        trace=sorted(calls+releases,key=lambda c:c["started_ns"])
        need(trace[0]["emissions_before"]==0 and all(a["returned_ns"]<=b["started_ns"]
             and a["emissions_after"]==b["emissions_before"] for a,b in zip(trace,trace[1:]))
             and trace[-1]["emissions_after"]==ex["program_emissions"],"serialized owner emission chain")
        need(all(c["emissions_after"]-c["emissions_before"]==(1 if c["native_called"] else 0) for c in calls),"native input emission delta")
        controllers=[c for c in releases if c["thread"]=="cleanup-only"]
        first_up=next((s for s,state in zip(samples,states) if not state),None)
        f9=[s for s,state in zip(samples,states) if "F9" in state]
        app=row["app_events"]
        need(all(a["at_ns"]<=b["at_ns"] for a,b in zip(app,app[1:])),"app event order")
        want=[("press",codes["F8"])]
        if row["blocked"]:
            need(len(controllers)==1 and neutral(row["cleanup_response"]) and first_up is not None,"cleanup independent readback")
            control=controllers[0]
            need(row["cleanup_response"]==control["result"],"cleanup response/call join")
            need(times["write_enter"]<=times["cancel_request"]<=times["revoked_set"]<=control["started_ns"]<=control["returned_ns"]
                 <times["checkpoint"]<times["write_resume"] and times["cancel_request"]==times["checkpoint_anchor"],"revocation/cleanup chronology")
            need(control["emissions_after"]-control["emissions_before"]==1 and first_up["at_ns"]<times["checkpoint"],"F8 cleanup evidence")
            need(times["write_resume"]>=times["cancel_request"]+plan["stall_after_request_ns"]
                 and row["checkpoint"]["writer_pending"] and row["checkpoint"]["program_pending"],"fault exposure")
            need(calls[1]["started_ns"]>=times["write_return"] and calls[1]["checked_ns"]>times["revoked_set"],"F9 after resume/revocation")
            want.append(("release",codes["F8"]))
            if not denied: want += [("press",codes["F9"]),("release",codes["F9"])]
        else:
            need(not controllers and not row["checkpoint"]["writer_pending"] and not row["checkpoint"]["program_pending"],"healthy parity")
            want += [("press",codes["F9"]),("release",codes["F8"]),("release",codes["F9"])]
        need([(e["kind"],e["keycode"]) for e in app]==want,"native app event sequence")
        need(not f9 if denied else bool(f9),"independent F9 logical coverage")
        late=[e for e in app if e["kind"]=="press" and e["keycode"]==codes["F9"] and row["blocked"] and e["at_ns"]>times["cancel_request"]]
        need(len(late)==(1 if row["blocked"] and not denied else 0),"late app input join")
        if late: need(late[0]["at_ns"]>=times["write_resume"] and all(s["at_ns"]>=times["write_resume"] for s in f9),"late F9 source chronology")
        summary.append({"id":row["id"],"blocked":row["blocked"],"policy":row["policy"],"late_f9_presses":len(late),
                        "f9_logical_samples":len(f9),"public_status":result["status"],
                        "first_confirmed_neutral_after_anchor_ms":None if first_up is None else (first_up["at_ns"]-times["checkpoint_anchor"])/1e6})
    return {"status":"FAIL_CLEANUP_ONLY_COMPOSITION_LATE_INPUT_SCOPED","reference":"SUPPORTED_BEFORE_POSITIVE_GATE_SCOPED",
            "n":12,"rows":summary,"public_api_regression_established":False,"production_cancel_integrated":False}

def main():
    p=argparse.ArgumentParser(); p.add_argument("raw");p.add_argument("plan");p.add_argument("out");args=p.parse_args()
    raw=Path(args.raw)
    try:
        rows=[json.loads(s) for s in raw.read_text().splitlines()]; result=audit(rows,json.loads(Path(args.plan).read_text()))
        for row in rows:
            path=raw.parent/row["png"]["file"]; data=path.read_bytes()
            need(hashlib.sha256(data).hexdigest()==row["png"]["sha256"] and len(data)==row["png"]["bytes"]
                 and data[:8].hex()==row["png"]["header"],"saved PNG bytes")
        result["raw_sha256"]=hashlib.sha256(raw.read_bytes()).hexdigest(); code=0
    except Exception as error: result={"status":"STOP_INVALID_EXPOSURE","error":repr(error)}; code=1
    with Path(args.out).open("x") as stream: json.dump(result,stream,indent=2);stream.write("\n")
    print(json.dumps(result)); raise SystemExit(code)

if __name__=="__main__":main()
