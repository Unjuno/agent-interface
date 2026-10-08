"""Forensic independent audit of a pre-candidate baseline-parser STOP."""
import hashlib,json,re,sys
from pathlib import Path
EXPECTED_RAW="eced38b64c1c1e1f78c5bfd5dc30dcede5c5c9563f8bac73b71e29d4d98ed689"
RUNNER_SHA="ffe1b5d081775c511de50a0a626b6e43ff6f4e094069b3d40baa9e33b334246b"
MANIFEST_SHA="196fae86bcd15993d76a217457f7aa2922bd94f1b623c9dde2d843da62621431"
IDS=["de-01","de-02","de-03","us-control"]
def sha(b):return hashlib.sha256(b).hexdigest()
def blob(b):return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def fp(m):return sha(json.dumps(m,sort_keys=True,separators=(",",":")).encode())
def inventory(root):return {p.relative_to(root).as_posix():sha(p.read_bytes()) for p in sorted(root.rglob("*")) if p.is_file() and p.name!="raw.json"}
def main():
    evidence,source,output=map(lambda p:Path(p).resolve(),sys.argv[1:4]);output.mkdir(parents=True,exist_ok=True)
    if any(output.iterdir()):raise SystemExit("STOP_AUDIT_OUTPUT_NOT_EMPTY")
    rawb=(evidence/"raw.json").read_bytes();raw=json.loads(rawb)
    runner=(source/"research/issue_3784_explicit_x11_receiver_v2/runner.py").read_bytes()
    mb=(source/"research/issue_3784_explicit_x11_receiver_v2/source_manifest.json").read_bytes();m=json.loads(mb)
    errors=[];findings=[]
    if sha(rawb)!=EXPECTED_RAW:errors.append("RAW_SHA")
    if sha(runner)!=RUNNER_SHA or raw.get("runner_sha256")!=RUNNER_SHA:errors.append("RUNNER_SHA")
    if sha(mb)!=MANIFEST_SHA or raw.get("source_manifest_sha256")!=MANIFEST_SHA:errors.append("MANIFEST_SHA")
    if raw.get("allocation")!="issue3784-explicit-x11-receiver-formal-02" or raw.get("disposition")!="STOP_GERMAN_FORMULA_DELIVERY":errors.append("RAW_ID_OR_DISPOSITION")
    if inventory(evidence)!=raw.get("artifact_sha256"):errors.append("ARTIFACT_INVENTORY")
    for path,row in m.get("files",{}).items():
        b=(source/path).read_bytes()
        if sha(b)!=row["sha256"] or blob(b)!=row["git_blob_sha1"]:errors.append("SOURCE:"+path)
    if len(raw.get("rows",[]))!=4 or [r.get("case_id") for r in raw.get("rows",[])]!=IDS:errors.append("MATRIX")
    for r in raw.get("rows",[]):
        cid=r["case_id"];case=evidence/"cases"/cid;recv=r.get("receiver",{});control=r.get("receiver_control",[])
        if r.get("status")!="STOP_BASELINE":errors.append("ROW_STATUS:"+cid)
        if recv.get("class")!="InputOnly" or recv.get("window_id")!=recv.get("focus_window_id") or r.get("focus_verified") is not True:errors.append("FOCUS:"+cid)
        if not (r.get("receiver_control_ok") is True and len(control)==2 and [e.get("type") for e in control]==["KeyPress","KeyRelease"] and [e.get("lookup_text") for e in control]==["a","a"]):errors.append("CONTROL:"+cid)
        s=r.get("baseline",{});q=s.get("query",{});out=q.get("stdout","")
        if q.get("exit")!=0 or not re.search(r"(?m)^layout:\s+us\s*$",out):errors.append("QUERY_NOT_US:"+cid)
        if s.get("layout_ok") is not False:errors.append("PARSER_DID_NOT_STOP:"+cid)
        if s.get("dump_exit")!=0:errors.append("DUMP_EXIT:"+cid)
        dp=case/"baseline.xkb";mp=case/"baseline.map.json";rp=case/"row.json"
        if not dp.is_file() or not mp.is_file() or not rp.is_file():errors.append("BASELINE_ARTIFACT:"+cid)
        else:
            mapping=json.loads(mp.read_text())
            if dp.read_bytes().decode()!=s.get("dump") or sha(dp.read_bytes())!=s.get("dump_sha256"):errors.append("DUMP_BINDING:"+cid)
            if mapping!=s.get("map") or fp(mapping)!=s.get("map_sha256"):errors.append("MAP_BINDING:"+cid)
            if json.loads(rp.read_text())!=r:errors.append("ROW_BINDING:"+cid)
        if r.get("plan_keycodes") is not None or r.get("events") is not None or r.get("unsupported") is not None:errors.append("CANDIDATE_REACHED:"+cid)
        if r.get("xvfb_cleanup",{}).get("reaped") is not True:errors.append("XVFB_REAP:"+cid)
        findings.append({"case_id":cid,"status":r.get("status"),"control_ok":r.get("receiver_control_ok"),"query_layout_us":bool(re.search(r"(?m)^layout:\s+us\s*$",out)),"parser_layout_ok":s.get("layout_ok"),"candidate_reached":r.get("plan_keycodes") is not None,"xvfb_reaped":r.get("xvfb_cleanup",{}).get("reaped")})
    runner_text=runner.decode()
    if 's.strip()=="layout: "+layout' not in runner_text:errors.append("EXPECTED_PARSER_DEFECT_NOT_FOUND")
    disp="FAIL_AUDIT_INTEGRITY" if errors else "PASS_AUDIT_CONFIRMED_HARNESS_STOP"
    result={"schema":"agent-interface/issue3791-baseline-stop-forensic-audit-v2","raw_sha256":sha(rawb),"runner_sha256":sha(runner),"manifest_sha256":sha(mb),"errors":errors,"rows":findings,"cause":"query output contains variable-width whitespace accepted by a whitespace-tolerant parse but rejected by the runner's exact string equality; execution stopped before German map application or candidate planning","disposition":disp}
    (output/"audit.json").write_text(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(result,ensure_ascii=False));return 1 if errors else 0
if __name__=="__main__":raise SystemExit(main())
