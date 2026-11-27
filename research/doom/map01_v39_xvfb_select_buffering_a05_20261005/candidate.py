import hashlib,json,platform,sys
from pathlib import Path
import audit_v2
INPUT=Path(sys.argv[1]); OUT=Path(sys.argv[2]); OUT.mkdir(parents=True,exist_ok=True)
def sha(b): return hashlib.sha256(b).hexdigest()
audit_freeze=json.loads((INPUT/"FREEZE_A03.json").read_text())
experiment_freeze=json.loads(Path("/src/FREEZE.json").read_text())
expect_bytes=(INPUT/"AUDIT_EXPECTATIONS_V2.json").read_bytes()
probe=(INPUT/"probe.py").read_bytes()
raw_bytes=(INPUT/"RAW.json").read_bytes()
audit_bytes=Path("/src/audit_v2.py").read_bytes()
checks={"audit_v2_sha256":sha(audit_bytes),"freeze_a03_sha256":sha((INPUT/"FREEZE_A03.json").read_bytes()),"probe_sha256":sha(probe),"raw_sha256":sha(raw_bytes),"expectations_sha256":sha(expect_bytes)}
# The input values are frozen before the role starts; no candidate output is written on mismatch.
expected=experiment_freeze["inputs"]
for key,value in checks.items():
 if value!=expected[key]: raise SystemExit("STOP_INPUT_IDENTITY:"+key)
expect=json.loads(expect_bytes); original=json.loads(raw_bytes)
variants=[("baseline",None),("status_contradiction",("status","FAIL_DIAGNOSTIC_CONTRACT")),("display_contradiction",("display",":188")),("python_xlib_contradiction",("python_xlib",[0,34]))]
rows=[]
for name,mutation in variants:
 obj=json.loads(raw_bytes)
 if mutation: obj[mutation[0]]=mutation[1]
 data=json.dumps(obj,indent=2,sort_keys=True).encode()+b"\n"
 result=audit_v2.audit(data,obj,audit_freeze,probe,expect)
 p=OUT/(name+".raw.json"); p.write_bytes(data)
 rows.append({"case":name,"mutation":{mutation[0]:mutation[1]} if mutation else None,"raw_path":p.name,"raw_sha256":sha(data),"audit_decision":result["decision"],"audit_errors":result["errors"],"audit_report":result})
cg={}
for n in ("cpu.max","memory.max","memory.swap.max"):
 try: cg[n]=Path("/sys/fs/cgroup",n).read_text().strip()
 except OSError as e: cg[n]="unavailable:"+type(e).__name__
report={"schema":"xvfb-audit-v3-candidate-v1","case_count":len(rows),
 "candidate_source_sha256":sha(Path("/src/candidate.py").read_bytes()),
 "audit_source_sha256":checks["audit_v2_sha256"],"input_hashes":checks,
 "runtime":{"python":platform.python_version(),"cgroup":cg},"cases":rows}
(OUT/"CANDIDATE.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
print(json.dumps({"status":"CANDIDATE_COMPLETE","case_count":len(rows),"decisions":[r["audit_decision"] for r in rows],"runtime":report["runtime"]},sort_keys=True))
