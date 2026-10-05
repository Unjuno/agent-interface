import hashlib,json,sys
from pathlib import Path
R=Path("/src");O=Path("/out");F=json.loads((R/"FROZEN_INPUTS.json").read_text())
def blob(b):return hashlib.sha1(b"blob "+str(len(b)).encode()+bytes([0])+b).hexdigest()
def sha(b):return hashlib.sha256(b).hexdigest()
errors=[]
actual_source_info={}
for p,want in F["source_blob_sha1"].items():
 try:
  b=(R/F.get("source_path_overrides",{}).get(p,p)).read_bytes()
  if blob(b)!=want:errors.append("source blob mismatch "+p)
  actual_source_info[p]={"blob":blob(b),"sha256":sha(b),"bytes":len(b)}
 except Exception as e:errors.append("source unreadable "+p+": "+repr(e))
candidate_sha=sha((R/"candidate.py").read_bytes())
auditor_sha=sha(Path(__file__).read_bytes())
if candidate_sha!=F["candidate_sha256"]:errors.append("candidate SHA256 mismatch")
if auditor_sha!=F["auditor_sha256"]:errors.append("auditor SHA256 mismatch")
try:
 r=json.loads((O/"candidate-result.json").read_text())
 trace=[json.loads(line) for line in (O/"operation-trace.jsonl").read_text().splitlines() if line]
except Exception as e:
 errors.append("raw result unreadable: "+repr(e));r={};trace=[]
if r.get("schema")!="map01-v39-v15-release-closure-a03-v1":errors.append("candidate result schema mismatch")
if r.get("run_id")!=F["run_id"]:errors.append("run id mismatch")
if r.get("main_sha")!=F["main_sha"]:errors.append("main SHA mismatch")
if r.get("session_selection")!={"default":"session_map01_v12.py","measurement":"session_map01_v15.py"}:errors.append("session selector mismatch")
if r.get("selected_classes")!={"backend":"doom_owner_thread_release_batch_backend_v1.Backend","executor":"executor_v13.Executor"}:errors.append("selected runtime classes mismatch")
if r.get("source_info")!=actual_source_info:errors.append("candidate source receipt mismatch")
b=r
if b.get("failure") is not None:errors.append("candidate has failure: "+str(b["failure"]))
if b.get("admission_keys")!=["F8","SPACE"]:errors.append("admission order mismatch")
if b.get("release_keys")!=["SPACE","F8"]:errors.append("release order mismatch")
if b.get("down_ids")!=b.get("up_ids") or set(b.get("down_ids",{}))!={"F8","SPACE"}:errors.append("actuation identity mismatch")
if b.get("release_verified") is not True:errors.append("release batch not verified")
if b.get("authority_false") is not True:errors.append("authority flags not false")
if b.get("physical_after")!=[] or b.get("backend_held_after")!=[]:errors.append("non-neutral final state")
if b.get("owner_stopped") is not True:errors.append("owner cleanup not confirmed")
up=[i for i,row in enumerate(trace) if row.get("op")=="up"]
if len(up)!=2:errors.append("wrong number of key-up injections")
between=trace[up[0]+1:up[1]] if len(up)==2 else []
observed=sum(row.get("op")=="query" for row in between)
if observed!=b.get("queries_between"):errors.append("query count does not reconstruct")
if between!=b.get("between"):errors.append("between-release trace copy mismatch")
expected="CONFIRMED_INTER_RELEASE_SAMPLING_IN_SELECTED_V15" if observed>0 else "NO_INTER_RELEASE_QUERY_OBSERVED"
if b.get("disposition")!=expected:errors.append("disposition mismatch")
if len([row for row in trace if row.get("op")=="down"])!=2:errors.append("down edge count mismatch")
if len([row for row in trace if row.get("op")=="up"])!=2:errors.append("up edge count mismatch")
status="PASS_AUDIT" if not errors else "FAIL_AUDIT"
out={"status":status,"main_sha":F["main_sha"],"candidate_sha256":candidate_sha,"auditor_sha256":auditor_sha,
 "query_events_between_releases":observed,"reconstructed_disposition":expected,"errors":errors,
 "checks":{"source_git_blobs":len(F["source_blob_sha1"]),"admissions":len(b.get("admission_keys",[])),
 "releases":len(b.get("release_keys",[])),"owner_neutral":b.get("physical_after")==[] and b.get("backend_held_after")==[],
 "authority_false":b.get("authority_false"),"owner_stopped":b.get("owner_stopped")}}
(O/"audit-result.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
(O/"audit.log").write_text(status+": "+json.dumps(out,sort_keys=True)+"\n")
print((O/"audit.log").read_text(),end="")
sys.exit(0 if status=="PASS_AUDIT" else 1)