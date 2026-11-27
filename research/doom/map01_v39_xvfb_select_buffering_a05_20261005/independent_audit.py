import hashlib,json,sys
from pathlib import Path
BUNDLE=Path(sys.argv[1]); OUT=Path(sys.argv[2]); OUT.mkdir(parents=True,exist_ok=True)
def sha(b): return hashlib.sha256(b).hexdigest()
freeze=json.loads((BUNDLE/"FREEZE.json").read_text()); source=BUNDLE/"SOURCE"; evidence=BUNDLE/"evidence"
candidate=json.loads((evidence/"candidate-output/CANDIDATE.json").read_text()); original=(source/"inputs/RAW.json").read_bytes()
expected=[("baseline",None,"PASS_METHOD_SCOPED_WITH_POSTRUN_IDENTITY_BINDING"),("status_contradiction",{"status":"FAIL_DIAGNOSTIC_CONTRACT"},"FAIL"),("display_contradiction",{"display":":188"},"FAIL"),("python_xlib_contradiction",{"python_xlib":[0,34]},"FAIL")]
errors=[]
if candidate.get("schema")!="xvfb-audit-v3-candidate-v1": errors.append("candidate schema")
if candidate.get("case_count")!=4 or len(candidate.get("cases",[]))!=4: errors.append("case cardinality")
if candidate.get("candidate_source_sha256")!=freeze["candidate_sha256"] or sha((BUNDLE/"candidate.py").read_bytes())!=freeze["candidate_sha256"]: errors.append("candidate source identity")
if sha(Path(__file__).read_bytes())!=freeze["independent_auditor_sha256"]: errors.append("independent auditor source identity")
if candidate.get("audit_source_sha256")!=freeze["inputs"]["audit_v2_sha256"] or sha((BUNDLE/"audit_v2.py").read_bytes())!=freeze["inputs"]["audit_v2_sha256"]: errors.append("audit-v2 source identity")
if sha(original)!=freeze["inputs"]["raw_sha256"]: errors.append("input raw identity")
if sha((source/"probe.py").read_bytes())!=freeze["inputs"]["probe_sha256"]: errors.append("probe identity")
if sha((source/"FREEZE_A03.json").read_bytes())!=freeze["inputs"]["freeze_a03_sha256"]: errors.append("freeze identity")
if sha((source/"inputs/AUDIT_EXPECTATIONS_V2.json").read_bytes())!=freeze["inputs"]["expectations_sha256"]: errors.append("expectations identity")
actual={r.get("case"):r for r in candidate.get("cases",[])}
if set(actual)!=set(x[0] for x in expected): errors.append("case identity set")
for name,mutation,decision in expected:
 row=actual.get(name,{})
 rawname=row.get("raw_path","")
 if Path(rawname).name!=rawname: errors.append(name+": unsafe output path"); continue
 p=evidence/"candidate-output"/rawname
 if not p.is_file(): errors.append(name+": raw output missing"); continue
 data=p.read_bytes()
 if sha(data)!=row.get("raw_sha256"): errors.append(name+": raw hash")
 obj=json.loads(data); expected_obj=json.loads(original)
 if mutation:
  for key,value in mutation.items(): expected_obj[key]=value
 if obj!=expected_obj: errors.append(name+": unexpected raw mutation delta")
 if row.get("audit_decision")!=decision: errors.append(name+": preregistered decision mismatch: "+str(row.get("audit_decision")))
 nested=row.get("audit_report",{})
 if nested.get("raw_sha256")!=sha(data): errors.append(name+": nested raw digest")
 if nested.get("decision")!=row.get("audit_decision"): errors.append(name+": nested decision")
 if nested.get("errors")!=row.get("audit_errors"): errors.append(name+": nested errors")
 if name=="baseline" and row.get("audit_errors")!=[]: errors.append("baseline errors")
decision="PASS_AUDIT_CONSISTENCY_SCOPED" if not errors else "FAIL_AUDIT_CONSISTENCY"
report={"schema":"xvfb-audit-v3-independent-audit-v1","allocation":freeze["allocation"],
 "candidate_source_sha256":freeze["candidate_sha256"],"auditor_source_sha256":freeze["independent_auditor_sha256"],
 "candidate_cases":len(actual),"checked_raw_sha256":[actual[name].get("raw_sha256") for name,_,_ in expected if name in actual],
 "errors":errors,"decision":decision}
(OUT/"AUDIT.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
print(json.dumps(report,sort_keys=True))
raise SystemExit(0 if not errors else 1)
