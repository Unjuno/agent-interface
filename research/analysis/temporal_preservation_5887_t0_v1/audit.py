import json,sys,itertools
raw=json.load(sys.stdin)
assert raw["schema"]=="5887-temporal-projection-raw-v1"
cs={c["id"]:c for c in raw["cases"]}
assert len(cs)==7
def values(c,indices):
 return [c["rows"][i] for i in indices]
def events(rs): return [e for r in rs for e in r["events"]]
def assess(c,mode):
 rs=c["rows"]; proj=values(c,c["arms"][mode]); cid=c["id"]
 if cid=="missing_timestamp" and any("t_ms" not in r for r in rs): return "UNKNOWN"
 if cid=="unobserved_interval" and any(not r.get("coverage",False) for r in rs): return "UNKNOWN"
 if cid=="benign_stutter": return "PRESERVED" if all(r["focus"] for r in proj) else "NOT_PRESERVED"
 if cid=="transient_warning":
  src=events(rs); got=events(proj)
  ok=("warning" in got and "done" in got and got.index("warning")<got.index("done"))
  return "PRESERVED" if ok else "NOT_PRESERVED"
 if cid=="focus_loss_recovery":
  return "PRESERVED" if all(r["focus"] for r in proj) else "NOT_PRESERVED"
 if cid=="pixel_equal_generation_switch":
  changed=any(a["generation"]!=b["generation"] for a,b in zip(proj,proj[1:]))
  return "PRESERVED" if changed else "NOT_PRESERVED"
 if cid=="critical_edge_order":
  expected=events(rs); got=c["reordered_events"] if mode=="reordered" else events(proj)
  return "PRESERVED" if got==expected else "NOT_PRESERVED"
 raise AssertionError(cid)
expected={
 "benign_stutter":{"identity":"PRESERVED","exact_full":"PRESERVED"},
 "transient_warning":{"identity":"PRESERVED","latest":"NOT_PRESERVED"},
 "focus_loss_recovery":{"identity":"NOT_PRESERVED","latest":"PRESERVED"},
 "pixel_equal_generation_switch":{"identity":"PRESERVED","pixel_only":"NOT_PRESERVED"},
 "critical_edge_order":{"identity":"PRESERVED","reordered":"NOT_PRESERVED"},
 "missing_timestamp":{"identity":"UNKNOWN"},
 "unobserved_interval":{"identity":"UNKNOWN"}}
checks=[]
for cid,modes in expected.items():
 c=cs[cid]
 for mode,want in modes.items():
  got=assess(c,mode); assert got==want,(cid,mode,want,got)
  if got=="NOT_PRESERVED":
   src=c["rows"]; idx=c["arms"][mode]
   # Replayable deletion witness: identity source/property versus actual projection.
   assert assess(c,"identity")!=assess(c,mode),(cid,mode,"no witness")
   assert all(0<=i<len(src) for i in idx)
  checks.append({"case":cid,"arm":mode,"verdict":got})
assert len(checks)==11
assert all(not r.get("authority_created",False) for c in raw["cases"] for r in c["rows"])
print(json.dumps({"schema":"5887-temporal-independent-audit-v1","status":"PASS_METHOD_SCOPED","checks":checks,"count":len(checks),"limits":["finite synthetic traces","no GUI/capture completeness claim","no runtime authority"]},sort_keys=True,separators=(",",":")))
