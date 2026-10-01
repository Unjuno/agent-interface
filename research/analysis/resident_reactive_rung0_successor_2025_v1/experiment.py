import hashlib, json
from itertools import product

def resident(trace, generation_message):
    owned=True; prev=False; events=[]; generation=1; stale_rejections=0
    for t,state in enumerate(trace):
        requested_t, requested_generation = generation_message
        if requested_t == t and requested_generation != generation:
            stale_rejections += 1
            continue
        if state and not prev and owned:
            events.append(("effect",t,generation))
        prev=state
    owned=False
    events.append(("release",4,generation))
    return events, owned, stale_rejections

def poll(trace):
    return [("effect",3,1)] if any(trace[1:3]) else []

def open_loop(trace):
    return [("effect",1,1)]

def main():
    rows=[]
    for trace in product((False,True),repeat=4):
        for msg_t in range(4):
            events,owned,rejected=resident(trace,(msg_t,0))
            expected=sum(1 for i,s in enumerate(trace) if s and (i==0 or not trace[i-1]))
            valid=(sum(e[0]=="effect" for e in events)==expected and
                   not owned and events[-1][0]=="release" and rejected==1)
            rows.append({"trace":trace,"msg_t":msg_t,"resident":events,
                         "stale_rejections":rejected,"poll":poll(trace),
                         "open_loop":open_loop(trace),"valid":valid})
    raw=json.dumps(rows,sort_keys=True,separators=(",",":"))
    print(json.dumps({"rows":len(rows),"valid":sum(r["valid"] for r in rows),
      "stale_rejections":sum(r["stale_rejections"] for r in rows),
      "terminal_release_failures":sum(r["resident"][-1][0]!="release" for r in rows),
      "sha256":hashlib.sha256(raw.encode()).hexdigest()}))
if __name__=="__main__": main()
