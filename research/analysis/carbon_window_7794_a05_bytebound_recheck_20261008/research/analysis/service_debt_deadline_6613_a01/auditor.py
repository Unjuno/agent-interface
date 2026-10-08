import json
import sys


def build_tasks(seed, scenario):
    state=(seed ^ {"asymmetric_recurring":0x13579BDF,"burst_recovery":0x2468ACE0,
                   "rights_interrupt":0x5A5A5A5A}[scenario]) & 0xffffffff
    def word():
        nonlocal state
        state=(state ^ ((state << 13)&0xffffffff))&0xffffffff
        state=(state ^ (state >> 17))&0xffffffff
        state=(state ^ ((state << 5)&0xffffffff))&0xffffffff
        return state
    records=[]
    for who in ("A","B"):
        arrival=0
        for ix in range(6):
            if scenario=="burst_recovery":
                arrival=word()%2 if ix<3 else 8+word()%3
            else:
                arrival+=word()%3
            duration=1+word()%6
            limit=arrival+duration+word()%16
            allowed=not(scenario=="rights_interrupt" and who=="B" and ix==2)
            records.append({"id":f"{who}{ix}","principal":who,"arrival":arrival,
                            "service":duration,"deadline":limit,"eligible":allowed,"mandatory":False})
    if scenario=="rights_interrupt":
        arrival=1+word()%4
        records.append({"id":"SYS0","principal":"SYS","arrival":arrival,"service":1,
                        "deadline":arrival+1,"eligible":True,"mandatory":True})
    return records


def replay(jobs, rule):
    waiting = jobs[:]
    timeline = []
    clock = 0
    spent = {}
    cursor = 0
    while waiting:
        available = [j for j in waiting if j["eligible"] and j["arrival"] <= clock]
        if not available:
            arrivals = [j["arrival"] for j in waiting if j["eligible"] and j["arrival"] > clock]
            if not arrivals:
                return timeline
            clock = min(arrivals)
            continue
        hard = [j for j in available if j["mandatory"]]
        candidates = hard if hard else available
        if rule == "fifo":
            chosen = sorted(candidates, key=lambda j:(j["arrival"],j["id"]))[0]
        elif rule == "shortest":
            chosen = sorted(candidates, key=lambda j:(j["service"],j["arrival"],j["id"]))[0]
        else:
            owners = sorted(set(j["principal"] for j in candidates))
            rotation = owners[cursor % len(owners):] + owners[:cursor % len(owners)]
            positions = {name:index for index,name in enumerate(rotation)}
            chosen = sorted(candidates, key=lambda j:(spent.get(j["principal"],0),positions[j["principal"]],j["arrival"],j["id"]))[0]
            cursor += 1
        begin = max(clock,chosen["arrival"])
        finish = begin+chosen["service"]
        timeline.append({"id":chosen["id"],"principal":chosen["principal"],"start":begin,"end":finish,
                         "wait":begin-chosen["arrival"],"on_time":finish<=chosen["deadline"],
                         "mandatory":chosen["mandatory"],"eligible":chosen["eligible"]})
        clock = finish
        spent[chosen["principal"]] = spent.get(chosen["principal"],0)+chosen["service"]
        waiting.remove(chosen)
    return timeline


def audit(fixture_path, raw_path, construction=False):
    with open(fixture_path,encoding="utf-8") as source:
        fixture=json.load(source)
    with open(raw_path,encoding="utf-8") as source:
        raw=json.load(source)
    seeds=fixture["construction_seeds"] if construction else fixture["formal_seeds"]
    errors=[]
    expected={(seed,s,p):(build_tasks(seed,s),p) for seed in seeds
              for s in fixture["scenarios"] for p in fixture["policies"]}
    seen=set()
    if raw.get("allocation_id") != fixture["allocation_id"]: errors.append("allocation_id")
    for row in raw.get("rows",[]):
        key=(row.get("seed"),row.get("scenario"),row.get("policy"))
        if key not in expected or key in seen: errors.append("row_identity"); continue
        seen.add(key)
        jobs,policy=expected[key]
        expected_offered=[{"id":t["id"],"eligible":t["eligible"],"mandatory":t["mandatory"]} for t in jobs]
        if row.get("offered") != expected_offered: errors.append("offered_ledger:"+str(key))
        truth=replay(jobs,policy)
        if row.get("schedule") != truth: errors.append("schedule_replay:"+str(key))
        dispatched={x["id"] for x in row.get("schedule",[])}
        if len(dispatched)!=len(row.get("schedule",[])): errors.append("duplicate_dispatch:"+str(key))
        if any(not t["eligible"] and t["id"] in dispatched for t in jobs): errors.append("ineligible_dispatch:"+str(key))
        mandatory={t["id"] for t in jobs if t["mandatory"] and t["eligible"]}
        if not mandatory.issubset(dispatched): errors.append("mandatory_omission:"+str(key))
        for a,b in zip(row.get("schedule",[]),row.get("schedule",[])[1:]):
            if a["end"]>b["start"]: errors.append("overlap:"+str(key))
    if seen != set(expected): errors.append("missing_rows")
    summaries={}
    for (seed,sid,policy),(jobs,_) in expected.items():
        r=next((x for x in raw.get("rows",[]) if (x.get("seed"),x.get("scenario"),x.get("policy"))==(seed,sid,policy)),None)
        if r:
            elig={t["id"] for t in jobs if t["eligible"] and not t["mandatory"]}
            got=[x for x in r["schedule"] if x["id"] in elig]
            summaries.setdefault((sid,policy),[]).append((max((x["wait"] for x in got),default=0),sum(x["on_time"] for x in got)))
    avg_wait={k:sum(v[0] for v in vals)/len(vals) for k,vals in summaries.items()}
    total_ontime={k:sum(v[1] for v in vals) for k,vals in summaries.items()}
    decision=[]
    if not (avg_wait[("asymmetric_recurring","debt")] < min(avg_wait[("asymmetric_recurring","fifo")],avg_wait[("asymmetric_recurring","shortest")])):
        decision.append("no_asymmetric_wait_gain")
    for sid in fixture["scenarios"]:
        floor=min(total_ontime[(sid,"fifo")],total_ontime[(sid,"shortest")])
        if total_ontime[(sid,"debt")] < floor: decision.append("on_time_floor:"+sid)
    return {"audit_status":"PASS_RAW_REPLAY" if not errors else "FAIL_AUDIT","errors":errors,
            "hypothesis_disposition":"PASS_METHOD_SCOPED" if not decision and not errors else "FAIL_HYPOTHESIS" if not errors else "UNRESOLVED_AUDIT_FAILURE",
            "decision_reasons":decision,
            "rows":len(seen),"summaries":{f"{k[0]}:{k[1]}":{"mean_trace_max_wait":round(avg_wait[k],6),"on_time_total":total_ontime[k]} for k in summaries}}


if __name__=="__main__":
    result=audit(sys.argv[1],sys.argv[2],"--construction" in sys.argv[4:])
    with open(sys.argv[3],"w",encoding="utf-8") as destination:
        json.dump(result,destination,sort_keys=True,separators=(",",":"))
        destination.write("\n")
    print(json.dumps(result,sort_keys=True))
    raise SystemExit(0 if result["audit_status"]=="PASS_RAW_REPLAY" else 1)
