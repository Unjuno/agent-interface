import json,sys
fixture=json.load(open(sys.argv[1],encoding="utf-8"))
raw=json.load(open(sys.argv[2],encoding="utf-8"))
errors=[]
expected={}
H=fixture["horizon"]
for s in fixture["rows"]:
 for p in ("fixed","triggered","sample_hold","yield"):
  x=s["initial_agent"]; v=s["initial_velocity"]; lt=0; lx=s["target"][0]; pr=0.0
  caps=[0] if p!="yield" else []; acts=[]; release=None; checks=0; chunks=1 if p!="yield" else 0; pr=0.0
  if p=="yield": release="voluntary_yield"
  else:
   for t in range(H):
    if not (s["present"][t] and s["lease"][t] and s["focus"][t] and s["bound"][t]):
     release="target_lost" if not s["present"][t] else "lease_invalid" if not s["lease"][t] else "focus_invalid" if not s["focus"][t] else "target_binding_unknown"
     break
    obs=(t==0 or p=="fixed" or (p=="sample_hold" and t%fixture["capture_period"]==0))
    residual=0.0
    if p=="triggered":
     checks+=1
     prediction=lx+v*(t-lt); residual=s["fast_position"][t]-prediction
     if t>0 and abs(residual)>fixture["residual_threshold"]:
      obs=True; v=max(-fixture["max_speed"],min(fixture["max_speed"],v+residual-pr))
    if obs and t>0:
     caps.append(t); chunks+=1
     if p in ("fixed","sample_hold"):
      v=max(-fixture["max_speed"],min(fixture["max_speed"],(s["target"][t]-lx)/(t-lt)))
     lt=t; lx=s["target"][t]
    pr=0.0 if obs else residual
    v=max(-fixture["max_speed"],min(fixture["max_speed"],v))
    x+=v; acts.append({"tick":t,"input":v})
   if release is None: release="horizon"
  et=len(acts); tx=s["target"][et-1] if et else s["target"][0]; er=abs(x-tx)
  expected[(s["id"],p)]={"scenario":s["id"],"policy":p,"capture_ticks":caps,"residual_checks":checks,"chunks":chunks,"actions":acts,"release":release,"final_agent":x,"final_target":tx,"final_error":er,"effect":bool(release=="horizon" and et==H and er<=0.5),"safe":all(s["present"][a["tick"]] and s["lease"][a["tick"]] and s["focus"][a["tick"]] and s["bound"][a["tick"]] for a in acts)}
got=raw.get("rows",[])
if len(got)!=len(expected): errors.append("row_count")
seen=set()
for r in got:
 k=(r.get("scenario"),r.get("policy"))
 if k in seen: errors.append("duplicate:"+str(k)); continue
 seen.add(k)
 if k not in expected: errors.append("unknown:"+str(k)); continue
 if r!=expected[k]: errors.append("reconstruction:"+str(k))
if len(seen)!=len(expected): errors.append("missing_rows")
for sid in ("r03","r04","r05","r06"):
 for p in ("fixed","triggered","sample_hold"):
  r=expected[(sid,p)]
  s=next(x for x in fixture["rows"] if x["id"]==sid)
  if r["release"]=="horizon" or any(not (s["present"][a["tick"]] and s["lease"][a["tick"]] and s["focus"][a["tick"]] and s["bound"][a["tick"]]) for a in r["actions"]): errors.append("unsafe_release:"+sid+":"+p)
eligible=("r01","r02","r07","r08")
for sid in eligible:
 a=expected[(sid,"fixed")]; b=expected[(sid,"triggered")]
 if b["effect"]!=a["effect"]: errors.append("effect_regression:"+sid)
if len(expected)>0 and len(expected[("r01","triggered")]["capture_ticks"])>=len(expected[("r01","fixed")]["capture_ticks"]): errors.append("no_stable_capture_saving")
if not expected[("r01","triggered")]["effect"]: errors.append("perfect_predictor_control")
if expected[("r02","triggered")]["release"]!="horizon" or not expected[("r02","triggered")]["effect"]: errors.append("stale_predictor_control")
print(json.dumps({"verdict":"PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT","rows":len(got),"errors":errors},sort_keys=True))
sys.exit(0 if not errors else 1)
