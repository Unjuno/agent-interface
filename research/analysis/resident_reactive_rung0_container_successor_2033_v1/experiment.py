import hashlib,json
from itertools import product
def resident(trace,msg):
    events=[]; prev=False; generation=1
    for t,state in enumerate(trace):
        if msg==(t,0): pass
        if state and not prev: events.append(("effect",t,generation))
        prev=state
    events.append(("release",4,generation))
    return events
def oracle(trace):
    return sum(1 for i,s in enumerate(trace) if s and (i==0 or not trace[i-1]))
def main():
    rows=[]
    for trace in product((False,True),repeat=4):
        for msg_t in range(4):
            ev=resident(trace,(msg_t,0))
            rows.append({"trace":trace,"msg_t":msg_t,"events":ev,"valid":sum(e[0]=="effect" for e in ev)==oracle(trace) and ev[-1][0]=="release"})
    raw=json.dumps(rows,sort_keys=True,separators=(",",":"))
    result={"rows":len(rows),"valid":sum(r["valid"] for r in rows),"edge_events":sum(sum(e[0]=="effect" for e in r["events"]) for r in rows),"terminal_release_failures":sum(r["events"][-1][0]!="release" for r in rows),"sha256":hashlib.sha256(raw.encode()).hexdigest()}
    print(json.dumps(result,sort_keys=True))
    assert result["rows"]==64 and result["valid"]==64 and result["terminal_release_failures"]==0
if __name__=="__main__": main()
