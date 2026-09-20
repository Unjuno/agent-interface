"""Independent audit of Issue #3796 construction and formal evidence."""
import hashlib,json,re,sys
from pathlib import Path
BASE="1355ff9c0e89e04887e7dd3a08aaa93c7b650df0"
IMAGE="agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27"
RUNNER_SHA="TO_BE_FROZEN";MANIFEST_SHA="TO_BE_FROZEN"
MATRIX=[("de-01","de"),("de-02","de"),("de-03","de"),("us-control","us")];FORMULA="=B2*A2"
def sha(b):return hashlib.sha256(b).hexdigest()
def blob(b):return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def fp(m):return sha(json.dumps(m,sort_keys=True,separators=(",",":")).encode())
def inv(p):return {f.relative_to(p).as_posix():sha(f.read_bytes()) for f in sorted(p.rglob("*")) if f.is_file() and f.name!="raw.json"}
def trace(chords):
    a=[]
    for c in chords:a += [("KeyPress",int(k)) for k in c]+[("KeyRelease",int(k)) for k in reversed(c)]
    return a
def main():
    evidence,source,output=map(lambda x:Path(x).resolve(),sys.argv[1:4]);output.mkdir(parents=True,exist_ok=True)
    if any(output.iterdir()):raise SystemExit("STOP_AUDIT_OUTPUT_NOT_EMPTY")
    rawb=(evidence/"raw.json").read_bytes();raw=json.loads(rawb);mb=(source/"research/issue_3784_explicit_x11_receiver_v3/source_manifest.json").read_bytes();m=json.loads(mb)
    run=(source/"research/issue_3784_explicit_x11_receiver_v3/runner.py").read_bytes();errors=[];stops=[];fails=[];summ=[]
    if raw.get("allocation")!="issue3784-explicit-x11-receiver-formal-03":errors.append("ALLOCATION")
    if raw.get("base_commit")!=BASE or m.get("base_commit")!=BASE:errors.append("BASE")
    if raw.get("image")!=IMAGE:errors.append("IMAGE")
    if sha(run)!=RUNNER_SHA or raw.get("runner_sha256")!=RUNNER_SHA:errors.append("RUNNER_HASH")
    if sha(mb)!=MANIFEST_SHA or raw.get("source_manifest_sha256")!=MANIFEST_SHA:errors.append("MANIFEST_HASH")
    if m.get("candidate_blob")!="9cae101a219348077668c8fc086acf8e13154afe":errors.append("CANDIDATE_BLOB")
    for p,e in m.get("files",{}).items():
        b=(source/p).read_bytes()
        if sha(b)!=e["sha256"] or blob(b)!=e["git_blob_sha1"]:errors.append("SOURCE:"+p)
    if inv(evidence)!=raw.get("artifact_sha256"):errors.append("ARTIFACT_INVENTORY")
    cpath=evidence/"construction.json"
    if not cpath.is_file() or json.loads(cpath.read_text())!=raw.get("construction"):errors.append("CONSTRUCTION_BINDING")
    cons=raw.get("construction",[])
    if len(cons)!=2:stops.append("CONSTRUCTION_MATRIX")
    for c,(layout,mutate) in zip(cons,[("de",True),("us",False)]):
        if c.get("layout")!=layout or c.get("status")!="PASS_CONSTRUCTION":stops.append("CONSTRUCTION_STATUS:"+str(layout))
        if c.get("focus_ok") is not True or c.get("control_ok") is not True:stops.append("CONSTRUCTION_RECEIVER:"+str(layout))
        if c.get("baseline",{}).get("layout_ok") is not True or c.get("after",{}).get("layout_ok") is not True:stops.append("CONSTRUCTION_QUERY:"+str(layout))
        if c.get("map_gate_ok") is not True:stops.append("CONSTRUCTION_MAP:"+str(layout))
        if c.get("apply",{}).get("exit")!=0:stops.append("CONSTRUCTION_APPLY:"+str(layout))
        if c.get("cleanup",{}).get("reaped") is not True:errors.append("CONSTRUCTION_CLEANUP:"+str(layout))
    rows=raw.get("rows",[])
    if rows and len(rows)!=4:stops.append("FORMAL_MATRIX_LENGTH")
    if rows and [r.get("case_id") for r in rows]!=[a for a,b in MATRIX]:errors.append("FORMAL_CASE_MATRIX")
    for r,(cid,layout) in zip(rows,MATRIX):
        case=evidence/"cases"/cid
        if r.get("layout")!=layout:errors.append("ROW_LAYOUT:"+cid)
        if r.get("xvfb_argv",[])[-1:]!=["-noreset"]:errors.append("NO_RESET:"+cid)
        if r.get("xvfb_cleanup",{}).get("reaped") is not True:errors.append("XVFB_REAP:"+cid)
        rp=case/"row.json"
        if not rp.is_file() or json.loads(rp.read_text())!=r:errors.append("ROW_BINDING:"+cid)
        recv=r.get("receiver",{});control=r.get("receiver_control",[])
        if recv and (recv.get("class")!="InputOnly" or recv.get("event_mask")!=3 or recv.get("mapped") is not True):errors.append("RECEIVER:"+cid)
        if recv and (r.get("focus_verified") is not True or recv.get("window_id")!=recv.get("focus_window_id")):stops.append("FOCUS:"+cid)
        cg=len(control)==2 and [e.get("type") for e in control]==["KeyPress","KeyRelease"] and control[0].get("keycode")==control[1].get("keycode") and [e.get("lookup_text") for e in control]==["a","a"]
        if recv and r.get("receiver_control_ok") is not cg:errors.append("CONTROL_BINDING:"+cid)
        if not cg:stops.append("RECEIVER_CONTROL:"+cid)
        b,a=r.get("baseline",{}),r.get("after",{});changed=layout=="de"
        for phase,state,want in (("baseline",b,"us"),("after",a,layout)):
            q=state.get("query",{}); valid=bool(re.search(r"(?m)^layout:\s+"+re.escape(want)+r"\s*$",q.get("stdout","")))
            if q.get("exit")!=0 or not valid or not state.get("layout_ok"):stops.append("LAYOUT_QUERY:"+cid+":"+phase)
            dp=case/(phase+".xkb");mp=case/(phase+".map.json")
            if not dp.is_file() or not mp.is_file():
                (stops if r.get("status","").startswith("STOP_") else errors).append("MAP_NOT_REACHED:"+cid+":"+phase);continue
            dump=dp.read_bytes();mapping=json.loads(mp.read_text())
            if dump.decode()!=state.get("dump") or sha(dump)!=state.get("dump_sha256"):errors.append("DUMP_BINDING:"+cid+":"+phase)
            if mapping!=state.get("map") or fp(mapping)!=state.get("map_sha256"):errors.append("MAP_BINDING:"+cid+":"+phase)
        gate=r.get("map_gate",{})
        if gate and (gate.get("query_layout") is not True or gate.get("dump_changed")!=changed or gate.get("fresh_map_changed")!=changed):stops.append("ACTIVE_MAP_GATE:"+cid)
        if layout=="de" and r.get("apply",{}).get("argv") not in (None,["setxkbmap","-layout","de"]):errors.append("APPLY_ARGV:"+cid)
        if r.get("plan_keycodes") is not None:
            u=r.get("unsupported",{});ev=r.get("events",[]);want=trace(r["plan_keycodes"]);actual=[(e.get("type"),e.get("keycode")) for e in ev]
            typed="".join(e.get("lookup_text","") for e in ev if e.get("type")=="KeyPress")
            if not u.get("refused_zero_event") or u.get("before_events") or u.get("after_events") or u.get("emissions")!=0 or "U+20AC" not in str(u.get("error")):fails.append("UNSUPPORTED:"+cid)
            if actual!=want:fails.append("TRACE:"+cid)
            if typed!=FORMULA or r.get("typed")!=typed:fails.append("TEXT:"+cid)
            if r.get("emissions")!=len(want):fails.append("EMISSIONS:"+cid)
            rel=r.get("release",{})
            if rel.get("verified") is not True or rel.get("keys_down")!=[] or rel.get("buttons_down")!=[]:fails.append("RELEASE:"+cid)
        elif not r.get("status","").startswith("STOP_"):fails.append("CANDIDATE_NOT_REACHED:"+cid)
        status=r.get("status","")
        if status.startswith("STOP_"):stops.append("ROW_STOP:"+cid+":"+status)
        elif status.startswith("FAIL_"):fails.append("ROW_FAIL:"+cid+":"+status)
        summ.append({"case_id":cid,"status":status,"control_ok":cg,"typed":r.get("typed"),"events":len(r.get("events",[]))})
    if raw.get("disposition")=="STOP_CONSTRUCTION_GATE":disposition="PASS_AUDIT_CONFIRMED_STOP" if not errors else "FAIL_AUDIT_INTEGRITY"
    elif errors:disposition="FAIL_AUDIT_INTEGRITY"
    elif stops:disposition="PASS_AUDIT_CONFIRMED_STOP"
    elif fails:disposition="PASS_AUDIT_CONFIRMED_FAIL"
    else:disposition="PASS_AUDIT_CONFIRMED_DELIVERY"
    report={"schema":"agent-interface/issue3796-audit-v1","raw_sha256":sha(rawb),"runner_sha256":sha(run),"manifest_sha256":sha(mb),"errors":errors,"stops":stops,"fails":fails,"rows":summ,"disposition":disposition}
    (output/"audit.json").write_text(json.dumps(report,sort_keys=True,indent=2,ensure_ascii=False)+"\n");print(json.dumps(report,ensure_ascii=False));return 1 if errors else 0
if __name__=="__main__":raise SystemExit(main())
