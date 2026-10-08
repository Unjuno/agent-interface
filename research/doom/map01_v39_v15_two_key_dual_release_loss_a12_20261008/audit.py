import hashlib,json,pathlib,sys
KEYS=["F8","F9"];CODES={"F8":38,"F9":39}
def validate(raw):
 e=[]
 def ck(v,n):
  if not v:e.append(n)
 ck(raw.get("run_id")=="a12-two-key-dual-release-loss-20261008","run_id");ck(raw.get("source_base")=="712a71b25dc024b5406b24b568225c0663e7278b","source_base")
 cases=raw.get("cases");ck(isinstance(cases,list) and len(cases)==2,"case_count")
 if not isinstance(cases,list) or len(cases)!=2:return {"status":"FAIL","errors":e}
 for ci,x in enumerate(cases):
  t=ci==1;n=2 if t else 1
  ck(x.get("injected_keyrelease_loss") is t,f"case{ci}_arm");ck(x.get("dropped_keyrelease_count")== (2 if t else 0),f"case{ci}_drops")
  ck(x.get("server_keycodes_down_after_executor_release")==[],f"case{ci}_final_map");ck(x.get("owner_close_error") is None,f"case{ci}_close")
  term=x.get("executor_terminal") or {};rel=term.get("release") or {}
  ck(term.get("status")=="completed",f"case{ci}_terminal");ck(rel.get("verified") is True and rel.get("keys_down")==[] and rel.get("buttons_down")==[],f"case{ci}_terminal_release")
  rows=[r for r in x.get("events",[]) if r.get("event")=="input_release_transition"]
  ck([r.get("key") for r in rows]==KEYS and len(rows)==2,f"case{ci}_rows")
  owners=set();tokens=set();samples=[]
  for i,k in enumerate(KEYS):
   if i>=len(rows):continue
   r=rows[i];q=r.get("owner_thread_keyup_receipt") or {};a=q.get("server_keyup_attempts") or []
   ck(r.get("release_batch_position")==i and r.get("release_batch_size")==2,f"case{ci}_{k}_position")
   ck(r.get("owner_thread_keyup_receipt_count")==1 and r.get("owner_thread_keyup_verified") is True,f"case{ci}_{k}_joined")
   ck(r.get("key")==k and q.get("key")==k and q.get("keycode")==CODES[k],f"case{ci}_{k}_identity")
   ck(q.get("server_keyup_verified") is True and q.get("server_key_down_after_keyup") is False,f"case{ci}_{k}_verified")
   ck(q.get("physical_verification_authoritative") is False and r.get("physical_verification_authoritative") is False and r.get("grants_input_authority") is False,f"case{ci}_{k}_authority")
   ck(q.get("release_batch_key_order")==KEYS and q.get("release_batch_initial_up_count")==2,f"case{ci}_{k}_batch")
   ck(len(a)==n and q.get("server_keyup_attempt_count")==n,f"case{ci}_{k}_attempt_count")
   if len(a)==n:
    ck([z.get("server_key_down_after") for z in a]==([True,False] if t else [False]),f"case{ci}_{k}_attempt_states")
    ck(all(z.get("keyrelease_error") is None and z.get("sync_error") is None for z in a),f"case{ci}_{k}_errors")
    samples.append(a[0].get("keymap_sampled_ns"))
   owners.add(q.get("owner_id"));tokens.add(q.get("intent_token"))
   ck(type(q.get("owner_keyrelease_started_ns")) is int and type(q.get("owner_sync_returned_ns")) is int and q["owner_keyrelease_started_ns"]<=q["owner_sync_returned_ns"],f"case{ci}_{k}_times")
  ck(len(owners)==1 and None not in owners,f"case{ci}_owner");ck(len(tokens)==1 and None not in tokens,f"case{ci}_intent")
  ck(len(samples)==2 and samples[0]==samples[1],f"case{ci}_shared_sample")
 return {"status":"PASS_CONSTRUCTION_SCOPED" if not e else "FAIL","errors":e}
def verify_sources(manifest,src):
 e=[]
 if set(src)!=set(manifest.get("files",{})):e.append("path_set")
 for p,m in manifest.get("files",{}).items():
  b=src.get(p)
  if b is None:e.append("missing:"+p);continue
  if hashlib.sha256(b).hexdigest()!=m.get("sha256"):e.append("sha256:"+p)
  if hashlib.sha1(b"blob "+str(len(b)).encode()+bytes([0])+b).hexdigest()!=m.get("git_blob"):e.append("git_blob:"+p)
 return {"status":"PASS" if not e else "FAIL","errors":e,"files":len(src)}
def main():
 root=pathlib.Path(__file__).parent;raw=json.loads((root/"results/candidate.json").read_text());o=validate(raw);m=json.loads((root/"source-manifest.json").read_text());s={p:(root/"source_snapshot"/p).read_bytes() for p in m["files"]};o["source_verification"]=verify_sources(m,s);o["candidate_sha256"]=hashlib.sha256((root/"candidate.py").read_bytes()).hexdigest();o["raw_sha256"]=hashlib.sha256((root/"results/candidate.json").read_bytes()).hexdigest();o["run_id"]="a12-two-key-dual-release-loss-20261008";(root/"results/audit.json").write_text(json.dumps(o,indent=2,sort_keys=True)+chr(10));print(json.dumps(o,sort_keys=True));return 0 if o["status"]=="PASS_CONSTRUCTION_SCOPED" and o["source_verification"]["status"]=="PASS" else 1
if __name__=="__main__":raise SystemExit(main())
