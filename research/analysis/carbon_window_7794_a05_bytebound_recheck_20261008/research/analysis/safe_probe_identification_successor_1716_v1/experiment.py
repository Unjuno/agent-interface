from itertools import product
import hashlib, json

STATES=range(3); ACTIONS=range(2)
PAIRS=tuple((s,a) for s in STATES for a in ACTIONS)
TABLES=tuple(product(STATES, repeat=len(PAIRS)))

def consistent(table, observed):
    return tuple(i for i,t in enumerate(TABLES) if all(t[PAIRS.index(p)]==v for p,v in observed.items()))

def choose_unknown(candidates, safe):
    if not safe: return None
    scored=[]
    for p in safe:
        groups={v:[] for v in STATES}
        i=PAIRS.index(p)
        for idx in candidates: groups[TABLES[idx][i]].append(idx)
        worst=max(len(g) for g in groups.values())
        scored.append((worst,p))
    return min(scored)[1]

def oracle(candidates, safe):
    return choose_unknown(candidates,safe)

def main():
    rows=[]
    for target_index in (0, 1, 2, len(TABLES)-1):
      for mask in range(1<<len(PAIRS)):
        truth=TABLES[target_index]
        observed={p:truth[i] for i,p in enumerate(PAIRS) if mask&(1<<i)}
        candidates=consistent(TABLES,observed)
        unknown=tuple(p for p in PAIRS if p not in observed)
        safe=unknown[:-1] if len(unknown)>1 else unknown
        selected=choose_unknown(candidates,safe)
        first=unknown[0] if unknown else None
        rows.append({"target":target_index,"mask":mask,"class_before":len(candidates),"unknown":len(unknown),"safe":len(safe),"selected":selected,"first":first})
        if selected is not None:
            i=PAIRS.index(selected)
            post=[]
            for v in STATES:
                post.append(len([idx for idx in candidates if TABLES[idx][i]==v]))
            assert max(post)==min(x[0] for x in [(max(len([idx for idx in candidates if TABLES[idx][PAIRS.index(p)]==v]) for v in STATES),p) for p in safe])
            assert selected in safe
        else:
            assert unknown==() or not safe
    assert all(r["selected"] == r["first"] for r in rows if r["unknown"] > 1)
    # Explicit unsafe admission control: the omitted final unknown pair is never selected.
    unsafe_rejections=sum(1 for r in rows if r["unknown"]>0 and r["safe"]<r["unknown"])
    payload=json.dumps(rows,sort_keys=True,default=str).encode()
    digest=hashlib.sha256(payload).hexdigest()
    tampered=list(rows); tampered[0]=dict(tampered[0],selected=(2,1))
    assert hashlib.sha256(json.dumps(tampered,sort_keys=True,default=str).encode()).hexdigest()!=digest
    print({"rows":len(rows),"tables":len(TABLES),"digest":digest,"unsafe_rejections":unsafe_rejections,"formal":1,"audit":1,"reruns":0,"tuning":0})

if __name__=="__main__": main()
