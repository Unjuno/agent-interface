import json,sys

def simulate(case,policy,fixed_cap,class_cap):
    queues={}; obligations={}; admitted=[]; deferred=[]; read_done=[]; max_backlog=0; backlog_area=0; max_age=0; release_done=[]; timeline=[]
    for tick in range(case["horizon"]):
        for task in [x for x in case["tasks"] if x["at"]==tick]:
            pending=sum(o["status"]=="PENDING" for o in obligations.values())
            effect_pending=sum(o["status"]=="PENDING" and o["kind"]=="effect" for o in obligations.values())
            resource_pending=sum(o["status"]=="PENDING" and o["resource"]==task["resource"] for o in obligations.values())
            if task["kind"]=="readonly":
                allow=not(policy=="GLOBAL_WAIT" and pending>0)
                if allow:read_done.append(task["id"]);admitted.append(task["id"])
                else:deferred.append(task["id"])
                continue
            if task["kind"]=="mandatory_release":allow=True
            elif policy=="LEDGER_ONLY":allow=True
            elif policy=="GLOBAL_WAIT":allow=pending==0
            elif policy=="FIXED_CAP2":allow=effect_pending<fixed_cap
            else:allow=resource_pending<class_cap
            if not allow:deferred.append(task["id"]);continue
            admitted.append(task["id"]);oid="ob-"+task["id"]
            obligations[oid]={"task":task["id"],"resource":task["resource"],"kind":task["kind"],"created":tick,"status":"PENDING"}
            queues.setdefault(task["resource"],[]).append(oid)
            max_backlog=max(max_backlog,sum(o["status"]=="PENDING" for o in obligations.values()))
        pending_pre_service=[o for o in obligations.values() if o["status"]=="PENDING"]
        if pending_pre_service:max_age=max(max_age,max(tick-o["created"]+1 for o in pending_pre_service))
        for resource,queue in queues.items():
            spec=case["resources"].get(resource,{"slots_per_tick":0,"oracle":True})
            slots=spec["slots_per_tick"] if spec["slots_per_tick"] is not None else 0
            if not spec["oracle"]:slots=0
            for _ in range(slots):
                if not queue:break
                oid=queue.pop(0);o=obligations[oid];o["status"]="VERIFIED_RELEASE" if o["kind"]=="mandatory_release" else "VERIFIED_EFFECT";o["resolved_at"]=tick
                if o["kind"]=="mandatory_release":release_done.append({"id":o["task"],"tick":tick})
        pending_now=[o for o in obligations.values() if o["status"]=="PENDING"]
        backlog_area+=len(pending_now)
        if pending_now:max_age=max(max_age,max(tick-o["created"]+1 for o in pending_now))
        timeline.append({"tick":tick,"system_pending":len(pending_now)})
    oracle_missing=any(not r["oracle"] for r in case["resources"].values())
    capacity_unknown=any(r["slots_per_tick"] is None for r in case["resources"].values())
    if oracle_missing:status="UNRESOLVABLE_ORACLE_GAP"
    elif capacity_unknown:status="UNKNOWN_CAPACITY"
    elif deferred:status="SATURATED_BUT_CONTAINED"
    elif not any(o["status"]=="PENDING" for o in obligations.values()):status="FEASIBLE_SERVICE_REGION"
    else:status="SATURATED_BUT_CONTAINED"
    return {"status":status,"admitted":admitted,"deferred":deferred,"readonly_completed":read_done,"verified_effects":[o["task"] for o in obligations.values() if o["status"]=="VERIFIED_EFFECT"],"unresolved_ids":[k for k,o in obligations.items() if o["status"]=="PENDING"],"max_system_backlog":max_backlog,"backlog_area":backlog_area,"max_age":max_age,"mandatory_releases":release_done,"timeline":timeline,"ledger":obligations}

def replay(events):
    records={};snapshots=[]
    for e in events:
        if e["type"]=="CREATE":records[e["id"]]={"owner":e["owner"],"status":"PENDING","parent":None,"owner_crashed":False}
        elif e["type"]=="OWNER_CRASH":records[e["id"]]["owner_crashed"]=True
        elif e["type"]=="ACCEPTED_HANDOFF":records[e["id"]]["owner"]=e["to"]
        elif e["type"]=="TIMEOUT":pass
        elif e["type"]=="COMPENSATION_FAILED":records[e["child"]]={"owner":e["owner"],"status":"PENDING","parent":e["parent"],"owner_crashed":False}
        elif e["type"]=="VERIFIED_TERMINAL":records[e["id"]]["status"]="VERIFIED_TERMINAL"
        snapshots.append({"after":e["type"],"system_pending":sum(x["status"]=="PENDING" for x in records.values())})
    return {"records":records,"snapshots":snapshots,"system_pending":sum(x["status"]=="PENDING" for x in records.values())}

def run(data):
    return {"schema":"obligation-capacity-t002-result-v1","cases":{c["id"]:{p:simulate(c,p,data["fixed_cap"],data["class_cap_per_resource"]) for p in data["policies"]} for c in data["cases"]},"ledger_replay":replay(data["ledger_events"])}

def main(src,dst):
    data=json.load(open(src,encoding="utf-8"));out=run(data)
    with open(dst,"w",encoding="utf-8") as f:json.dump(out,f,indent=2,sort_keys=True);f.write("\n")
if __name__=="__main__":main(*sys.argv[1:3])
