#!/usr/bin/env python3
"""Source-bound XDamage v3 runner. Formal mode is single-shot and must not be retried."""
import argparse, hashlib, json, os, pathlib, platform, random, select, shutil, subprocess, sys, time
from exact_gate import ExactGate, Frame

HERE=pathlib.Path(__file__).resolve().parent
CASES=("QUIET","REPAINT_A","PERSIST_B","ABA_1PX","ABA_2X2","ABA_8X8")
KIND={name:i for i,name in enumerate(CASES)}
ALLOC="xdamage-temporal-boundary-3935-v3-20260927-01"
IMAGE="agent-interface-gtk-preflight:local"
IMAGE_ID="sha256:e2a7634d2b9627ec037c488d6aa472c6c00d5ef0dda6e302f7dced8b9b8752d4"

def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def write_json(path,obj): pathlib.Path(path).write_text(json.dumps(obj,sort_keys=True,indent=2)+"\n")
def exact_gate(baseline,endpoint):
    gate=ExactGate("O1","xdamage-formal")
    first=gate.push(baseline,observed_ns=1,action_id="baseline")
    # Deliberately do not pass the middle frame to the candidate gate.
    final=gate.push(endpoint,observed_ns=2,action_id="endpoint")
    return {"baseline_forwarded":first.frame is not None,"endpoint_forwarded":final.frame is not None,
            "endpoint_changed":final.frame is not None,"middle_used_by_candidate":False,
            "action_authority":False,"sequence":final.sequence,"base_sequence":final.base_sequence}

def source_hashes():
    names=("run_formal.py","xdamage_native.c","audit_formal.py","exact_gate.py",
           "temporal_protocol.py","test_temporal_protocol.py","run_container.ps1")
    return {name:sha(HERE/name) for name in names}

def start_xvfb(session,root):
    err=(root/f"xvfb_s{session:02d}.stderr").open("wb")
    p=subprocess.Popen(["Xvfb","-displayfd","1","-screen","0","128x128x24","-nolisten","tcp","-ac"],stdout=subprocess.PIPE,stderr=err,text=True)
    ready,_,_=select.select([p.stdout],[],[],10)
    if not ready:
        p.terminate();p.wait(timeout=5);err.close();raise TimeoutError("Xvfb display allocation timed out")
    display_no=int(p.stdout.readline().strip())
    return p,display_no,err

def frame(path): return Frame(64,64,"RGB",pathlib.Path(path).read_bytes())
def case_order(session):
    k=session%len(CASES)
    return CASES[k:]+CASES[:k]

def verify_freeze():
    freeze_path=HERE/"FREEZE.json"
    freeze=json.loads(freeze_path.read_text())
    if freeze.get("allocation")!=ALLOC or freeze.get("base_main_sha")!="c1e6f24d259f96b4d4dbf211e83fcdf6b9e0a4dd":
        raise RuntimeError("STOP_FREEZE_ALLOCATION_OR_BASE_MISMATCH")
    if freeze.get("image_id")!=IMAGE_ID or freeze.get("image")!=IMAGE:
        raise RuntimeError("STOP_FREEZE_IMAGE_MISMATCH")
    gate_bytes=(HERE/"exact_gate.py").read_bytes()
    gate_blob=hashlib.sha1(b"blob "+str(len(gate_bytes)).encode()+b"\0"+gate_bytes).hexdigest()
    if gate_blob!="d2629bc94d40cc0a8e1bf9e053585549218629ed" or freeze.get("exact_gate_git_blob")!=gate_blob:
        raise RuntimeError("STOP_EXACT_GATE_BLOB_MISMATCH")
    for name,expected in freeze.get("source_sha256",{}).items():
        if sha(HERE/name)!=expected: raise RuntimeError("STOP_SOURCE_HASH_MISMATCH:"+name)
    if len(freeze.get("source_sha256",{}))<5: raise RuntimeError("STOP_FREEZE_INCOMPLETE_SOURCE_SET")
    return freeze

def run(args):
    out=pathlib.Path(args.out).resolve()
    out.mkdir(parents=True,exist_ok=False)
    state={"allocation":ALLOC,"mode":args.mode,"sessions":args.sessions,"started_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"formal_invocation":0}
    try: freeze=verify_freeze()
    except Exception as exc:
        state.update(disposition="STOP_PREFLIGHT",error=repr(exc));write_json(out/"STOP.json",state);return 2
    if args.mode=="formal":
        marker=out/"FORMAL_INVOCATION_STARTED.json"
        # O_EXCL makes accidental second use of this exact output impossible.
        fd=os.open(marker,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        with os.fdopen(fd,"w") as f: json.dump({"allocation":ALLOC,"started":state["started_utc"]},f)
        state["formal_invocation"]=1;state["freeze_sha256"]=sha(HERE/"FREEZE.json")
    else:
        write_json(out/"CONSTRUCTION_NOT_FORMAL.json",{"allocation":ALLOC,"formal_count":0,"mode":"excluded construction"})
    native=out/"xdamage_native"
    build=subprocess.run(["gcc","-O2","-Wall","-Wextra",str(HERE/"xdamage_native.c"),"-o",str(native),"-lX11","-ldl"],capture_output=True,text=True)
    (out/"build.stdout").write_text(build.stdout);(out/"build.stderr").write_text(build.stderr)
    if build.returncode: state.update(disposition="STOP_BUILD",build_exit=build.returncode);write_json(out/"STOP.json",state);return 2
    native_hash=sha(native)
    sessions=args.sessions
    rows=[]
    try:
        for session in range(sessions):
            xv,display_no,xvlog=start_xvfb(session,out)
            env=os.environ.copy();env["DISPLAY"]=f":{display_no}"
            try:
                for case in case_order(session):
                    prefix=out/f"s{session+1:02d}_{case}"
                    cp=subprocess.run([str(native),"observe",str(KIND[case]),str(prefix)],env=env,capture_output=True,text=True,timeout=15)
                    (out/f"s{session+1:02d}_{case}.observer.stderr").write_text(cp.stderr)
                    if cp.returncode!=0: raise RuntimeError(f"observer exit {cp.returncode}: {case}")
                    receipt=json.loads(cp.stdout)
                    bpath=pathlib.Path(str(prefix)+"_baseline.rgb");mpath=pathlib.Path(str(prefix)+"_middle.rgb");epath=pathlib.Path(str(prefix)+"_endpoint.rgb")
                    b,m,e=frame(bpath),frame(mpath),frame(epath)
                    gate=exact_gate(b,e)
                    row={"allocation":ALLOC,"session":session+1,"case":case,"observer_exit":cp.returncode,
                         "observer":receipt,"xvfb_pid":xv.pid,"display":display_no,"baseline_file":bpath.name,
                         "native_executable_sha256":native_hash,
                         "middle_file":mpath.name,"endpoint_file":epath.name,
                         "baseline_sha256":sha(bpath),"middle_sha256":sha(mpath),"endpoint_sha256":sha(epath),
                         "gate":gate,"damage_disposition":"DAMAGE_OBSERVED" if receipt["damage_count"] else ("NO_DAMAGE_OBSERVED_SCOPED" if case=="QUIET" else "UNKNOWN")}
                    rows.append(row)
                    with (out/"rows.jsonl").open("a",encoding="utf-8") as log: log.write(json.dumps(row,sort_keys=True)+"\n")
                    print(json.dumps({"session":session+1,"case":case,"damage":receipt["damage_count"],"gate_forwards":gate["endpoint_forwarded"]}),flush=True)
            finally:
                xv.terminate();xv_exit=xv.wait(timeout=5);xvlog.close()
                state.setdefault("xvfb_exits",[]).append({"session":session+1,"pid":xv.pid,"exit":xv_exit})
        state.update(disposition="CANDIDATE_COMPLETE",rows=len(rows),native_sha256=native_hash,
                     runner_sha256=sha(HERE/"run_formal.py"),gate_sha256=sha(HERE/"exact_gate.py"),
                     auditor_sha256=sha(HERE/"audit_formal.py"),protocol_sha256=sha(HERE/"temporal_protocol.py"),
                     test_sha256=sha(HERE/"test_temporal_protocol.py"),container_sha256=sha(HERE/"run_container.ps1"),
                     source_commit=os.environ.get("SOURCE_GIT_COMMIT"),freeze_sha256=sha(HERE/"FREEZE.json"),
                     code_sha256=source_hashes(),
                     frozen_source_sha256=freeze.get("source_sha256"),
                     source_sha256=sha(HERE/"xdamage_native.c"),python=sys.version,platform=platform.platform(),
                     image=IMAGE,image_id=IMAGE_ID,network="none",gpu_used=False)
        write_json(out/"candidate_summary.json",state)
        return 0
    except Exception as exc:
        state.update(disposition="STOP_PARTIAL",rows=len(rows),native_sha256=native_hash,error=repr(exc))
        write_json(out/"STOP.json",state)
        return 2

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--mode",choices=("construction","formal"),required=True);p.add_argument("--sessions",type=int,default=1);p.add_argument("--out",required=True);a=p.parse_args()
    if a.mode=="formal" and a.sessions!=8:p.error("formal requires exactly 8 sessions")
    if a.mode=="construction" and not 1<=a.sessions<=2:p.error("construction is limited to one or two sessions")
    raise SystemExit(run(a))
