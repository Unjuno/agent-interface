"""Deterministic discrete-event adoption/verification model for #7741 T0c."""
import hashlib, json, sys

def uniform(*parts):
    payload=":".join(map(str,parts)).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8],"big")/(2**64)

def peers(topology,principal,n):
    if topology=="ring": return ((principal-1)%n,(principal+1)%n)
    return tuple(range(1,n)) if principal==0 else (0,)

def simulate(config,topology,seed,imitation,mode,ticks=None):
    ticks=config["ticks"] if ticks is None else ticks
    n=config["principals"]; service=config["service_ticks"]
    adopted=[False]*n; adopted[0]=True
    success_seen=[False]*n
    partitioned=mode.endswith("per_principal")
    queues=[[] for _ in range(n)] if partitioned else [[]]
    busy=[[] for _ in range(n)] if partitioned else [[]]
    servers=24 if "shared_24" in mode else (1 if mode.endswith("shared_1") else None)
    rows=[]; next_id=0
    route_p=config["route_start_probability"]["baseline" if mode.startswith("baseline") else "reduced_cost"]
    cost=config["interaction_cost"]["baseline" if mode.startswith("baseline") else "reduced_cost"]
    for tick in range(ticks):
        # Work reaching its fixed service completion is verified before this tick's adoption update.
        for qi,active in enumerate(busy):
            still=[]
            for job in active:
                if job["finish"]==tick:
                    rows.append({"type":"completion","id":job["id"],"tick":tick,
                                 "latency":tick-job["arrival"],"queue":qi,"principal":job["principal"]})
                    success_seen[job["principal"]]=True
                else: still.append(job)
            busy[qi]=still
        for p in range(n):
            before=adopted[p]; adjacent=peers(topology,p,n)
            seen=sum(success_seen[q] for q in adjacent)
            innovation=uniform("innovation",topology,seed,imitation,tick,p)
            peer_draw=uniform("peer",topology,seed,imitation,tick,p)
            exogenous=uniform("exogenous",topology,seed,imitation,tick,p)
            cause=None
            if not before:
                if mode=="reduced_peer_shared_1" or mode=="reduced_peer_shared_24" or mode=="reduced_peer_per_principal":
                    if innovation<config["innovation_probability"]:
                        adopted[p]=True; cause="innovation"
                    elif peer_draw < imitation*seen/len(adjacent):
                        adopted[p]=True; cause="peer_verified"
                elif mode=="reduced_exogenous_shared_1" and exogenous<config["innovation_probability"]+imitation*0.06:
                    adopted[p]=True; cause="exogenous"
            rows.append({"type":"adoption","tick":tick,"principal":p,"before":before,
                         "after":adopted[p],"cause":cause,"verified_peers":seen,
                         "peer_count":len(adjacent),"innovation_draw":innovation,
                         "peer_draw":peer_draw,"exogenous_draw":exogenous})
        for p in range(n):
            start_draw=uniform("route_start",topology,seed,tick,p)
            started=adopted[p] and start_draw<route_p
            rows.append({"type":"opportunity","tick":tick,"principal":p,"offered":True,
                         "adopted":adopted[p],"start_draw":start_draw,"start_probability":route_p,
                         "started":started})
            if started:
                qi=p if partitioned else 0
                job={"id":next_id,"principal":p,"arrival":tick,"cost":cost,"queue":qi}
                next_id+=1; queues[qi].append(job); rows.append({"type":"arrival",**job})
        for qi,q in enumerate(queues):
            limit=1 if partitioned else servers
            while q and len(busy[qi])<limit:
                slot=next((s for s in range(limit) if all(j["server"]!=s for j in busy[qi])),None)
                job={**q.pop(0),"server":slot,"finish":tick+service}
                busy[qi].append(job)
                rows.append({"type":"service_start","id":job["id"],"tick":tick,
                             "queue":qi,"server":slot})
    for qi,q in enumerate(queues):
        rows.extend({"type":"unfinished","id":j["id"],"state":"queued","queue":qi,
                     "principal":j["principal"],"arrival":j["arrival"]} for j in q)
    for qi,active in enumerate(busy):
        rows.extend({"type":"unfinished","id":j["id"],"state":"in_service","queue":qi,
                     "principal":j["principal"],"arrival":j["arrival"],"finish":j["finish"],
                     "server":j["server"]} for j in active)
    return rows

def build(config):
    groups=[]
    for top in config["topologies"]:
        for seed in config["seeds"]:
            for imitation in config["imitation_probabilities"]:
                for mode in config["modes"]:
                    groups.append({"topology":top,"seed":seed,"imitation":imitation,"mode":mode,
                                   "events":simulate(config,top,seed,imitation,mode)})
    return {"schema":"7741-t0c-raw-v1","config":config,"groups":groups}

if __name__=="__main__": json.dump(build(json.load(open(sys.argv[1],encoding="utf-8"))),sys.stdout,sort_keys=True,separators=(",",":"))
