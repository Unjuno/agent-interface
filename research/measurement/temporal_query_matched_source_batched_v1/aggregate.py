from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
import model
TASK='TEMPORAL-QUERY-MATCHED-SOURCE-COVERAGE-BATCHED-20260918-002';BATCH=11000;N=20
def main():
 ap=argparse.ArgumentParser();ap.add_argument('dir');ap.add_argument('--out',required=True);a=ap.parse_args();d=Path(a.dir);out=Path(a.out)
 if out.exists():raise FileExistsError(out)
 totals={"n":0,"mismatch":0,"future":0,"cross_scope":0,"budget":0,"authority":0,"fixed":0,"query":0};by={k:{"n":0,"fixed":0,"query":0} for k in model.CLASSES};manifest=[]
 for bi in range(N):
  p=d/f'BATCH_{bi:02d}.json'
  if not p.exists():raise RuntimeError('missing batch')
  raw=p.read_bytes();x=json.loads(raw);s=bi*BATCH
  if x.get('task')!=TASK or x.get('batch_index')!=bi or x.get('start')!=s or x.get('end')!=s+BATCH or x.get('invocation')!=1 or x.get('reruns')!=0:raise RuntimeError('batch metadata')
  for k in totals: totals[k]+=x['counters'][k]
  for cls in by:
   for k in by[cls]:by[cls][k]+=x['by_class'][cls][k]
  manifest.append({"batch":bi,"start":s,"end":s+BATCH,"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),"row_digest":x['row_digest']})
 if totals['n']!=220000:raise RuntimeError('count')
 fixed_rate=totals['fixed']/totals['n'];query_rate=totals['query']/totals['n'];delta_pp=(query_rate-fixed_rate)*100
 class_rates={}
 for cls,z in by.items():class_rates[cls]={"n":z['n'],"fixed_rate":z['fixed']/z['n'],"query_rate":z['query']/z['n'],"delta_pp":(z['query']-z['fixed'])*100/z['n']}
 worse=[cls for cls,z in class_rates.items() if z['query_rate']<z['fixed_rate']]
 r={"task":TASK,"formal_invocations":1,"batch_invocations":20,"batch_reruns":0,"total":totals['n'],"counters":totals,"fixed_rate":fixed_rate,"query_rate":query_rate,"delta_pp":delta_pp,"class_rates":class_rates,"query_worse_classes":worse,"manifest":manifest,"model_calls":0,"gui_actions":0,"task_input_actions":0}
 if any(totals[k] for k in ('mismatch','future','cross_scope','budget','authority')): decision='FAIL_LEAKAGE_OR_MISMATCH'
 elif worse: decision='FAIL_QUERY_CLASS_REGRESSION'
 elif delta_pp>=15: decision='PASS_MATCHED_SOURCE_TEMPORAL_QUERY_BATCHED_SCOPED'
 else: decision='HOLD_NO_SELECTION_DISCRIMINATOR'
 r['decision']=decision
 out.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ('manifest','class_rates')},indent=2,sort_keys=True));print(json.dumps(class_rates,indent=2,sort_keys=True))
if __name__=='__main__':main()
