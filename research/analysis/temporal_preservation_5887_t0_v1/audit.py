import json,sys,itertools
raw=json.load(sys.stdin)
assert raw["schema"]=="5887-temporal-projection-raw-v1"
cs={c["id"]:c for c in raw["cases"]}
assert len(cs)==7
def events(rs): return [e for r in rs for e in r["events"]]
def prop(cid,rs):
 if cid=="benign_stutter": return all(r["focus"] for r in rs)
 if cid=="transient_warning":
  es=events(rs)
  return "warning" in es and "done" in es and es.index("warning")<es.index("done")
 if cid=="focus_loss_recovery": return "focus_lost" in events(rs)
 if cid=="pixel_equal_generation_switch": return any(a["generation"]!=b["generation"] for a,b in zip(rs,rs[1:]))
 if cid=="critical_edge_order": return events(rs)
 raise AssertionError(cid)
def assess(c,mode):
 rs=c["rows"]; cid=c["id"]
 if cid=="missing_timestamp" and any("t_ms" not in r for r in rs): return "UNKNOWN"
 if cid=="unobserved_interval" and any(not r.get("coverage",False) for r in rs): return "UNKNOWN"
 if mode=="reordered":
  return "PRESERVED" if c["reordered_events"]==prop(cid,rs) else "NOT_PRESERVED"
 proj=[rs[i] for i in c["arms"][mode]]
 return "PRESERVED" if prop(cid,rs)==prop(cid,proj) else "NOT_PRESERVED"
expected={
 "benign_stutter":{"identity":"PRESERVED","exact_full":"PRESERVED"},
 "transient_warning":{"identity":"PRESERVED","latest":"NOT_PRESERVED"},
 "focus_loss_recovery":{"identity":"PRESERVED","latest":"NOT_PRESERVED"},
 "pixel_equal_generation_switch":{"identity":"PRESERVED","pixel_only":"NOT_PRESERVED"},
 "critical_edge_order":{"identity":"PRESERVED","reordered":"NOT_PRESERVED"},
 "missing_timestamp":{"identity":"UNKNOWN"},
 "unobserved_interval":{"identity":"UNKNOWN"}}
checks=[]
for cid,modes in expected.items():
 c=cs[cid]
 for mode,want in modes.items():
  got=assess(c,mode); assert got==want,(cid,mode,want,got)
  witness=None
  if got=="NOT_PRESERVED" and mode!="reordered":
   src=c["rows"]; kept=set(c["arms"][mode])
   dropped=[i for i in range(len(src)) if i not in kept]
   singles=[]
   for i in dropped:
    reduced=[r for j,r in enumerate(src) if j!=i]
    if prop(cid,src)!=prop(cid,reduced): singles.append(i)
   assert singles,(cid,mode,"no single-deletion witness")
   witness={"deleted_source_indices":singles,"source_value":prop(cid,src),"reduced_value":prop(cid,[r for i,r in enumerate(src) if i not in singles])}
  if mode=="reordered" and got=="NOT_PRESERVED":
   assert len(c["reordered_events"])==len(prop(cid,c["rows"]))
   witness={"source_event_order":prop(cid,c["rows"]),"projected_event_order":c["reordered_events"]}
  checks.append({"case":cid,"arm":mode,"verdict":got,"witness":witness})
assert len(checks)==11
assert cs["pixel_equal_generation_switch"]["rows"][0]["pixels"]==cs["pixel_equal_generation_switch"]["rows"][1]["pixels"]
assert cs["pixel_equal_generation_switch"]["rows"][0]["authority"]!=cs["pixel_equal_generation_switch"]["rows"][1]["authority"]
print(json.dumps({"schema":"5887-temporal-independent-audit-v1","status":"PASS_METHOD_SCOPED","checks":checks,"count":len(checks),"limits":["finite synthetic traces","no GUI/capture completeness claim","no runtime authority"]},sort_keys=True,separators=(",",":")))
