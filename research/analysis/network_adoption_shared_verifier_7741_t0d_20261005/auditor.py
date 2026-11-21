"""Independent raw event-log auditor for Issue #7741 T0d; no candidate import."""
import gzip,hashlib,json,math,sys

def draw(*parts):
    return int.from_bytes(hashlib.sha256(":".join(map(str,parts)).encode()).digest()[:8],"big")/2**64

def adjacent(top,p,n):
    if top=="ring": return ((p-1)%n,(p+1)%n)
    return tuple(range(1,n)) if p==0 else (0,)

def audit(raw,config):
    errors=[]; n=config["principals"]; ticks=config["ticks"]; svc=config["service_ticks"]
    if raw.get("schema")!="7741-t0d-raw-v1": errors.append("schema")
    if raw.get("config")!=config: errors.append("config_mismatch")
    expected_keys={(t,s,i,m) for t in config["topologies"] for s in config["seeds"]
                   for i in config["imitation_probabilities"] for m in config["modes"]}
    groups={}; summaries={}
    for g in raw.get("groups",[]):
        key=(g.get("topology"),g.get("seed"),g.get("imitation"),g.get("mode"))
        if key in groups: errors.append(f"duplicate_group:{key}")
        groups[key]=g
    if set(groups)!=expected_keys: errors.append("group_inventory")
    for key,g in groups.items():
        top,seed,imi,mode=key; events=g.get("events",[])
        bytype={name:[e for e in events if e.get("type")==name] for name in
                ("adoption","opportunity","arrival","service_start","completion","unfinished")}
        adop={(e["tick"],e["principal"]):e for e in bytype["adoption"]}
        opp={(e["tick"],e["principal"]):e for e in bytype["opportunity"]}
        if len(adop)!=ticks*n or len(opp)!=ticks*n: errors.append(f"denominator:{key}")
        arr={e["id"]:e for e in bytype["arrival"]}; starts={e["id"]:e for e in bytype["service_start"]}
        done={e["id"]:e for e in bytype["completion"]}; unfinished={e["id"]:e for e in bytype["unfinished"]}
        if len(arr)!=len(bytype["arrival"]) or len(starts)!=len(bytype["service_start"]) or len(done)!=len(bytype["completion"]) or len(unfinished)!=len(bytype["unfinished"]):
            errors.append(f"duplicate_task_event:{key}")
        adopters=[False]*n; adopters[0]=True
        # Compute due verified feedback from the event log, then replay adoption and every opportunity.
        completed_by_tick={}
        for e in bytype["completion"]: completed_by_tick.setdefault(e["tick"],[]).append(e["principal"])
        seen=set()
        routeprob=config["route_start_probability"]["baseline" if mode.startswith("baseline") else "reduced_cost"]
        for tick in range(ticks):
            seen.update(completed_by_tick.get(tick,[]))
            for p in range(n):
                e=adop.get((tick,p))
                if e is None: errors.append(f"missing_adoption:{key}:{tick}:{p}"); continue
                adj=adjacent(top,p,n); peer_count=sum(q in seen for q in adj)
                inn=draw("innovation",top,seed,imi,tick,p); pd=draw("peer",top,seed,imi,tick,p)
                ex=draw("exogenous",top,seed,imi,tick,p); before=adopters[p]; after=before; cause=None
                if not before:
                    if mode in ("reduced_peer_shared_1","reduced_peer_shared_24","reduced_peer_per_principal"):
                        if inn<config["innovation_probability"]: after=True; cause="innovation"
                        elif pd<imi*peer_count/len(adj): after=True; cause="peer_verified"
                    elif mode=="reduced_exogenous_shared_1" and ex<config["innovation_probability"]+imi*0.06:
                        after=True; cause="exogenous"
                if (e.get("before")!=before or e.get("after")!=after or e.get("cause")!=cause or
                    e.get("verified_peers")!=peer_count or e.get("peer_count")!=len(adj) or
                    e.get("innovation_draw")!=inn or e.get("peer_draw")!=pd or e.get("exogenous_draw")!=ex):
                    errors.append(f"adoption_replay:{key}:{tick}:{p}")
                adopters[p]=after
                o=opp.get((tick,p)); rd=draw("route_start",top,seed,tick,p)
                should=after and rd<routeprob
                if o is None or o.get("offered") is not True or o.get("adopted")!=after or o.get("start_draw")!=rd or o.get("start_probability")!=routeprob or o.get("started")!=should:
                    errors.append(f"opportunity_replay:{key}:{tick}:{p}")
        # Every offered start must create exactly one typed arrival and preserve work obligations.
        started={(tick,p) for (tick,p),o in opp.items() if o.get("started") is True}
        arr_pairs={(e["arrival"],e["principal"]) for e in arr.values()}
        if len(arr_pairs)!=len(arr) or arr_pairs!=started: errors.append(f"arrival_coverage:{key}")
        baseline=mode.startswith("baseline")
        cost=config["interaction_cost"]["baseline" if baseline else "reduced_cost"]
        partitioned=mode.endswith("per_principal")
        cap=n if "shared_24" in mode else 1
        # Independently compute FIFO service admission from release-ordered jobs.
        arrivals_by_queue={}
        for jid,j in arr.items():
            q=j["principal"] if partitioned else 0
            if j.get("id")!=jid or j.get("queue")!=q or j.get("cost")!=cost or j.get("arrival") not in range(ticks):
                errors.append(f"arrival_fields:{key}:{jid}")
            arrivals_by_queue.setdefault(q,[]).append(j)
        expected_starts={}
        for q,jobs in arrivals_by_queue.items():
            limit=1 if partitioned else cap; free=[0]*limit
            for j in sorted(jobs,key=lambda x:(x["arrival"],x["id"])):
                start=max(j["arrival"],min(free))
                server=min(s for s in range(limit) if free[s]<=start)
                if start<ticks:
                    expected_starts[j["id"]]={"tick":start,"queue":q,"server":server}
                    free[server]=start+svc
        if set(starts)!=set(expected_starts): errors.append(f"start_inventory:{key}")
        for jid,want in expected_starts.items():
            got=starts.get(jid)
            if got is None or any(got.get(k)!=v for k,v in want.items()): errors.append(f"service_admission:{key}:{jid}")
        expected_done={jid for jid,s in expected_starts.items() if s["tick"]+svc<ticks}
        expected_unfinished=set(arr)-expected_done
        if set(done)!=expected_done or set(unfinished)!=expected_unfinished: errors.append(f"terminal_inventory:{key}")
        for jid,s in expected_starts.items():
            j=arr[jid]
            if jid in done:
                d=done[jid]
                if d.get("tick")!=s["tick"]+svc or d.get("latency")!=d.get("tick")-j["arrival"] or d.get("queue")!=s["queue"] or d.get("principal")!=j["principal"]:
                    errors.append(f"completion_receipt:{key}:{jid}")
        for jid in expected_unfinished:
            u=unfinished.get(jid); j=arr[jid]
            state="in_service" if jid in expected_starts else "queued"
            expected={"state":state,"queue":j["principal"] if partitioned else 0,"principal":j["principal"],"arrival":j["arrival"]}
            if jid in expected_starts: expected.update({"server":expected_starts[jid]["server"],"finish":expected_starts[jid]["tick"]+svc})
            if u is None or any(u.get(k)!=v for k,v in expected.items()): errors.append(f"unfinished_receipt:{key}:{jid}")
        latencies=sorted(e["latency"] for e in done.values())
        p95=latencies[math.ceil(.95*len(latencies))-1] if latencies else None
        total_adopters=sum(adopters)
        summaries[key]={"opportunities":len(opp),"adopters_final":total_adopters,"arrivals":len(arr),
                        "verified_completions":len(done),"unfinished":len(unfinished),"p95_latency":p95,
                        "interaction_cost_per_started_task":cost}
    def value(t,s,i,m): return summaries[(t,s,i,m)]["p95_latency"]
    primary=[]; controls={"no_imitation_nonzero":0,"shared_24_nonzero":0}
    differences=[]
    for top in config["topologies"]:
        for seed in config["seeds"]:
            for imi in config["imitation_probabilities"]:
                peer=value(top,seed,imi,"reduced_peer_shared_1")
                frozen=value(top,seed,imi,"reduced_frozen_shared_1")
                local_peer=value(top,seed,imi,"reduced_peer_per_principal")
                local_frozen=value(top,seed,imi,"reduced_frozen_per_principal")
                shared_diff=None if peer is None or frozen is None else peer-frozen
                local_diff=None if local_peer is None or local_frozen is None else local_peer-local_frozen
                did=None if shared_diff is None or local_diff is None else shared_diff-local_diff
                if did is not None:
                    difference={"topology":top,"seed":seed,"imitation":imi,
                                "d_shared":shared_diff,"d_local":local_diff,
                                "spillover_did":did,
                                "shared_unfinished_delta":summaries[(top,seed,imi,"reduced_peer_shared_1")]["unfinished"]-summaries[(top,seed,imi,"reduced_frozen_shared_1")]["unfinished"]}
                    differences.append(difference)
                    if shared_diff>0 and did>=svc and difference["shared_unfinished_delta"]>0:
                        primary.append((top,seed,imi))
                for name,a,b in (("no_imitation_nonzero","reduced_no_imitation_shared_1","reduced_frozen_shared_1"),
                                 ("shared_24_nonzero","reduced_peer_shared_24","reduced_frozen_shared_24")):
                    x,y=value(top,seed,imi,a),value(top,seed,imi,b)
                    if x is not None and y is not None and x!=y: controls[name]+=1
    supported=all(sum(1 for t,s,i in primary if t==top and i==imi)>=6
                  for top in config["topologies"] for imi in config["imitation_probabilities"])
    status=("PASS_METHOD_SCOPED" if not errors and supported and not any(controls.values()) else
            "NO_INCREMENTAL_SHARED_SPILLOVER" if not errors and not primary and not any(controls.values()) else "METHOD_FAIL_OR_INCONCLUSIVE")
    return {"status":status,"errors":errors,"groups":len(summaries),"primary_reversals":[list(x) for x in primary],
            "control_nonzero_counts":controls,"differences":differences,
            "summary":[{"key":list(k),**v} for k,v in sorted(summaries.items())]}

if __name__=="__main__":
    config=json.load(open(sys.argv[2],encoding="utf-8"))
    opener=gzip.open if sys.argv[1].endswith(".gz") else open
    with opener(sys.argv[1],"rt",encoding="utf-8") as source: raw=json.load(source)
    print(json.dumps(audit(raw,config),sort_keys=True,separators=(",",":")))
