from __future__ import annotations
import json,statistics,sys,time
from pathlib import Path
import backend,cases

def q(xs,p):
 ys=sorted(xs);i=(len(ys)-1)*p;lo=int(i);hi=min(lo+1,len(ys)-1);return ys[lo]+(ys[hi]-ys[lo])*(i-lo)

def run():
 rows=[]; dt=[]; pt=[]; serialization=[]; reuse=0
 for i,case in enumerate(cases.CASES):
  f=case["features"]
  s0=time.perf_counter_ns(); payload=json.dumps({"features":f},sort_keys=True,separators=(",",":")).encode();s1=time.perf_counter_ns()
  direct,dns=backend.timed_forward("direct",f)
  pred,pns=backend.timed_forward("predicates",f)
  disp,reads=backend.graph(pred)
  reused=sum(max(0,reads.count(p)-1) for p in backend.PREDICATES);reuse+=reused
  rows.append({"index":i,"name":case["name"],"features":f,"direct":direct,"predicates":pred,"graph":disp,
               "graph_reads":reads,"reuse_reads":reused,"authority_granted":False,
               "timing_ns":{"serialize":s1-s0,"direct":dns,"predicates":pns},"payload_sha256":__import__('hashlib').sha256(payload).hexdigest()})
  serialization.append(s1-s0);dt.append(dns);pt.append(pns)
 return {"allocation":"semantic-predicate-fabric-4215-20260923-01","formal_invocations":1,"reruns":0,"replacements":0,"exclusions":0,"tuning":0,
         "case_count":len(rows),"predicate_count":len(backend.PREDICATES),"direct_calls":len(rows),"predicate_calls":len(rows),"reuse_reads":reuse,
         "timing":{"direct":{"p50":q(dt,.5),"p95":q(dt,.95),"p99":q(dt,.99)},"predicates":{"p50":q(pt,.5),"p95":q(pt,.95),"p99":q(pt,.99)},"serialization":{"p50":q(serialization,.5),"p95":q(serialization,.95),"p99":q(serialization,.99)}},
         "rows":rows}
if __name__=="__main__":
 if len(sys.argv)!=2:raise SystemExit("usage: run.py OUTPUT")
 out=Path(sys.argv[1]);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(run(),sort_keys=True,indent=2)+"\n")
