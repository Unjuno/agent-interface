from __future__ import annotations
import copy, json, ntpath, sys
from pathlib import Path

EXPECTED={
 "repo-root":(True,""),"workspace-root":(True,""),"repo-file":(True,"\\plain.txt"),
 "workspace-unicode":(True,"\\folder space\\café 資料.txt"),"repo-dir-space":(True,"\\work dir"),
 "in-root-dir-symlink":(True,"\\folder space\\café 資料.txt"),
 "host-absolute":(False,None),"drive-absolute":(False,None),"unc":(False,None),
 "device-namespace":(False,None),"device-dot":(False,None),"parent-traversal":(False,None),
 "encoded-dot":(False,None),"nested-encoded-dot":(False,None),"deep-encoded-dot":(False,None),
 "encoded-separator":(False,None),"encoded-backslash":(False,None),"raw-backslash":(False,None),
 "empty-component":(False,None),"dot-component":(False,None),"nul":(False,None),
 "external-symlink":(False,None),"missing":(False,None),"win-device-nul":(False,None),
 "win-device-con-extension":(False,None),"win-device-aux":(False,None),"win-device-com1":(False,None),
 "win-device-lpt9":(False,None)
}
DEVICE={"CON","PRN","AUX","NUL",*(f"COM{i}" for i in range(1,10)),*(f"LPT{i}" for i in range(1,10))}

def audit(data):
 errors=[]
 if data.get("schema")!="broker-path-windows-parity-4876-v1": errors.append("schema")
 if data.get("allocation")!="broker-path-windows-parity-4876-20260927-01": errors.append("allocation")
 if data.get("candidate_blob")!="cdd0e3d57e08a316fc9df6b55abca8c740db070d": errors.append("candidate_blob")
 if data.get("production_broker_blob")!="5734f54f318db9ac5e96b2bed6f6bed105ac39ff": errors.append("broker_blob")
 if data.get("os")!="win32" or not str(data.get("python","")).startswith("3.11.9"): errors.append("runtime_identity")
 cases=data.get("cases")
 if not isinstance(cases,list) or len(cases)!=len(EXPECTED): return errors+["case_count"]
 by={x.get("name"):x for x in cases if isinstance(x,dict)}
 if len(by)!=len(cases) or set(by)!=set(EXPECTED): errors.append("case_identity")
 root=data.get("root")
 if not isinstance(root,str) or not ntpath.splitdrive(root)[0]: errors.append("root_not_drive_absolute")
 for name,(accepted,suffix) in EXPECTED.items():
  row=by.get(name)
  if row is None: continue
  if row.get("expected_accept") is not accepted or row.get("expected_suffix")!=suffix: errors.append("frozen_expectation:"+name)
  actual=row.get("actual")
  if accepted:
   expected=ntpath.normcase(ntpath.normpath(root+suffix))
   if actual is None or ntpath.normcase(ntpath.normpath(actual))!=expected: errors.append("canonical_target:"+name)
   drive,tail=ntpath.splitdrive(actual or "")
   rdrive,rtail=ntpath.splitdrive(root)
   if ntpath.normcase(drive)!=ntpath.normcase(rdrive) or not (ntpath.normcase(actual or "")==ntpath.normcase(root) or ntpath.normcase(actual or "").startswith(ntpath.normcase(root.rstrip("\\\\")+"\\") )): errors.append("root_containment:"+name)
   if actual and (actual.startswith("\\\\\\\\?\\") or actual.startswith("\\\\\\\\.\\")): errors.append("device_namespace_returned:"+name)
  elif actual is not None:
   errors.append("forbidden_case_returned_path:"+name)
   drive,_=ntpath.splitdrive(actual)
   if drive or actual.startswith("\\\\\\\\") or ntpath.basename(actual).split(".")[0].upper() in DEVICE: errors.append("host_or_device_escape:"+name)
 return errors

def main(src,out):
 raw=Path(src).read_bytes()
 try: data=json.loads(raw)
 except Exception as exc:
  result={"decision":"STOP_RAW_INVALID","errors":[type(exc).__name__]}
 else:
  errors=audit(data)
  controls=[]
  mutations=[]
  m=copy.deepcopy(data); m["cases"][0]["actual"]="D:\\outside\\schema.json"; mutations.append(("valid_path_escape",m))
  m=copy.deepcopy(data); m["cases"][6]["actual"]="D:\\outside\\secret.txt"; mutations.append(("forbidden_host_path",m))
  m=copy.deepcopy(data); m["cases"].pop(); mutations.append(("missing_case",m))
  m=copy.deepcopy(data); m["cases"][0]["expected_suffix"]="\\changed"; mutations.append(("expectation_tamper",m))
  m=copy.deepcopy(data); m["candidate_blob"]="wrong"; mutations.append(("source_flip",m))
  for name,item in mutations: controls.append({"name":name,"rejected":bool(audit(item))})
  result={"decision":"PASS_INDEPENDENT_AUDIT" if not errors and all(x["rejected"] for x in controls) else "FAIL_INDEPENDENT_AUDIT",
          "rows":len(data.get("cases",[])),"errors":errors,"controls":controls,"rejected_controls":sum(x["rejected"] for x in controls),"raw_bytes":len(raw)}
  out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(result,sort_keys=True))
 return 0 if result.get("decision")=="PASS_INDEPENDENT_AUDIT" else 1

if __name__=="__main__":
 if len(sys.argv)!=3: raise SystemExit("usage: audit_windows_probe.py RAW AUDIT")
 raise SystemExit(main(Path(sys.argv[1]),Path(sys.argv[2])))

