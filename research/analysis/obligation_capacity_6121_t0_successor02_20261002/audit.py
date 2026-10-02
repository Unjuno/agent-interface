import json,sys

POLICIES={"LEDGER_ONLY","GLOBAL_WAIT","FIXED_CAP2","CLASS_AWARE"}

def replay_independently(case,policy,cap,class_cap):
    ledger={};lanes={};accepted=[];deferred=[];readonly=[];release=[];timeline=[];max_backlog=0;area=0;age_peak=0
    for now in range(case["horizon"]):
        for task in (t for t in case["tasks"] if t["at"]==now):
            live=[v for v in ledger.values() if v["state"]=="pending"]
            discretionary=[v for v in live if v["kind"]=="effect"]
            same=[v for v in discretionary if v["lane"]==task["resource"]]
            if task["kind"]=="readonly":
                ok=not(policy=="GLOBAL_WAIT" and live)
                (readonly if ok else deferred).append(task["id"])
                if ok:accepted.append(task["id"])
                continue
            if task["kind"]=="mandatory_release":ok=True
            elif policy=="LEDGER_ONLY":ok=True
            elif policy=="GLOBAL_WAIT":ok=not live
            elif policy=="FIXED_CAP2":ok=len(discretionary)<cap
            else:ok=len(same)<class_cap
            if not ok:deferred.append(task["id"]);continue
            accepted.append(task["id"]);oid="ob-"+task["id"]
            ledger[oid]={"task":task["id"],"lane":task["resource"],"kind":task["kind"],"created":now,"state":"pending"}
            lanes.setdefault(task["resource"],[]).append(oid)
            max_backlog=max(max_backlog,sum(v["state"]=="pending" for v in ledger.values()))
        live=[v for v in ledger.values() if v["state"]=="pending"]
        if live:age_peak=max(age_peak,max(now-v["created"]+1 for v in live))
        for lane,ids in lanes.items():
            spec=case["resources"].get(lane,{"slots_per_tick":0,"oracle":True})
            capacity=spec["slots_per_tick"]
            if capacity is None or not spec["oracle"]:capacity=0
            while capacity>0 and ids:
                oid=ids.pop(0);item=ledger[oid];item["state"]="verified-release" if item["kind"]=="mandatory_release" else "verified-effect";item["resolved"]=now
                if item["kind"]=="mandatory_release":release.append({"id":item["task"],"tick":now})
                capacity-=1
        area+=sum(v["state"]=="pending" for v in ledger.values())
        timeline.append({"tick":now,"system_pending":sum(v["state"]=="pending" for v in ledger.values())})
    no_oracle=any(not x["oracle"] for x in case["resources"].values())
    unknown=any(x["slots_per_tick"] is None for x in case["resources"].values())
    if no_oracle:status="UNRESOLVABLE_ORACLE_GAP"
    elif unknown:status="UNKNOWN_CAPACITY"
    elif deferred or any(v["state"]=="pending" for v in ledger.values()):status="SATURATED_BUT_CONTAINED"
    else:status="FEASIBLE_SERVICE_REGION"
    canonical={k:{"task":v["task"],"resource":v["lane"],"kind":v["kind"],"created":v["created"],"status":v["state"].upper().replace("-","_"),**({"resolved_at":v["resolved"]} if "resolved" in v else {})} for k,v in ledger.items()}
    return {"status":status,"admitted":accepted,"deferred":deferred,"readonly_completed":readonly,"verified_effects":[v["task"] for v in ledger.values() if v["state"]=="verified-effect"],"unresolved_ids":[k for k,v in ledger.items() if v["state"]=="pending"],"max_system_backlog":max_backlog,"backlog_area":area,"max_age":age_peak,"mandatory_releases":release,"timeline":timeline,"ledger":canonical}

def replay_ledger(events):
    entries={};snapshots=[]
    for e in events:
        typ=e["type"]
        if typ=="CREATE":entries[e["id"]]={"owner":e["owner"],"status":"PENDING","parent":None,"owner_crashed":False}
        elif typ=="OWNER_CRASH":entries[e["id"]]["owner_crashed"]=True
        elif typ=="ACCEPTED_HANDOFF":entries[e["id"]]["owner"]=e["to"]
        elif typ=="TIMEOUT":pass
        elif typ=="COMPENSATION_FAILED":entries[e["child"]]={"owner":e["owner"],"status":"PENDING","parent":e["parent"],"owner_crashed":False}
        elif typ=="VERIFIED_TERMINAL":entries[e["id"]]["status"]="VERIFIED_TERMINAL"
        snapshots.append({"after":typ,"system_pending":sum(x["status"]=="PENDING" for x in entries.values())})
    return {"records":entries,"snapshots":snapshots,"system_pending":sum(x["status"]=="PENDING" for x in entries.values())}

def audit(fixture,output):
    errors=[];actual=output.get("cases",{})
    if set(actual)!={c["id"] for c in fixture["cases"]}:errors.append("case_set")
    for case in fixture["cases"]:
        if set(actual.get(case["id"],{}))!=POLICIES:errors.append("policy_set:"+case["id"]);continue
        for policy in POLICIES:
            rebuilt=replay_independently(case,policy,fixture["fixed_cap"],fixture["class_cap_per_resource"])
            if actual[case["id"]][policy]!=rebuilt:errors.append("simulation_mismatch:"+case["id"]+":"+policy)
    ledger=replay_ledger(fixture["ledger_events"])
    if output.get("ledger_replay")!=ledger:errors.append("ledger_transition_mismatch")
    near=actual.get("near_saturated_burst_drain",{})
    if near:
        ca=near.get("CLASS_AWARE",{});lo=near.get("LEDGER_ONLY",{});gw=near.get("GLOBAL_WAIT",{})
        if not(ca.get("max_system_backlog",999)<lo.get("max_system_backlog",-1) and ca.get("max_age",999)<lo.get("max_age",-1)):errors.append("backlog_age_tradeoff")
        if len(ca.get("verified_effects",[]))<=len(gw.get("verified_effects",[])):errors.append("useful_effects_vs_global_wait")
        if any(x.get("tick")!=0 for p in POLICIES for x in near.get(p,{}).get("mandatory_releases",[])):errors.append("mandatory_release_delay")
    over=actual.get("above_capacity_burst",{}).get("CLASS_AWARE",{})
    if over and (not over.get("deferred") or over.get("status")!="SATURATED_BUT_CONTAINED"):errors.append("overload_not_contained")
    if actual.get("missing_effect_oracle",{}).get("CLASS_AWARE",{}).get("status")!="UNRESOLVABLE_ORACLE_GAP":errors.append("missing_oracle_claim")
    if actual.get("unknown_capacity",{}).get("CLASS_AWARE",{}).get("status")!="UNKNOWN_CAPACITY":errors.append("unknown_capacity_claim")
    return {"status":"PASS_METHOD_SCOPED" if not errors else "FAIL","case_count":len(fixture["cases"]),"policy_runs":len(fixture["cases"])*len(POLICIES),"ledger_events":len(fixture["ledger_events"]),"errors":errors}

def main(fp,rp,dp):
    f=json.load(open(fp));r=json.load(open(rp));res=audit(f,r)
    with open(dp,"w") as stream:json.dump(res,stream,indent=2,sort_keys=True);stream.write("\n")
    print(json.dumps(res,sort_keys=True));return 0 if not res["errors"] else 1
if __name__=="__main__":raise SystemExit(main(*sys.argv[1:4]))
