import json
from itertools import product

def resident(trace, msg_t):
    previous=False; events=[]; stale=0
    for t,state in enumerate(trace):
        if t == msg_t:
            stale += 1
            continue
        if state and not previous:
            events.append(["effect", t, 1])
        previous=state
    events.append(["release", 4, 1])
    return events, stale

def main():
    rows=[]
    for trace in product((False, True), repeat=4):
        for msg_t in range(4):
            events, stale = resident(trace, msg_t)
            expected=sum(1 for i,state in enumerate(trace) if state and (i == 0 or not trace[i-1]))
            rows.append({"trace":list(trace),"msg_t":msg_t,"resident":events,"stale_rejections":stale,"valid":len([e for e in events if e[0]=="effect"]) == expected and events[-1][0] == "release" and stale == 1})
    with open("RESULT.json", "w", encoding="utf-8") as f:
        json.dump({"rows_detail":rows}, f, sort_keys=True, indent=2)
    print("rows=64")
if __name__ == "__main__": main()
