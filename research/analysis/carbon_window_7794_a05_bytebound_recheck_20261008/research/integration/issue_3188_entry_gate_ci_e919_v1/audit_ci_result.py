import copy,hashlib,itertools,json,pathlib,sys
F=["physical_task_effect_endpoint","task_effect_contract","matched_arm","arm_bound_audit","terminal_integrity"]
S={"workflow_sha256":"44dd333a2a5da2f9cf67dc4e4bc80750af3bcab3d8e1e8e130ada71d07bc53d7","run_py_sha256":"e104bf12925ef7878e7972c768cb19ecfdfe699303667bebf0ee6a0276f05822","audit_py_sha256":"72a5f6dcffff0e9d3a5e2daa58937bb4ab440ca789d824f183f168abc57e458d"}
R="8460a9ca79611929cbd6d2f6930067a06c6f177e7da3287ad07d1b7f483cb324"
I="sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9"
Q="PASS_AUDIT rows=37 vectors=32 authorize=1 current=HOLD controls=5/5"
C={"missing_receipt":(True,True,True,True,False),"stale_binding":(True,True,False,True,True),"unknown_boundary":(False,True,True,True,True),"cleanup_failure":(True,True,True,True,False),"corrupt_recomputation":(True,True,True,False,True)}
def sem(d):
 e=[]
 if type(d)is not dict or set(d)!={"schema","fields","vectors","controls"}: return ["shape"]
 if d["schema"]!="map01-recovery-entry-gate-3008-v2" or d["fields"]!=F:e.append("schema/order")
 v=d["vectors"]
 if type(v)is not list or len(v)!=32:return e+["vector count"]
 for i,b in enumerate(itertools.product((False,True),repeat=5)):
  x=v[i]
  if type(x)is not dict or set(x)!=set(F)|{"decision"}:e.append(f"vector shape {i}");continue
  a=tuple(x.get(k) for k in F)
  if any(type(z)is not bool for z in a) or a!=b:e.append(f"vector/order {i}")
  if x.get("decision")!=("AUTHORIZE" if all(b) else "HOLD"):e.append(f"vector label {i}")
 c=d["controls"]
 if type(c)is not list or len(c)!=5:return e+["controls count"]
 if [x.get("name") for x in c]!=list(C):e.append("controls names/order")
 for x in c:
  n=x.get("name")
  if type(x)is not dict or set(x)!=set(F)|{"name","decision"}:e.append(f"control shape {n}");continue
  a=tuple(x.get(k) for k in F)
  if any(type(z)is not bool for z in a) or a!=C.get(n):e.append(f"control bits {n}")
  if x.get("decision")!="HOLD":e.append(f"control label {n}")
 return e
def srcok(m):
 s=m.get("source",{})
 return all(s.get(k)==v for k,v in S.items()) and s.get("commit")=="e9198a1c74ef4ca2759e92c4539b10dbe3a20ba8" and s.get("workflow_path")==".github/workflows/map01-recovery-entry-gate-3008-v2.yml"
def logok(t):
 return t.count("RAW vectors=32 controls=5")==2 and t.count(Q)==2 and all(x in t for x in ("e9198a1c74ef4ca2759e92c4539b10dbe3a20ba8","docker run --rm --network none",I,"ubuntu-24.04","Version: 20260907.300.1","Artifact ID 10611375709"))
def audit(n,c,m,t):
 e=[]
 if hashlib.sha256(n).hexdigest()!=R or hashlib.sha256(c).hexdigest()!=R:e.append("raw digest")
 if n!=c:e.append("native/container differ")
 try:a=json.loads(n);b=json.loads(c)
 except Exception as x:return {"status":"FAIL_INDEPENDENT_ENTRY_GATE_AUDIT","errors":["JSON "+str(x)]}
 e+=["native "+x for x in sem(a)]+["container "+x for x in sem(b)]
 if a!=b:e.append("decoded outputs differ")
 if not srcok(m):e.append("frozen source identity")
 run=m.get("run",{})
 if (run.get("id"),run.get("attempt"),run.get("head_sha"))!=(35529905690,1,"e9198a1c74ef4ca2759e92c4539b10dbe3a20ba8"):e.append("run identity")
 z=m.get("container",{})
 if (z.get("requested_image"),z.get("resolved_digest"),z.get("network"))!=("python:3.12-slim",I,"none"):e.append("container identity")
 if not logok(t):e.append("run log summaries/identity")
 d=copy.deepcopy(b);d["vectors"][0][F[0]]=True
 m2=copy.deepcopy(m);m2["source"]["run_py_sha256"]="0"*64
 d2=copy.deepcopy(b);d2["vectors"][-1]["decision"]="HOLD"
 probes={"single_vector_corruption":bool(sem(d)),"summary_count_corruption":not logok(t.replace("RAW vectors=32 controls=5","RAW vectors=31 controls=5",1)),"source_hash_corruption":not srcok(m2),"expected_class_label_corruption":bool(sem(d2))}
 if not all(probes.values()):e.append("corruption control accepted")
 return {"status":"PASS_INDEPENDENT_ENTRY_GATE_AUDIT" if not e else "FAIL_INDEPENDENT_ENTRY_GATE_AUDIT","errors":e,"run_id":run.get("id"),"source_commit":m.get("source",{}).get("commit"),"raw_sha256_native":hashlib.sha256(n).hexdigest(),"raw_sha256_container":hashlib.sha256(c).hexdigest(),"native_container_identical":n==c,"vectors":len(b.get("vectors",[])),"authorize":sum(x.get("decision")=="AUTHORIZE" for x in b.get("vectors",[])),"hold_vectors":sum(x.get("decision")=="HOLD" for x in b.get("vectors",[])),"negative_controls":len(b.get("controls",[])),"current":"HOLD","corruption_controls_rejected":probes}
def main():
 p=pathlib.Path(__file__).resolve().parent
 r=audit((p/"raw/native.json").read_bytes(),(p/"raw/container.json").read_bytes(),json.loads((p/"FREEZE.json").read_text()),(p/"ACTIONS-LOG.txt").read_text())
 print(json.dumps(r,indent=2,sort_keys=True))
 if r["status"]!="PASS_INDEPENDENT_ENTRY_GATE_AUDIT":raise SystemExit(1)
if __name__=="__main__":main()
