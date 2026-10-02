import itertools, json, math, sys, hashlib
def rnd(x):
    return None if x is None else round(float(x), 12)
def quantile(items, q):
    ordered=sorted(items, key=lambda z:z[0])
    total=math.fsum(w for _,w in ordered)
    cut=q*total
    acc=0.0
    for x,w in ordered:
        acc+=w
        if acc+1e-15>=cut: return rnd(x)
    return rnd(ordered[-1][0])
def summary(vals, truth, conditional):
    mass=math.fsum(w for v,w in vals if v is not None)
    xs=[(v,w) for v,w in vals if v is not None]
    if not xs: return {"defined_mass":rnd(mass),"undefined_mass":rnd(1-mass)}
    norm=[(v,w/mass) for v,w in xs]
    mean=math.fsum(v*w for v,w in norm)
    variance=math.fsum(w*(v-mean)**2 for v,w in norm)
    mse=math.fsum(w*(v-truth)**2 for v,w in norm)
    return {"defined_mass":rnd(mass),"undefined_mass":rnd(1-mass),
      "mean":rnd(mean),"bias":rnd(mean-truth),"variance":rnd(variance),"mse":rnd(mse),
      "q025":quantile(norm,.025),"median":quantile(norm,.5),"q975":quantile(norm,.975),
      "min":rnd(min(v for v,_ in norm)),"max":rnd(max(v for v,_ in norm))}
def main():
    f=json.load(sys.stdin); rows=f["population"]; n=len(rows); methods=["selected_only","ht","dr_truep_badq","dr_badp_trueq","dr_both_wrong"]
    draws=[]
    for mask in range(1<<n):
        chosen=["A" if (mask>>(n-1-i))&1 else "B" for i in range(n)]
        prob=math.prod(rows[i]["p"][chosen[i]] for i in range(n))
        ent={"mask":format(mask,f"0{n}b"),"probability":round(prob,17),"selected":chosen,"estimators":{},"ess":{}}
        for v in ("A","B"):
            ix=[i for i,x in enumerate(chosen) if x==v]; ys=[rows[i]["y"][v] for i in ix]
            ent["estimators"][v]={}
            ent["estimators"][v]["selected_only"]=rnd(sum(ys)/len(ys)) if ix else None
            ent["estimators"][v]["ht"]=rnd(math.fsum(rows[i]["y"][v]/rows[i]["p"][v] for i in ix)/n)
            ent["estimators"][v]["dr_truep_badq"]=rnd(math.fsum(.25+(rows[i]["y"][v]-.25)/rows[i]["p"][v] if i in ix else .25 for i in range(n))/n)
            ent["estimators"][v]["dr_badp_trueq"]=rnd(math.fsum(rows[i]["y"][v]+(rows[i]["y"][v]-rows[i]["y"][v])/.5 if i in ix else rows[i]["y"][v] for i in range(n))/n)
            ent["estimators"][v]["dr_both_wrong"]=rnd(math.fsum(.25+(rows[i]["y"][v]-.25)/.5 if i in ix else .25 for i in range(n))/n)
            ww=[1/rows[i]["p"][v] for i in ix]
            ent["ess"][v]=rnd(math.fsum(ww)**2/math.fsum(w*w for w in ww)) if ww else 0.0
        draws.append(ent)
    truth={v:math.fsum(r["y"][v] for r in rows)/n for v in ("A","B")}
    summaries={}
    for v in ("A","B"):
        summaries[v]={}
        for m in methods:
            summaries[v][m]=summary([(d["estimators"][v][m],d["probability"]) for d in draws],truth[v],m=="selected_only")
        summaries[v]["ess"]={"mean":rnd(math.fsum(d["ess"][v]*d["probability"] for d in draws)),
           "min_positive":min(d["ess"][v] for d in draws if d["ess"][v]>0)}
    cal={}
    for fam in sorted(set(r["family"] for r in rows)):
      for diff in ("easy","hard"):
        sub=[i for i,r in enumerate(rows) if r["family"]==fam and r["difficulty"]==diff]
        empirical=math.fsum(d["probability"]*sum(1 for i in sub if d["selected"][i]=="A")/len(sub) for d in draws)
        target=math.fsum(rows[i]["p"]["A"] for i in sub)/len(sub)
        cal[f"{fam}/{diff}"]={"expected_A":rnd(empirical),"logged_A":rnd(target),"abs_error":rnd(abs(empirical-target))}
    zs=[]
    for r in rows:
      q=dict(r); q["p"]=dict(r["p"])
      if r["difficulty"]=="hard": q["p"]={"A":1.0,"B":0.0}
      zs.append(q)
    feasible=[]
    for bits in itertools.product(("A","B"),repeat=n):
      if any(zs[i]["p"][bits[i]]==0 for i in range(n)): continue
      feasible.append((bits,math.prod(zs[i]["p"][bits[i]] for i in range(n))))
    worlds=[]
    for alternate in (False,True):
      logs=[]
      for bits,prob in feasible:
        observed=[]
        for i,v in enumerate(bits):
          y=zs[i]["y"][v]
          if alternate and v=="B" and zs[i]["difficulty"]=="hard": y=0
          observed.append([zs[i]["id"],v,y])
        logs.append({"probability":round(prob,17),"observed":observed})
      worlds.append(logs)
    canonical=lambda x: json.dumps(x,sort_keys=True,separators=(",",":"))
    zobj={"status_B":"NONIDENTIFIABLE_FROM_LOGS","feasible_draws":len(feasible),
       "log_worlds_identical":canonical(worlds[0])==canonical(worlds[1]),
       "true_B_mean_world1":rnd(math.fsum(r["y"]["B"] for r in zs)/n),
       "true_B_mean_world2":rnd(math.fsum((0 if r["difficulty"]=="hard" else r["y"]["B"]) for r in zs)/n),
       "world1_logs_sha256":hashlib.sha256(canonical(worlds[0]).encode()).hexdigest(),
       "world2_logs_sha256":hashlib.sha256(canonical(worlds[1]).encode()).hexdigest()}
    out={"schema":"verifier-selection-5917-candidate-v1","fixture_sha256":hashlib.sha256(canonical(f).encode()).hexdigest(),
      "draw_count":len(draws),"probability_mass":rnd(math.fsum(d["probability"] for d in draws)),
      "true_means":{k:rnd(v) for k,v in truth.items()},"summaries":summaries,
      "calibration":cal,"max_inverse_weight":10.0,"zero_support":zobj,"draws":draws}
    print(canonical(out))
if __name__=="__main__": main()
