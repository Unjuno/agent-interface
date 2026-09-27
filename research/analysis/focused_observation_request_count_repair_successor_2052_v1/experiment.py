import hashlib,json,itertools
def admit(f,r):
    if f["epoch"]!=r["epoch"]: return False,"epoch"
    if f["identity"]!=r["identity"]: return False,"identity"
    if r["reason"]!="uncertain": return False,"reason"
    x,y,w,h=r["region"]; W,H=f["size"]
    if w<=0 or h<=0 or x<0 or y<0 or x+w>W or y+h>H: return False,"region"
    if r["authority"]: return False,"authority"
    return True,"ok"
def main():
    frames=[{"epoch":e,"identity":i,"size":(10,10)} for e in (1,2) for i in ("a","b")]
    reasons=("uncertain","changed"); regions=((0,0,2,2),(9,9,1,1),(10,0,1,1),(0,0,0,1))
    rows=[]
    for f,ep,ident,reason,reg,auth in itertools.product(frames,(1,2),("a","b"),reasons,regions,(False,True)):
        ok,why=admit(f,{"epoch":ep,"identity":ident,"reason":reason,"region":reg,"authority":auth})
        expected=(f["epoch"]==ep and f["identity"]==ident and reason=="uncertain" and reg in regions[:2] and not auth)
        rows.append({"ok":ok,"expected":expected,"why":why,"auth":auth})
    raw=json.dumps(rows,sort_keys=True,separators=(",",":"))
    result={"rows":len(rows),"accepted":sum(r["ok"] for r in rows),"expected_accepted":sum(r["expected"] for r in rows),"mismatches":sum(r["ok"]!=r["expected"] for r in rows),"authority_positive_admissions":sum(r["ok"] and r["auth"] for r in rows),"sha256":hashlib.sha256(raw.encode()).hexdigest()}
    print(json.dumps(result,sort_keys=True)); assert result["rows"]==256 and result["accepted"]==8 and result["mismatches"]==0 and result["authority_positive_admissions"]==0
if __name__=="__main__": main()
