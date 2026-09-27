from __future__ import annotations
import argparse, copy, json, os, tempfile
from audit import audit


def write_tmp(obj):
    fd,path=tempfile.mkstemp(prefix="corr_",suffix=".json"); os.close(fd)
    with open(path,"w",encoding="utf-8") as f: json.dump(obj,f,separators=(",",":"),sort_keys=True)
    return path


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("formal"); ap.add_argument("out")
    a=ap.parse_args(); base=json.load(open(a.formal,"r",encoding="utf-8"))
    tests=[]
    muts=[]
    x=copy.deepcopy(base); x["rows"][0]["position_jitter_bound_u"]=999; muts.append(("error_bound",x))
    x=copy.deepcopy(base); x["rows"][0]["jitter_u"][0]+=1; muts.append(("jitter_value",x))
    x=copy.deepcopy(base); x["rows"][0]["oracle"]*=-1; muts.append(("oracle",x))
    x=copy.deepcopy(base); x["rows"].pop(); x["row_count"]-=1; muts.append(("row_count",x))
    for name,obj in muts:
        p=write_tmp(obj)
        try:
            r=audit(p,True); rejected=(r["decision"]=="FAIL_INTEGRITY")
            tests.append({"name":name,"rejected":rejected,"errors":r["errors"]})
        finally:
            os.unlink(p)
    out={"all_rejected":all(t["rejected"] for t in tests),"tests":tests}
    with open(a.out,"w",encoding="utf-8") as f: json.dump(out,f,separators=(",",":"),sort_keys=True)
    print(json.dumps(out,sort_keys=True))
if __name__=="__main__": main()
