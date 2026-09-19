import hashlib,json,itertools
def admit(frame,req):
    if frame["epoch"]!=req["epoch"]: return False,"epoch"
    if frame["identity"]!=req["identity"]: return False,"identity"
    if req["reason"]!="uncertain": return False,"reason"
    x,y,w,h=req["region"]
    W,H=frame["size"]
    if w<=0 or h<=0 or x<0 or y<0 or x+w>W or y+h>H: return False,"region"
    return False if req["authority"] else True,"ok"
def main():
    frames=[{"epoch":e,"identity":i,"size":(10,10)} for e in (1,2) for i in ("a","b")]
    reasons=("uncertain","changed")
    regions=((0,0,2,2),(9,9,1,1),(10,0,1,1),(0,0,0,1))
    rows=[]
    for f,ep,ident,reason,reg,auth in itertools.product(frames,(1,2),("a","b"),reasons,regions,(False,True)):
        ok,why=admit(f,{"epoch":ep,"identity":ident,"reason":reason,"region":reg,"authority":auth})
        expected=(f["epoch"]==ep and f["identity"]==ident and reason=="uncertain" and reg in regions[:2] and not auth)
        rows.append({"ok":ok,"expected":expected,"why":why})
    raw=json.dumps(rows,sort_keys=True,separators=(",",":"))
    result={"rows":len(rows),"accepted":sum(r["ok"] for r in rows),"expected_accepted":sum(r["expected"] for r in rows),"mismatches":sum(r["ok"]!=r["expected"] for r in rows),"authority_true_admitted":sum(r["ok"] and False for r in rows),"sha256":hashlib.sha256(raw.encode()).hexdigest()}
    print(json.dumps(result,sort_keys=True)); assert result["rows"]==256 and result["mismatches"]==0 and result["accepted"]==16
if __name__=="__main__": main()
