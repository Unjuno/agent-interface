import hashlib,json,itertools
from pathlib import Path
def candidate(f,r):
    if f["epoch"]!=r["epoch"]: return False,"epoch"
    if f["identity"]!=r["identity"]: return False,"identity"
    if r["reason"]!="uncertain": return False,"reason"
    x,y,w,h=r["region"]; W,H=f["size"]
    if w<=0 or h<=0 or x<0 or y<0 or x+w>W or y+h>H: return False,"region"
    if r["authority"]: return False,"authority"
    return True,"ok"
def main():
    frames=[{"epoch":e,"identity":i,"size":[10,10]} for e in (1,2) for i in ("a","b")]
    reasons=("uncertain","changed"); regions=[[0,0,2,2],[9,9,1,1],[10,0,1,1],[0,0,0,1]]
    rows=[]
    for f,ep,ident,reason,reg,auth in itertools.product(frames,(1,2),("a","b"),reasons,regions,(False,True)):
        req={"epoch":ep,"identity":ident,"reason":reason,"region":reg,"authority":auth}
        ok,why=candidate(f,req); rows.append({"frame":f,"request":req,"candidate":ok,"reason":why})
    raw=json.dumps(rows,sort_keys=True,separators=(",",":"))
    result={"rows":rows,"rows_count":len(rows),"candidate_accepted":sum(x["candidate"] for x in rows),"raw_sha256":hashlib.sha256(raw.encode()).hexdigest(),"formal_invocations":1,"construction_invocations":0,"authority_events":0}
    Path(__file__).with_name("RAW_RESULT.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="rows"},sort_keys=True))
if __name__=="__main__": main()
