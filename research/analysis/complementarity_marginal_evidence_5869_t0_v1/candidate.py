import json, math, sys
def norm(ws):
 s=sum(w["weight"] for w in ws)
 return [(w,w["weight"]/s) for w in ws]
def terminal(c,ws):
 if not c["mandatory_gate_passed"]: return (sum(p*c["loss"]["abstain"][str(w["target"]).lower()] for w,p in norm(ws)),"abstain")
 acts=["commit","decline","abstain"]
 vals=[(sum(p*c["loss"][a][str(w["target"]).lower()] for w,p in norm(ws)),a) for a in acts]
 return min(vals)
def feasible(c,ids):
 cs={x["id"]:x for x in c["checks"]}; xs=[cs[i] for i in ids]
 return c["mandatory_gate_passed"] and len({x["source_id"] for x in xs})==len(xs) and len({x["epoch"] for x in xs})<=1 and sum(x["cost"] for x in xs)<=c["budget"]+1e-12 and sum(x["latency_ms"] for x in xs)<=c["deadline_ms"]
def risk(c,ws,ids):
 if not ids:return terminal(c,ws)[0]
 groups={}
 for w in ws:groups.setdefault(tuple(w["obs"][i] for i in ids),[]).append(w)
 mass=sum(w["weight"] for w in ws)
 return sum(sum(w["weight"] for w in g)/mass*terminal(c,g)[0] for g in groups.values())
def stop():return {"stop":True}
def seq(c,ids,ws=None):
 ws=c["worlds"] if ws is None else ws
 if not ids:return stop()
 i=ids[0];groups={}
 for w in ws:groups.setdefault(w["obs"][i],[]).append(w)
 return {"test":i,"branches":{str(v):seq(c,ids[1:],g) for v,g in groups.items()}}
def fixed(c):
 ids=[x["id"] for x in c["checks"]]
 return seq(c,ids) if feasible(c,ids) else stop()
def myopic(c):
 ids=[]
 for _ in range(2):
  now=risk(c,c["worlds"],ids); opts=[]
  for x in c["checks"]:
   i=x["id"]
   if i in ids or not feasible(c,ids+[i]):continue
   net=now-risk(c,c["worlds"],ids+[i])-x["cost"]
   if net>1e-12:opts.append((net,i))
  if not opts:break
  opts.sort(key=lambda z:(-z[0],z[1]));ids.append(opts[0][1])
 return seq(c,ids)
def bellman(c,ws=None,used=None,d=2):
 ws=c["worlds"] if ws is None else ws;used=[] if used is None else used
 base=terminal(c,ws)[0];best=(base,stop())
 if d==0 or not c["mandatory_gate_passed"]:return best
 for x in c["checks"]:
  i=x["id"]
  if i in used or not feasible(c,used+[i]):continue
  groups={}
  for w in ws:groups.setdefault(w["obs"][i],[]).append(w)
  mass=sum(w["weight"] for w in ws); branches={};value=x["cost"]
  for v,g in sorted(groups.items(),key=lambda z:str(z[0])):
   p=sum(w["weight"] for w in g)/mass;v2,sub=bellman(c,g,used+[i],d-1)
   value+=p*v2;branches[str(v)]=sub
  if value<best[0]-1e-12:best=(value,{"test":i,"branches":branches})
 return best
def pair(c):
 base=risk(c,c["worlds"],[]);best=(0.0,[])
 for ix,x in enumerate(c["checks"]):
  for y in c["checks"][ix+1:]:
   ids=[x["id"],y["id"]]
   if not feasible(c,ids):continue
   gain=base-risk(c,c["worlds"],ids)
   single=max(base-risk(c,c["worlds"],[i]) for i in ids)
   net=gain-single-sum(z["cost"] for z in [x,y])
   if gain-single>1e-12 and net>best[0]+1e-12:best=(net,ids)
 return seq(c,best[1])
def evalplan(c,ws,p,used=None):
 used=[] if used is None else used
 if p.get("stop") is True:
  l,a=terminal(c,ws);return {"query_cost":0.0,"decision_loss":l,"total_loss":l,"decision":a}
 i=p["test"]; assert i not in used and feasible(c,used+[i])
 x=next(z for z in c["checks"] if z["id"]==i);groups={}
 for w in ws:groups.setdefault(w["obs"][i],[]).append(w)
 mass=sum(w["weight"] for w in ws);qc=x["cost"];dl=0.0
 if "branches" in p:
  assert set(p["branches"])=={str(v) for v in groups}
  for v,g in groups.items():
   e=evalplan(c,g,p["branches"][str(v)],used+[i]);prob=sum(w["weight"] for w in g)/mass
   qc+=prob*e["query_cost"];dl+=prob*e["decision_loss"]
  queries=used+[i]
 else:
  e=evalplan(c,ws,p["next"],used+[i]);qc+=e["query_cost"];dl=e["decision_loss"];queries=e["queries"]
 return {"query_cost":qc,"decision_loss":dl,"total_loss":qc+dl,"decision":"policy"}
def ig(c,ids):
 def h(p):return -sum(x*math.log(x,2) for x in p if x>0)
 ws=c["worlds"];mass=sum(w["weight"] for w in ws);p=sum(w["weight"] for w in ws if w["target"])/mass
 prior=h([p,1-p]);groups={}
 for w in ws:groups.setdefault(tuple(w["obs"][i] for i in ids),[]).append(w)
 cond=0
 for g in groups.values():
  m=sum(w["weight"] for w in g)/mass;q=sum(w["weight"] for w in g if w["target"])/sum(w["weight"] for w in g)
  cond+=m*h([q,1-q])
 return prior-cond
def main():
 f=json.load(sys.stdin);out=[]
 for c in f["cases"]:
  _,bp=bellman(c);ps={"fixed":fixed(c),"myopic":myopic(c),"bellman2":bp,"pair_gate":pair(c)}
  out.append({"case_id":c["id"],"information_bits":{x["id"]:ig(c,[x["id"]]) for x in c["checks"]},
   "strategies":{k:{"plan":p,"claim":evalplan(c,c["worlds"],p)} for k,p in ps.items()}})
 print(json.dumps({"allocation_id":f["allocation_id"],"cases":out},sort_keys=True,separators=(",",":")))
if __name__=="__main__":main()
