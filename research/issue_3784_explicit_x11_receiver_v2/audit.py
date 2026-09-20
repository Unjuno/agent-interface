"""Independent read-only audit for #3791 formal-02."""
import hashlib,json,re,sys
from pathlib import Path
BASE="f5f9ff842fd061e6e1eb2f43a17cc7785b807fc7"
IMAGE="agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27"
MATRIX=[("de-01","de"),("de-02","de"),("de-03","de"),("us-control","us")]
FORMULA="=B2*A2"
def sha(b):return hashlib.sha256(b).hexdigest()
def blob(b):return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def fp(m):return sha(json.dumps(m,sort_keys=True,separators=(",",":")).encode())
def inventory(root):return {p.relative_to(root).as_posix():sha(p.read_bytes()) for p in sorted(root.rglob("*")) if p.is_file() and p.name!="raw.json"}
def expected(chords):
    out=[]
    for chord in chords:out += [("KeyPress",int(c)) for c in chord]+[("KeyRelease",int(c)) for c in reversed(chord)]
    return out
def main():
    evidence,source,output=map(lambda p:Path(p).resolve(),sys.argv[1:4]);output.mkdir(parents=True,exist_ok=True)
    if any(output.iterdir()):raise SystemExit("STOP_AUDIT_OUTPUT_NOT_EMPTY")
    rawb=(evidence/"raw.json").read_bytes();raw=json.loads(rawb)
    mbytes=(source/"research/issue_3784_explicit_x11_receiver_v2/source_manifest.json").read_bytes();m=json.loads(mbytes)
    runner=(source/"research/issue_3784_explicit_x11_receiver_v2/runner.py").read_bytes()
    errors=[];stops=[];fails=[];summary=[]
    if raw.get("allocation")!="issue3784-explicit-x11-receiver-formal-02":errors.append("ALLOCATION")
    if raw.get("base_commit")!=BASE or m.get("base_commit")!=BASE:errors.append("BASE")
    if raw.get("image")!=IMAGE:errors.append("IMAGE")
    if raw.get("runner_sha256")!=sha(runner):errors.append("RUNNER_BINDING")
    if raw.get("source_manifest_sha256")!=sha(mbytes):errors.append("MANIFEST_BINDING")
    if m.get("candidate_blob")!="9cae101a219348077668c8fc086acf8e13154afe":errors.append("CANDIDATE_BLOB")
    for p,e in m.get("files",{}).items():
        b=(source/p).read_bytes()
        if sha(b)!=e["sha256"] or blob(b)!=e["git_blob_sha1"]:errors.append("SOURCE:"+p)
    if inventory(evidence)!=raw.get("artifact_sha256"):errors.append("ARTIFACT_INVENTORY")
    rows=raw.get("rows",[])
    if len(rows)!=4:stops.append("INCOMPLETE_MATRIX")
    for r,(cid,layout) in zip(rows,MATRIX):
        case=evidence/"cases"/cid
        if r.get("case_id")!=cid or r.get("layout")!=layout:errors.append("ROW_ID:"+cid)
        if r.get("xvfb_argv",[]) [-1:]!=["-noreset"]:errors.append("NO_RESET:"+cid)
        if r.get("xvfb_cleanup",{}).get("reaped") is not True:errors.append("XVFB_REAP:"+cid)
        rp=case/"row.json"
        if not rp.is_file() or json.loads(rp.read_text())!=r:errors.append("ROW_BINDING:"+cid)
        recv=r.get("receiver",{})
        if recv.get("class")!="InputOnly" or recv.get("mapped") is not True or recv.get("event_mask")!=3:errors.append("RECEIVER:"+cid)
        if r.get("focus_verified") is not True or recv.get("window_id")!=recv.get("focus_window_id"):stops.append("FOCUS:"+cid)
        c=r.get("receiver_control",[])
        good=len(c)==2 and [(x.get("type"),x.get("keycode"),x.get("keysym"),x.get("lookup_text")) for x in c]==[("KeyPress",c[0].get("keycode") if c else None,97,"a"),("KeyRelease",c[0].get("keycode") if c else None,97,"a")]
        if r.get("receiver_control_ok") is not good:errors.append("CONTROL_GATE_BINDING:"+cid)
        if not good:stops.append("RECEIVER_CONTROL:"+cid)
        base,after=r.get("baseline",{}),r.get("after",{})
        for phase,s,expected_layout in (("baseline",base,"us"),("after",after,layout)):
            q=s.get("query",{})
            if q.get("exit")!=0 or not s.get("layout_ok") or not any(t.strip()=="layout: "+expected_layout for t in q.get("stdout","").splitlines()):stops.append("LAYOUT:"+cid+":"+phase)
            dp=case/(phase+".xkb");mp=case/(phase+".map.json")
            if not dp.is_file() or not mp.is_file():
                (stops if r.get("status","").startswith("STOP_") else errors).append("MAP_ARTIFACT_NOT_REACHED:"+cid+":"+phase);continue
            dump=dp.read_bytes();mapping=json.loads(mp.read_text())
            if dump.decode()!=s.get("dump") or sha(dump)!=s.get("dump_sha256"):errors.append("DUMP_BINDING:"+cid+":"+phase)
            if mapping!=s.get("map") or fp(mapping)!=s.get("map_sha256"):errors.append("MAP_BINDING:"+cid+":"+phase)
        gate=r.get("map_gate",{});changed=layout=="de"
        if gate.get("query_layout") is not True or gate.get("dump_changed")!=changed or gate.get("fresh_map_changed")!=changed:stops.append("MAP_GATE:"+cid)
        if layout=="de" and (r.get("apply",{}).get("argv")!=["setxkbmap","-layout","de"] or r.get("apply",{}).get("exit")!=0):stops.append("APPLY:"+cid)
        if layout=="us" and r.get("apply",{}).get("argv") is not None:errors.append("CONTROL_MUTATION")
        status=r.get("status","")
        if r.get("plan_keycodes") is not None:
            u=r.get("unsupported",{})
            if not u.get("refused_zero_event") or u.get("before_events") or u.get("after_events") or u.get("emissions")!=0 or "U+20AC" not in str(u.get("error")):fails.append("UNSUPPORTED:"+cid)
            plan=r.get("plan_keycodes",[]);ev=r.get("events",[]);trace=[(e.get("type"),e.get("keycode")) for e in ev];want=expected(plan)
            text="".join(e.get("lookup_text","") for e in ev if e.get("type")=="KeyPress")
            if trace!=want:fails.append("TRACE:"+cid)
            if text!=FORMULA or r.get("typed")!=text:fails.append("TEXT:"+cid)
            if r.get("emissions")!=len(want):fails.append("EMISSIONS:"+cid)
            rel=r.get("release",{})
            if rel.get("verified") is not True or rel.get("keys_down")!=[] or rel.get("buttons_down")!=[]:fails.append("RELEASE:"+cid)
        else:
            text=""
            (stops if status.startswith("STOP_") else fails).append("CANDIDATE_STAGE_NOT_REACHED:"+cid)
        if status.startswith("STOP_"):stops.append("ROW_STOP:"+cid+":"+status)
        elif status.startswith("FAIL_"):fails.append("ROW_FAIL:"+cid+":"+status)
        summary.append({"case_id":cid,"status":status,"control_ok":good,"typed":text,"event_count":len(ev),"map_gate":gate})
    stat=[r.get("status") for r in rows]
    disp="PASS_GERMAN_FORMULA_DELIVERY" if len(rows)==4 and all(s=="PASS_ROW" for s in stat) else "FAIL_GERMAN_FORMULA_DELIVERY" if any(s.startswith("FAIL_") for s in stat) else "STOP_GERMAN_FORMULA_DELIVERY"
    if raw.get("disposition")!=disp:errors.append("DISPOSITION")
    auditdisp="FAIL_AUDIT_INTEGRITY" if errors else "PASS_AUDIT_CONFIRMED_STOP" if stops else "PASS_AUDIT_CONFIRMED_FAIL" if fails else "PASS_AUDIT_CONFIRMED_DELIVERY"
    result={"schema":"agent-interface/issue3784-formal02-audit-v1","raw_sha256":sha(rawb),"runner_sha256":sha(runner),"manifest_sha256":sha(mbytes),"errors":errors,"stops":stops,"fails":fails,"rows":summary,"disposition":auditdisp}
    (output/"audit.json").write_text(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(result,ensure_ascii=False));return 1 if errors else 0
if __name__=="__main__":raise SystemExit(main())
