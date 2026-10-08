import itertools,json,math,sys,copy
def r(x): return None if x is None else round(float(x),12)
def qtile(pairs,q):
    pairs=sorted(pairs,key=lambda a:a[0]); mass=math.fsum(w for _,w in pairs); target=q*mass; acc=0
    for x,w in pairs:
        acc+=w
        if acc+1e-15>=target:return r(x)
    return r(pairs[-1][0])
def oracle(f):
    rows=f["population"]; n=len(rows); raw=[]
    # Product enumeration (not candidate's integer-mask traversal).
    for bits in itertools.product((0,1),repeat=n):
        picked=tuple("A" if b else "B" for b in bits)
        p=math.prod(rows[i]["p"][picked[i]] for i in range(n))
        stats={}; ess={}
        for v in ("A","B"):
            chosen=[i for i in range(n) if picked[i]==v]
            count=len(chosen); y=[rows[i]["y"][v] for i in chosen]
            psel=(sum(y)/count) if count else None
            ht=math.fsum((rows[i]["y"][v]/rows[i]["p"][v]) for i in chosen)/n
            d1=math.fsum(.25+((rows[i]["y"][v]-.25)/rows[i]["p"][v]) if i in chosen else .25 for i in range(n))/n
            d2=math.fsum(rows[i]["y"][v] for i in range(n))/n
            d3=math.fsum(.25+((rows[i]["y"][v]-.25)/.5) if i in chosen else .25 for i in range(n))/n
            w=[1/rows[i]["p"][v] for i in chosen]
            stats[v]={"selected_only":r(psel),"ht":r(ht),"dr_truep_badq":r(d1),"dr_badp_trueq":r(d2),"dr_both_wrong":r(d3)}
            ess[v]=r((math.fsum(w)**2/math.fsum(z*z for z in w)) if w else 0.0)
        raw.append({"mask":"".join(str(b) for b in bits),"probability":round(p,17),
          "selected":list(picked),"estimators":stats,"ess":ess})
    return raw
def moments(raw,truth):
    out={}
    for v in ("A","B"):
      out[v]={}
      for name in ("selected_only","ht","dr_truep_badq","dr_badp_trueq","dr_both_wrong"):
        mass=math.fsum(x["probability"] for x in raw if x["estimators"][v][name] is not None)
        vals=[(x["estimators"][v][name],x["probability"]/mass) for x in raw if x["estimators"][v][name] is not None]
        mean=math.fsum(a*w for a,w in vals); variance=math.fsum(w*(a-mean)**2 for a,w in vals)
        mse=math.fsum(w*(a-truth[v])**2 for a,w in vals)
        out[v][name]={"defined_mass":r(mass),"undefined_mass":r(1-mass),"mean":r(mean),"bias":r(mean-truth[v]),
          "variance":r(variance),"mse":r(mse),"q025":qtile(vals,.025),"median":qtile(vals,.5),"q975":qtile(vals,.975),
          "min":r(min(a for a,_ in vals)),"max":r(max(a for a,_ in vals))}
      out[v]["ess"]={"mean":r(math.fsum(x["ess"][v]*x["probability"] for x in raw)),
        "min_positive":min(x["ess"][v] for x in raw if x["ess"][v]>0)}
    return out
def zero_support(f):
    rows=f["population"]; n=len(rows); feasible=[]
    for bits in itertools.product((0,1),repeat=n):
        sel=tuple("A" if b else "B" for b in bits); p=1.0; ok=True; obs=[]
        for i,v in enumerate(sel):
            q=dict(rows[i]["p"])
            if rows[i]["difficulty"]=="hard": q={"A":1.0,"B":0.0}
            pv=q[v]
            if pv==0: ok=False; break
            p*=pv
            obs.append([rows[i]["id"],v,rows[i]["y"][v] if not(v=="B" and rows[i]["difficulty"]=="hard") else 1])
        if ok: feasible.append({"probability":round(p,17),"observed":obs})
    alt=[]
    for x in feasible:
        obs=copy.deepcopy(x["observed"])
        # The only changed potential outcomes are B on hard rows, which have zero inclusion.
        for entry in obs:
            if entry[1]=="B" and any(z["id"]==entry[0] and z["difficulty"]=="hard" for z in rows): entry[2]=0
        alt.append({"probability":x["probability"],"observed":obs})
    b1=math.fsum(z["y"]["B"] for z in rows)/n
    b2=math.fsum((0 if z["difficulty"]=="hard" else z["y"]["B"]) for z in rows)/n
    # Deep equality of all feasible observed rows across the two worlds.
    equivalent=feasible==alt
    return {"status_B":"NONIDENTIFIABLE_FROM_LOGS","feasible_draws":len(feasible),"log_worlds_identical":equivalent,
      "true_B_mean_world1":r(b1),"true_B_mean_world2":r(b2)}
def calibrate(f,raw):
    rows=f["population"]; out={}
    for family in sorted(set(x["family"] for x in rows)):
      for difficulty in ("easy","hard"):
        ix=[i for i,x in enumerate(rows) if x["family"]==family and x["difficulty"]==difficulty]
        actual=math.fsum(z["probability"]*sum(1 for i in ix if z["selected"][i]=="A")/len(ix) for z in raw)
        declared=math.fsum(rows[i]["p"]["A"] for i in ix)/len(ix)
        out[f"{family}/{difficulty}"]={"expected_A":r(actual),"logged_A":r(declared),"abs_error":r(abs(actual-declared))}
    return out
def verify(f,c):
    expected=oracle(f); truth={v:math.fsum(z["y"][v] for z in f["population"])/len(f["population"]) for v in ("A","B")}
    expected_summ=moments(expected,truth)
    fixture_hash=__import__("hashlib").sha256(json.dumps(f,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    expected_max=max(1.0/x["p"][v] for x in f["population"] for v in ("A","B"))
    if c.get("schema")!="verifier-selection-5917-candidate-v1": return False
    if c.get("draws")!=expected: return False
    if c.get("draw_count")!=len(expected): return False
    if c.get("probability_mass")!=r(math.fsum(x["probability"] for x in expected)): return False
    if c.get("summaries")!=expected_summ: return False
    if c.get("calibration")!=calibrate(f,expected): return False
    if c.get("fixture_sha256")!=fixture_hash or c.get("max_inverse_weight")!=r(expected_max): return False
    if c.get("zero_support") is None: return False
    z=zero_support(f)
    for k,v in z.items():
        if c["zero_support"].get(k)!=v:return False
    return True
def main():
    bundle=json.load(sys.stdin); f=bundle["fixture"]; c=bundle["candidate"]
    raw=oracle(f); truth={v:math.fsum(z["y"][v] for z in f["population"])/len(f["population"]) for v in ("A","B")}
    checked=verify(f,c); summ=moments(raw,truth); z=zero_support(f); calibration=calibrate(f,raw)
    calibration_ok=max(x["abs_error"] for x in calibration.values())<1e-12
    mutants=[]
    m=copy.deepcopy(c); m["draws"][0]["probability"]=round(m["draws"][0]["probability"]+.01,17); mutants.append(m)
    m=copy.deepcopy(c); m["draws"].pop(); mutants.append(m)
    m=copy.deepcopy(c); m["zero_support"]["status_B"]="ESTIMATED"; mutants.append(m)
    rejected=[not verify(f,m) for m in mutants]
    cond=(len(raw)==256 and abs(math.fsum(x["probability"] for x in raw)-1)<1e-12 and
      all(abs(summ[v]["selected_only"]["bias"])>=.35 and abs(summ[v]["ht"]["bias"])<1e-12 and
      summ[v]["ht"]["mse"]<summ[v]["selected_only"]["mse"] and
      abs(summ[v]["dr_truep_badq"]["bias"])<1e-12 and abs(summ[v]["dr_badp_trueq"]["bias"])<1e-12 and
      abs(summ[v]["dr_both_wrong"]["bias"])>=.35 for v in ("A","B")) and
      z["status_B"]=="NONIDENTIFIABLE_FROM_LOGS" and z["log_worlds_identical"] and
      z["true_B_mean_world1"]==.5 and z["true_B_mean_world2"]==0.0 and calibration_ok and
      max(1.0/x["p"][v] for x in f["population"] for v in ("A","B"))==10.0)
    out={"status":"PASS_METHOD_SCOPED" if checked and cond and all(rejected) else "FAIL_OR_HOLD",
      "candidate_matches_independent_enumeration":checked,"draw_count":len(raw),
      "probability_mass":r(math.fsum(x["probability"] for x in raw)),
      "mutation_controls_rejected":rejected,"mutation_rejections":sum(rejected),
      "estimand_summaries":summ,"calibration":calibration,"zero_support":z,"predeclared_conditions":cond,"errors":[] if checked and cond and all(rejected) else ["one or more preregistered conditions failed"]}
    print(json.dumps(out,sort_keys=True,separators=(",",":")))
if __name__=="__main__": main()
