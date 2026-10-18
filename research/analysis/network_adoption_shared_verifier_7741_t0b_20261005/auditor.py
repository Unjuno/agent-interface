"""Independent raw-only replay for Issue #7741 T0b; imports no candidate code."""
import hashlib, json, math, sys

N,TICKS,SERVICE=24,160,3

def u(*x):
    return int.from_bytes(hashlib.sha256(":".join(map(str,x)).encode()).digest()[:8],"big")/2**64

def adjacent(top,i):
    return ((i-1)%N,(i+1)%N) if top=="ring" else ((1,) if i==0 else (0,))

def main(path):
    raw=json.load(open(path,encoding="utf-8")); grouped={}; errors=[]
    for e in raw["rows"]:
        k=(e["topology"],e["seed"],e["imitation"],e["mode"])
        grouped.setdefault(k,[]).append({a:b for a,b in e.items() if a not in ("topology","seed","imitation","mode")})
    sums={}
    for key,events in grouped.items():
        top,seed,imi,mode=key
        ad=[e for e in events if e["type"]=="adoption"]
        op=[e for e in events if e["type"]=="opportunity"]
        ad_by={(e["tick"],e["principal"]):e for e in ad}
        op_by={(e["tick"],e["principal"]):e for e in op}
        ar={e["id"]:e for e in events if e["type"]=="arrival"}
        st={e["id"]:e for e in events if e["type"]=="service_start"}
        co={e["id"]:e for e in events if e["type"]=="completion"}
        un={e["id"]:e for e in events if e["type"]=="unfinished"}
        if len(op)!=TICKS*N or len(ad)!=TICKS*N: errors.append(f"{key}: row_denominator")
        adopters=[False]*N; adopters[0]=True; completed_feedback=set()
        for tick in range(TICKS):
            for i in range(N):
                e=ad_by.get((tick,i))
                if e is None: errors.append(f"{key}: missing_adoption:{tick}:{i}"); continue
                peers=adjacent(top,i); verified=sum((tick-1,j) in completed_feedback for j in peers)
                if e["before"]!=adopters[i] or e["verified_peers"]!=verified or e["peer_count"]!=len(peers):
                    errors.append(f"{key}: adoption_context:{tick}:{i}")
                if abs(e["innovation_draw"]-u("innovation",top,seed,imi,tick,i))>0 or abs(e["imitation_draw"]-u("imitation",top,seed,imi,tick,i))>0:
                    errors.append(f"{key}: adoption_draw:{tick}:{i}")
                if not adopters[i] and "frozen" not in mode and "no_imitation" not in mode:
                    if mode.startswith("reduced_exogenous"):
                        adopters[i]=e["innovation_draw"] < min(1,0.012+imi*0.5)
                    else:
                        adopters[i]=(e["innovation_draw"]<0.012 or e["imitation_draw"]<imi*verified/len(peers))
                if e["after"]!=adopters[i]: errors.append(f"{key}: adoption_transition:{tick}:{i}")
            for i in range(N):
                e=op_by.get((tick,i))
                p=0.12 if mode.startswith("baseline") else 0.22
                if e is None or not e["offered"] or e["adopted"]!=adopters[i] or e["route_draw"]!=u("route",top,seed,tick,i) or e["start_draw"]!=u("start",top,seed,tick,i):
                    errors.append(f"{key}: opportunity_integrity:{tick}:{i}"); continue
                should=adopters[i] and e["start_draw"]<p
                matching=[x for x in ar.values() if x["arrival"]==tick and x["principal"]==i]
                if len(matching)!=int(should): errors.append(f"{key}: start_decision:{tick}:{i}")
            # Only completions after this tick's adoption phase inform the next tick.
            completed_feedback.update((tick,j["principal"]) for jid,j in ar.items()
                                      if jid in co and co[jid]["tick"]==tick)
        if set(ar)!=set(st)|set(un) or set(st)!=set(co)|{j for j,x in un.items() if x["state"]=="in_service"}:
            errors.append(f"{key}: lifecycle_partition")
        if set(ar)!=set(co)|set(un): errors.append(f"{key}: terminal_partition")
        for jid,job in ar.items():
            if jid in st and st[jid]["tick"]<job["arrival"]: errors.append(f"{key}: start_before_arrival:{jid}")
            if jid in co and (jid not in st or co[jid]["tick"]!=st[jid]["tick"]+SERVICE or co[jid]["latency"]!=co[jid]["tick"]-job["arrival"]):
                errors.append(f"{key}: service_or_latency:{jid}")
        for q in set(x["queue"] for x in st.values()):
            arrived=sorted((j["arrival"],jid) for jid,j in ar.items() if (q==0 and "per_principal" not in mode) or j["principal"]==q)
            started=sorted((x["tick"],jid) for jid,x in st.items() if x["queue"]==q)
            if [jid for _,jid in started] != [jid for _,jid in arrived if jid in st]: errors.append(f"{key}: fifo_order:{q}")
        waits=sorted(x["latency"] for x in co.values())
        p95=waits[math.ceil(.95*len(waits))-1] if waits else None
        sums[key]={"opportunities":len(op),"adopters_final":sum(e["after"] for e in ad if e["tick"]==TICKS-1),
                   "started":len(ar),"completed":len(co),"unfinished":len(un),"p95_latency":p95,
                   "interaction_cost":10 if mode.startswith("baseline") else 6}
    def val(top,seed,imi,mode): return sums[(top,seed,imi,mode)]["p95_latency"]
    primary=[]; controls={"no_imitation":0,"shared_24":0,"per_principal":0}
    for top in ("ring","star"):
        for seed in (11,29,47,83):
            for imi in (0.08,0.2):
                peer=val(top,seed,imi,"reduced_peer_shared_1")
                frozen=val(top,seed,imi,"reduced_frozen_shared_1")
                if peer is not None and frozen is not None and peer>frozen: primary.append((top,seed,imi))
                for label,pm,fm in (("no_imitation","reduced_no_imitation_shared_1","reduced_frozen_shared_1"),
                                    ("shared_24","reduced_peer_shared_24","reduced_frozen_shared_24"),
                                    ("per_principal","reduced_peer_per_principal","reduced_frozen_per_principal")):
                    x,y=val(top,seed,imi,pm),val(top,seed,imi,fm)
                    if x is not None and y is not None and x>y: controls[label]+=1
    cells={(t,m) for t in ("ring","star") for m in (.08,.2)}
    supported=all(sum(1 for t,s,m in primary if (t,m)==cell)>=3 for cell in cells)
    status="METHOD_PASS_SCOPED" if not errors and supported and not any(controls.values()) else ("NO_REVERSAL_IN_GRID" if not primary and not errors else "METHOD_FAIL_OR_INCONCLUSIVE")
    json.dump({"status":status,"errors":errors,"groups":len(sums),"primary_reversals":[list(x) for x in primary],"control_reversal_counts":controls,
               "summary":[{"key":list(k),**v} for k,v in sorted(sums.items())]},sys.stdout,sort_keys=True,separators=(",",":"))

if __name__=="__main__": main(sys.argv[1])
