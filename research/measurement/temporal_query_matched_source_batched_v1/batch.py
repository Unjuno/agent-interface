from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
import model,oracle
TASK='TEMPORAL-QUERY-MATCHED-SOURCE-COVERAGE-BATCHED-20260918-002'
BATCH=11000; TOTAL=220000
def run(start,count,out):
 if start<0 or count!=BATCH or start%BATCH or start+count>TOTAL: raise ValueError('formal range')
 p=Path(out)
 if p.exists(): raise FileExistsError(out)
 by={k:{"n":0,"fixed":0,"query":0} for k in model.CLASSES}
 counters={"n":0,"mismatch":0,"future":0,"cross_scope":0,"budget":0,"authority":0,"fixed":0,"query":0}
 h=hashlib.sha256()
 for i in range(start,start+count):
  a=model.one(i);o=oracle.one(i)
  mismatch=(a['class']!=o['class'] or a['fixed_covered']!=o['fixed_covered'] or a['query_covered']!=o['query_covered'])
  counters['n']+=1;counters['mismatch']+=int(mismatch);counters['future']+=a['future_selected'];counters['cross_scope']+=a['cross_scope_selected'];counters['budget']+=a['budget_violations'];counters['authority']+=a['authority_grants'];counters['fixed']+=int(a['fixed_covered']);counters['query']+=int(a['query_covered'])
  z=by[a['class']];z['n']+=1;z['fixed']+=int(a['fixed_covered']);z['query']+=int(a['query_covered'])
  h.update(f"{i}|{a['class']}|{int(a['fixed_covered'])}|{int(a['query_covered'])}\n".encode())
 x={"task":TASK,"start":start,"end":start+count,"batch_index":start//BATCH,"invocation":1,"reruns":0,"counters":counters,"by_class":by,"row_digest":h.hexdigest()}
 p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
 print(json.dumps({"start":start,"end":start+count,"mismatch":counters['mismatch'],"fixed":counters['fixed'],"query":counters['query']},sort_keys=True))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--start',type=int,required=True);ap.add_argument('--count',type=int,default=BATCH);ap.add_argument('--out',required=True);a=ap.parse_args();run(a.start,a.count,a.out)
if __name__=='__main__':main()
