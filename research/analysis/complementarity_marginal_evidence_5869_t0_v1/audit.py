import itertools,json,math,sys
EPS=1e-9
def close(a,b):return abs(float(a)-float(b))<=EPS
def probability(ws):return sum(float(w["weight"]) for w in ws)
def action_loss(c,ws,action):
 z=probability(ws)
 return sum(float(w["weight"])/z*float(c["loss"][action][str(w["target"]).lower()]) for w in ws)
def best_terminal(c,ws):
 if not c["mandatory_gate_passed"]:return "abstain",action_loss(c,ws,"abstain")
 labels={w["target"] for w in ws}
 allowed=["commit","decline","abstain"]
 # Commit is only a recommendation in this no-effect simulator; the explicit mandatory gate remains absolute.
 values=[(action_loss(c,ws,a),a) for a in allowed]
 loss,act=min(values)
 return act,loss
def legal(c,used):
 byid={x["id"]:x for x in c["checks"]}
 xs=[byid[x] for x in used]
 return c["mandatory_gate_passed"] and len({x["source_id"] for x in xs})==len(xs) and len({x["epoch"] for x in xs})<=1 and sum(x["cost"] for x in xs)<=c["budget"]+EPS and sum(x["latency_ms"] for x in xs)<=c["deadline_ms"]
def score(c,ws,plan,used=()):
 if plan=={"stop":True}:
  act,loss=best_terminal(c,ws)
  return {"cost":0.0,"loss":loss,"total":loss,"act":act,"queried":[],"false_commit_mass":probability([w for w in ws if w["target"] is False]) if act=="commit" else 0.0}
 if set(plan)!={"test","branches"}:raise ValueError("tree schema")
 i=plan["test"]
 if i in used or not legal(c,tuple(used)+(i,)):raise ValueError("query violates source/epoch/budget/deadline/gate")
 ck=next((x for x in c["checks"] if x["id"]==i),None)
 if ck is None:raise ValueError("unknown test")
 groups={}
 for w in ws:groups.setdefault(str(w["obs"][i]),[]).append(w)
 if set(plan["branches"])!=set(groups):raise ValueError("branch outcomes mismatch")
 z=probability(ws);cost=float(ck["cost"]);loss=0.;false=0.; queried={i}
 for v,g in groups.items():
  q=probability(g)/z;s=score(c,g,plan["branches"][v],tuple(used)+(i,))
  cost+=q*s["cost"];loss+=q*s["loss"];false+=q*s["false_commit_mass"];queried|=set(s["queried"])
 return {"cost":cost,"loss":loss,"total":cost+loss,"act":"policy","queried":sorted(queried),"false_commit_mass":false}
def make_sequence(c,ids,ws=None):
 ws=c["worlds"] if ws is None else ws
 if not ids:return {"stop":True}
 i=ids[0];groups={}
 for w in ws:groups.setdefault(str(w["obs"][i]),[]).append(w)
 return {"test":i,"branches":{v:make_sequence(c,ids[1:],g) for v,g in groups.items()}}
def enumerate_trees(c,ws,left,used,depth):
 yield {"stop":True}
 if depth<=0:return
 for ck in left:
  i=ck["id"]
  if not legal(c,tuple(used)+(i,)):continue
  groups={}
  for w in ws:groups.setdefault(str(w["obs"][i]),[]).append(w)
  children=[list(enumerate_trees(c,g,[x for x in left if x["id"]!=i],tuple(used)+(i,),depth-1)) for g in groups.values()]
  for combo in itertools.product(*children):
   yield {"test":i,"branches":dict(zip(groups.keys(),combo))}
def entropy(p):return -sum(q*math.log(q,2) for q in p if q>0)
def independent_information(c,ids):
 ws=c["worlds"];z=probability(ws);p=sum(w["weight"] for w in ws if w["target"])/z
 before=entropy([p,1-p]);groups={}
 for w in ws:groups.setdefault(tuple(w["obs"][i] for i in ids),[]).append(w)
 after=0.
 for g in groups.values():
  m=probability(g)/z;pt=sum(w["weight"] for w in g if w["target"])/probability(g)
  after+=m*entropy([pt,1-pt])
 return before-after
def path_ids(plan):
 if plan=={"stop":True}:return []
 i=plan["test"]
 child=next(iter(plan["branches"].values()))
 return [i]+path_ids(child)
def plan_tests_same_path(plan):
 if plan=={"stop":True}:return True
 children=list(plan["branches"].values())
 paths=[path_ids(x) for x in children]
 return all(x==paths[0] for x in paths) and all(plan_tests_same_path(x) for x in children)
def audit(f,raw):
 errs=[]
 if raw.get("allocation_id")!=f.get("allocation_id"):errs.append("allocation mismatch")
 cs=f["cases"];rs=raw.get("cases",[])
 if [x["id"] for x in cs]!=[x.get("case_id") for x in rs]:errs.append("case inventory mismatch")
 details={}
 for c,r in zip(cs,rs):
  if set(r.get("strategies",{}))!={"fixed","myopic","bellman2","pair_gate"}:errs.append(c["id"]+": strategy inventory")
  details[c["id"]]={}
  for name,row in r.get("strategies",{}).items():
   try:e=score(c,c["worlds"],row["plan"])
   except Exception as ex:errs.append(c["id"]+"/"+name+": "+str(ex));continue
   claim=row.get("claim",{})
   for key,k in [("query_cost","cost"),("decision_loss","loss"),("total_loss","total")]:
    if not close(claim.get(key,float("nan")),e[k]):errs.append(c["id"]+"/"+name+": "+key+" claim mismatch")
   if e["act"]!="policy" and claim.get("decision")!=e["act"]:errs.append(c["id"]+"/"+name+": terminal decision mismatch")
   if e["act"]=="policy" and claim.get("decision")!="policy":errs.append(c["id"]+"/"+name+": policy decision tag mismatch")
   details[c["id"]][name]=e
  for ck in c["checks"]:
   got=r.get("information_bits",{}).get(ck["id"],float("nan"));want=independent_information(c,[ck["id"]])
   if not close(got,want):errs.append(c["id"]+"/"+ck["id"]+": information mismatch")
  # Exact exhaustive two-query oracle, independent of candidate recursion.
  scored=[score(c,c["worlds"],p)["total"] for p in enumerate_trees(c,c["worlds"],c["checks"],(),2)]
  optimum=min(scored)
  if not close(details[c["id"]].get("bellman2",{}).get("total",float("nan")),optimum):errs.append(c["id"]+": bellman2 differs from exhaustive oracle")
  # Fixed and myopic policies are intentionally unconditional sequences.
  allids=[x["id"] for x in c["checks"]]
  fp=r["strategies"]["fixed"]["plan"]
  if feasible_all(c,allids):
   if path_ids(fp)!=allids or not plan_tests_same_path(fp):errs.append(c["id"]+": fixed checklist mismatch")
  elif fp!={"stop":True}:errs.append(c["id"]+": fixed checklist bypassed feasibility")
  mp=r["strategies"]["myopic"]["plan"]
  if not plan_tests_same_path(mp):errs.append(c["id"]+": myopic unexpectedly branches")
  chosen=path_ids(mp);expected=[]
  for _ in range(2):
   base=score(c,c["worlds"],make_sequence(c,expected))["loss"];opts=[]
   for ck in c["checks"]:
    i=ck["id"]
    if i in expected or not legal(c,tuple(expected)+(i,)):continue
    alt=score(c,c["worlds"],make_sequence(c,expected+[i]))["loss"]
    net=base-alt-ck["cost"]
    if net>EPS:opts.append((net,i))
   if not opts:break
   opts.sort(key=lambda x:(-x[0],x[1]));expected.append(opts[0][1])
  if chosen!=expected:errs.append(c["id"]+": myopic marginal choice mismatch")
  # Pair gate requires positive excess joint decision value over the best singleton and positive net benefit.
  base=score(c,c["worlds"],{"stop":True})["loss"];pairs=[]
  for ix,x in enumerate(c["checks"]):
   for y in c["checks"][ix+1:]:
    ids=[x["id"],y["id"]]
    if not legal(c,ids):continue
    joint=base-score(c,c["worlds"],make_sequence(c,ids))["loss"]
    single=max(base-score(c,c["worlds"],make_sequence(c,[i]))["loss"] for i in ids)
    interaction=joint-single;net=interaction-x["cost"]-y["cost"]
    if interaction>EPS and net>EPS:pairs.append((net,ids))
  pairs.sort(key=lambda x:(-x[0],x[1]));expected_pair=make_sequence(c,pairs[0][1]) if pairs else {"stop":True}
  if r["strategies"]["pair_gate"]["plan"]!=expected_pair:errs.append(c["id"]+": pair gate choice mismatch")
  # A failed mandatory gate must block all evidence acquisition and all commit recommendations.
  if not c["mandatory_gate_passed"]:
   if any(details[c["id"]][n]["queried"] for n in details[c["id"]]):errs.append(c["id"]+": mandatory gate bypass")
   if any(details[c["id"]][n]["false_commit_mass"] for n in details[c["id"]]):errs.append(c["id"]+": forbidden recommendation at failed gate")
 # Prespecified sentinel outcomes.
 xor=details.get("xor-complementary",{})
 red=details.get("redundant-duplicate",{})
 dim=details.get("diminishing-returns",{})
 bit=details.get("one-bit-low-decision-value",{})
 if xor.get("myopic",{}).get("queried")!=[] or xor.get("bellman2",{}).get("total")>=xor.get("myopic",{}).get("total",0):errs.append("XOR complementarity not detected")
 if red.get("pair_gate",{}).get("queried")!=[]:errs.append("redundant pair acquired")
 if dim.get("myopic",{}).get("queried")!=["a"]:errs.append("diminishing-return singleton mismatch")
 if any(details.get(x,{}).get("pair_gate",{}).get("queried") for x in ["pair-too-costly","pair-too-late","epoch-mismatch","shared-source","mandatory-gate-failed","one-bit-low-decision-value"]):errs.append("pair gate accepted blocked/nonvaluable control")
 if not close(bit.get("pair_gate",{}).get("total",float("nan")),bit.get("myopic",{}).get("total",float("nan"))):errs.append("one-bit low-value decision changed")
 return {"status":"PASS_METHOD_SCOPED" if not errs else "FAIL_AUDIT","errors":errs,"case_count":len(cs),"strategy_count":len(cs)*4,"exhaustive_tree_checks":len(cs),"details":details}
def feasible_all(c,ids):return legal(c,ids)
def main():
 x=json.load(sys.stdin);r=audit(x["fixture"],x["candidate"]);print(json.dumps(r,sort_keys=True,separators=(",",":")));sys.exit(0 if r["status"]=="PASS_METHOD_SCOPED" else 1)
if __name__=="__main__":main()
