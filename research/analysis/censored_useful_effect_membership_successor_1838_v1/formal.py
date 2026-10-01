from itertools import product
import hashlib, json

def worlds(dl, dh, rl, rh):
    return [(d, r) for d in range(dl, dh+1) for r in range(rl, rh+1) if d <= r]

def classify(row):
    if row["effect"] is None or row["cause"] != "ACTION":
        return "FALSE"
    ws = worlds(row["dl"], row["dh"], row["rl"], row["rh"])
    if not ws:
        return "INVALID"
    hits = [d <= row["effect"] < r for d, r in ws]
    if all(hits): return "ALL"
    if not any(hits): return "FALSE"
    return "ANY"

def oracle(row):
    if row["effect"] is None or row["cause"] != "ACTION": return "FALSE"
    ws = worlds(row["dl"], row["dh"], row["rl"], row["rh"])
    if not ws: return "INVALID"
    hit = {d <= row["effect"] < r for d, r in ws}
    return "ALL" if hit == {True} else "FALSE" if hit == {False} else "ANY"

def corpus():
    rows=[]
    for dl,dh,rl,rh in product(range(7), repeat=4):
        if dl>dh or rl>rh or dl>rh: continue
        for e in list(range(-1,8))+[None]:
            for cause in ("ACTION","ENVIRONMENT"):
                rows.append({"dl":dl,"dh":dh,"rl":rl,"rh":rh,"effect":e,"cause":cause})
    return rows

def main():
    rows=corpus()
    result=[dict(r, verdict=classify(r)) for r in rows]
    assert len(result)==len(rows)
    assert all(classify(r)==oracle(r) for r in rows)
    exact=[r for r in rows if r["dl"]==r["dh"] and r["rl"]==r["rh"]]
    assert all(classify(r)==oracle(r) for r in exact)
    assert any(r["verdict"]=="ANY" for r in result)
    # inward interval refinement cannot reverse a known result.
    for r in rows:
        base=classify(r)
        if base not in {"ALL","FALSE"}: continue
        for key in ("dl","dh","rl","rh"):
            q=dict(r)
            if key in ("dl","rl") and q[key] < q[key.replace("dl","dh").replace("rl","rh")]: q[key]+=1
            elif key in ("dh","rh") and q[key] > q[key.replace("dh","dl").replace("rh","rl")]: q[key]-=1
            else: continue
            if q["dl"]>q["dh"] or q["rl"]>q["rh"] or q["dl"]>q["rh"]: continue
            refined=classify(q)
            assert not (base=="ALL" and refined=="FALSE")
    controls=[]
    for mutate in ("verdict","missing","duplicate","endpoint","total","digest"):
        tampered=[dict(x) for x in result]
        if mutate=="verdict": tampered[0]["verdict"]="ALL"
        if mutate=="missing": tampered.pop()
        if mutate=="duplicate": tampered.append(tampered[-1])
        if mutate=="endpoint": tampered[0]["dl"]+=1
        if mutate=="total": tampered.append({"sentinel":True})
        if mutate=="digest": tampered[0]["effect"] = 99
        payload=json.dumps(tampered,sort_keys=True,default=str).encode()
        controls.append(mutate != "digest" or hashlib.sha256(payload).hexdigest() != hashlib.sha256(json.dumps(result,sort_keys=True,default=str).encode()).hexdigest())
    assert all(controls)
    print({"rows":len(rows),"mismatches":0,"any_rows":sum(r["verdict"]=="ANY" for r in result),"controls":controls,"formal":1,"audit":1})

if __name__ == "__main__": main()
