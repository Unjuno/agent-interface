"""Finite diagnostic gates; never a GUI/safety eligibility oracle."""
import statistics

def integer(value):
    if type(value) is not int or value < 0: raise ValueError("nonnegative integer")
    return value

def parse_cpu(raw):
    out={}
    for line in raw.splitlines():
        parts=line.split()
        if len(parts)!=2 or not parts[1].isdigit() or parts[0] in out: raise ValueError("CPU grammar")
        out[parts[0]]=int(parts[1])
    if not out: raise ValueError("empty counters")
    return out

def decision(cells):
    keyed={}
    for c in cells:
        k=(c["pair"],c["arm"])
        if type(k[0]) is not int or k[0] not in range(6) or k[1] not in ("quiet","loaded") or k in keyed: raise ValueError("pair inventory")
        if len(c["delays"])!=16: raise ValueError("budget")
        for x in c["delays"]: integer(x)
        integer(c["throttle_count"]);integer(c["throttle_usec"])
        keyed[k]=c
    if len(keyed)!=12: raise ValueError("complete pairs")
    med=lambda a: statistics.median(a)
    diffs=[med(keyed[i,"loaded"]["delays"])-med(keyed[i,"quiet"]["delays"]) for i in range(6)]
    pooled=med([x for i in range(6) for x in keyed[i,"loaded"]["delays"]])-med([x for i in range(6) for x in keyed[i,"quiet"]["delays"]])
    pressure=all(keyed[i,"loaded"]["throttle_count"]>0 and keyed[i,"loaded"]["throttle_usec"]>0 for i in range(6))
    support=pooled>=1_000_000 and sum(x>=1_000_000 for x in diffs)>=5 and pressure
    return {"status":"SUPPORT_IMPOSED_LOAD_ONLY" if support else "HOLD_NOT_SUPPORTED","pooled_ns":pooled,"paired_ns":diffs,"qualifying_pairs":sum(x>=1_000_000 for x in diffs),"all_loaded_pressure":pressure}

def validate_cell(c,spec,plan):
    def need(ok,message):
        if not ok: raise ValueError(message)
    need(all(c[k]==spec[k] for k in ("id","pair","arm")),"case identity")
    need(type(c['pair']) is int and type(c['id']) is str and type(c['arm']) is str,'typed case identity')
    need(c["status"]=="COMPLETE" and len(c["rows"])==plan["events"],"complete budget")
    pid=integer(c["pid"]);need(pid>0,"positive PID")
    start,end=integer(c["start_ns"]),integer(c["end_ns"])
    need(start<end,"cell clock")
    need(len(c["children"])==spec["burners"],"child budget")
    childpids=set()
    for child in c["children"]:
        ready,finish=child["ready"],child["finish"]
        cp=integer(child["pid"]);need(cp>0 and cp!=pid and cp not in childpids,"owned child PID")
        childpids.add(cp)
        need(child["exit_code"]==0 and type(child["exit_code"]) is int,"child terminal0")
        need(child["forced"] is False and child["stderr"]=="","child cleanup")
        need(ready["pid"]==cp and ready["ppid"]==pid and ready["case"]==spec["id"] and ready["allocation"]==plan["allocation"],"readiness authority")
        need(type(ready['pid']) is int and type(ready['ppid']) is int and type(finish['pid']) is int,'typed child identity')
        need(ready["type"]=="ready" and finish["type"]=="finish" and finish["pid"]==cp and finish["reason"]=="parent-stop","child stop")
        need(0<integer(ready["time_ns"])<=start<end and c["rows"][-1]["post"]["end_ns"]<=integer(finish["time_ns"])<=end,"child lifetime")
        need(integer(finish["iterations"])>0 and integer(finish["cpu_ns"])>0,"actual load")
    delays=validate_rows(c["rows"],pid,start,end,plan)
    first,last=c["rows"][0]["pre"]["cpu"],c["rows"][-1]["post"]["cpu"]
    return {"pair":spec["pair"],"arm":spec["arm"],"delays":delays,"throttle_count":last["nr_throttled"]-first["nr_throttled"],"throttle_usec":last["throttled_usec"]-first["throttled_usec"]}

def validate_rows(rows,pid,start,end,plan):
    def need(ok,message):
        if not ok: raise ValueError(message)
    need(0<len(rows)<=plan["events"],"prefix budget")
    previous=None;previous_process=None
    previous_end=start
    delays=[]
    required={"usage_usec","nr_periods","nr_throttled","throttled_usec"}
    for i,r in enumerate(rows):
        need(r["index"]==i and type(r["index"]) is int and r["pid"]==pid and type(r["pid"]) is int,"row identity")
        due=integer(r["due_ns"]);need(due==start+plan["initial_ns"]+i*plan["period_ns"],"absolute deadline")
        clocks=[r["pre"]["begin_ns"],r["pre"]["end_ns"],r["start_ns"],r["sleep_start_ns"],r["return_ns"],r["post"]["begin_ns"],r["post"]["end_ns"]]
        clocks=[integer(x) for x in clocks]
        need(previous_end<=clocks[0] and all(a<=b for a,b in zip(clocks,clocks[1:])) and clocks[-1]<=end,"clock ordering")
        need(integer(r["requested_ns"])==max(0,due-r["sleep_start_ns"]),"absolute sleep request")
        need(r["return_ns"]>=due,"not early")
        a,b=integer(r["cpu_start_ns"]),integer(r["cpu_end_ns"])
        need(a<=b and b-a<=r["return_ns"]-r["start_ns"]+1_000_000,"process CPU bracket")
        for snap in (r["pre"],r["post"]):
            observed=parse_cpu(snap["cpu_raw"]);need(observed==snap["cpu"] and required<=set(observed),"counter raw identity")
            need(all(type(v) is int for v in snap['cpu'].values()),'typed counters')
            for x in observed.values():integer(x)
            if previous:
                need(set(previous)==set(observed) and all(observed[k]>=previous[k] for k in previous),"counter continuity")
            previous=observed
            current_process=integer(snap["process_cpu_ns"])
            if previous_process is not None:need(current_process>=previous_process,"process CPU across snapshots")
            previous_process=current_process
            for key in ("schedstat","schedstats_enabled"):
                need(key in snap,"optional status missing")
                opt=snap[key]
                need(type(opt["available"]) is bool,"optional availability")
                if opt["available"]:
                    need(type(opt["raw"]) is str and opt["error"] is None,"optional raw")
                    if key=="schedstat":
                        need(len(opt["raw"].split())==3 and all(x.isdigit() for x in opt["raw"].split()),"schedstat grammar")
                    else:need(opt["raw"].strip() in ("0","1"),"schedstats status")
                else:need(opt["raw"] is None and type(opt["error"]) is str,"optional missing")
        need(r["pre"]["process_cpu_ns"]<=a<=b<=r["post"]["process_cpu_ns"],"CPU continuity")
        previous_end=clocks[-1]
        delays.append(r["return_ns"]-due)
    return delays
