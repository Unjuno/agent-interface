import json, random

def run(policy, seed, horizon=200, capacity=4):
    rng = random.Random(seed); q=[]; dropped_critical=0; ages=[]
    for t in range(horizon):
        # bursty observations; rare critical edges must survive
        for _ in range(rng.randrange(0, 5)):
            item={"gen":t,"critical":rng.random()<0.08}
            if len(q) >= capacity:
                if policy == "latest":
                    j=next((i for i,x in enumerate(q) if not x["critical"]), None)
                    if j is None: dropped_critical += int(not item["critical"])
                    else: q.pop(j); dropped_critical += 0
                elif policy == "critical":
                    j=next((i for i,x in enumerate(q) if not x["critical"]), None)
                    if j is None:
                        dropped_critical += int(item["critical"])
                    else: q.pop(j)
            if len(q)<capacity: q.append(item)
        if q:
            x=q.pop(0); ages.append(t-x["gen"])
    return {"mean_age":sum(ages)/len(ages) if ages else None,"p95_age":sorted(ages)[int(.95*len(ages))-1] if ages else None,"critical_drop_count":dropped_critical}

def main():
    out={p:{k:sum(run(p,s)[k] for s in range(1000))/1000 for k in ("mean_age","p95_age","critical_drop_count")} for p in ("latest","critical")}
    print(json.dumps({"experiment":"43-aoi-t0","trials":1000,"horizon":200,"capacity":4,"results":out,"scope":"toy queue; no planner/model, no semantic event oracle"},sort_keys=True,indent=2))
if __name__=='__main__': main()
