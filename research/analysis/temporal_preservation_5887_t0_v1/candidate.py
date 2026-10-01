import json
CASES = [
 {"id":"benign_stutter","required":["target","session","generation","pixels","focus","authority"],"rows":[
  {"target":"w1","session":"s1","generation":1,"pixels":"p","focus":True,"authority":"a1","events":[],"t_ms":0,"coverage":True},
  {"target":"w1","session":"s1","generation":1,"pixels":"p","focus":True,"authority":"a1","events":[],"t_ms":1,"coverage":True},
  {"target":"w1","session":"s1","generation":1,"pixels":"p","focus":True,"authority":"a1","events":[],"t_ms":2,"coverage":True}]},
 {"id":"transient_warning","required":["target","session","generation","pixels","focus","authority"],"rows":[
  {"target":"w1","session":"s1","generation":1,"pixels":"p","focus":True,"authority":"a1","events":[],"t_ms":0,"coverage":True},
  {"target":"w1","session":"s1","generation":1,"pixels":"q","focus":True,"authority":"a1","events":["warning"],"t_ms":1,"coverage":True},
  {"target":"w1","session":"s1","generation":1,"pixels":"p","focus":True,"authority":"a1","events":["done"],"t_ms":2,"coverage":True}]},
 {"id":"focus_loss_recovery","required":["target","session","generation","pixels","focus","authority"],"rows":[
  {"target":"w1","session":"s1","generation":1,"pixels":"p","focus":True,"authority":"a1","events":[],"t_ms":0,"coverage":True},
  {"target":"w1","session":"s1","generation":1,"pixels":"q","focus":False,"authority":"a1","events":["focus_lost"],"t_ms":1,"coverage":True},
  {"target":"w1","session":"s1","generation":1,"pixels":"p","focus":True,"authority":"a1","events":["focus_restored"],"t_ms":2,"coverage":True}]},
 {"id":"pixel_equal_generation_switch","required":["target","session","generation","pixels","focus","authority"],"rows":[
  {"target":"w1","session":"s1","generation":1,"pixels":"same","focus":True,"authority":"a1","events":[],"t_ms":0,"coverage":True},
  {"target":"w1","session":"s1","generation":2,"pixels":"same","focus":True,"authority":"a2","events":["generation_changed"],"t_ms":1,"coverage":True}]},
 {"id":"critical_edge_order","required":["target","session","generation","pixels","focus","authority"],"rows":[
  {"target":"w1","session":"s1","generation":1,"pixels":"p","focus":True,"authority":"a1","events":["focus_lost"],"t_ms":0,"coverage":True},
  {"target":"w1","session":"s1","generation":1,"pixels":"q","focus":False,"authority":"a1","events":["lease_expired"],"t_ms":1,"coverage":True}]},
 {"id":"missing_timestamp","required":["target","session","generation","pixels","focus","authority"],"rows":[
  {"target":"w1","session":"s1","generation":1,"pixels":"p","focus":True,"authority":"a1","events":[],"coverage":True},
  {"target":"w1","session":"s1","generation":1,"pixels":"p","focus":True,"authority":"a1","events":[],"coverage":True}]},
 {"id":"unobserved_interval","required":["target","session","generation","pixels","focus","authority"],"rows":[
  {"target":"w1","session":"s1","generation":1,"pixels":"p","focus":True,"authority":"a1","events":[],"t_ms":0,"coverage":True},
  {"target":"w1","session":"s1","generation":1,"pixels":"p","focus":True,"authority":"a1","events":[],"t_ms":4,"coverage":False}]}
]
def project(rows, required, mode):
 if mode == "identity": return list(range(len(rows)))
 if mode == "exact_full":
  out=[]
  for i,r in enumerate(rows):
   if out:
    p=rows[out[-1]]
    complete=all(k in p and k in r for k in required)
    same=complete and all(p[k]==r[k] for k in required)
    if same and not p["events"] and not r["events"]: continue
   out.append(i)
  return out
 if mode == "latest": return [len(rows)-1]
 if mode == "pixel_only":
  out=[]
  for i,r in enumerate(rows):
   if out and rows[out[-1]]["pixels"]==r["pixels"]: continue
   out.append(i)
  return out
 if mode == "edge_retain": return [i for i,r in enumerate(rows) if r["events"]] + ([len(rows)-1] if len(rows)-1 not in [i for i,r in enumerate(rows) if r["events"]] else [])
 return []
out={"schema":"5887-temporal-projection-raw-v1","cases":[]}
for c in CASES:
 rows=c["rows"]
 arms={m:project(rows,c["required"],m) for m in ("identity","exact_full","latest","pixel_only","edge_retain")}
 out["cases"].append({"id":c["id"],"required":c["required"],"rows":rows,"arms":arms,
  "reordered_events":list(reversed([e for r in rows for e in r["events"]])) if c["id"]=="critical_edge_order" else None})
print(json.dumps(out,sort_keys=True,separators=(",",":")))
