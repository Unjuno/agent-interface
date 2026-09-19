from fractions import Fraction as F
from itertools import product
import argparse,hashlib,json
from pathlib import Path
KINDS=('CACHED_COMPLETE','ACTIVE_JOB');TIME=tuple(F(i,2) for i in range(5));P=tuple(F(i,4) for i in range(5));COST=tuple(F(i) for i in range(3));OUT=('REUSE','DROP_EXPIRED','REBUILD_REQUIRED','CANCEL_STALE','CANCEL_TARDY','RUN','WAIT','TIE')
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def expected(p,g,w):
 r=p*w;q=(1-p)*g
 return 'RUN' if r<q else ('WAIT' if r>q else 'TIE')
def oracle(k,m,t,c,d,p,g,w):
 if k=='CACHED_COMPLETE':return 'REBUILD_REQUIRED' if not m else ('DROP_EXPIRED' if t>d else 'REUSE')
 if not m:return 'CANCEL_STALE'
 if t+c>d:return 'CANCEL_TARDY'
 return expected(p,g,w)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--result',required=True);ap.add_argument('--freeze',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();o=Path(a.output);assert not o.exists();R=json.loads(Path(a.result).read_text());FZ=json.loads(Path(a.freeze).read_text())
 rows=0;counts={x:0 for x in OUT};ireuse=irebuild=hover=smis=bypass=0
 for k,m,t,c,d,p,g,w in product(KINDS,(False,True),TIME,TIME,TIME,P,COST,COST):
  x=oracle(k,m,t,c,d,p,g,w);rows+=1;counts[x]+=1
  ireuse+=int(x=='REUSE' and not(k=='CACHED_COMPLETE' and m and t<=d));irebuild+=int(x=='REBUILD_REQUIRED' and not(k=='CACHED_COMPLETE' and not m));bypass+=int(k=='CACHED_COMPLETE' and not m and x in ('RUN','WAIT','TIE'))
  if k=='ACTIVE_JOB' and ((not m) or t+c>d):hover+=int(x in ('RUN','WAIT','TIE'))
  if k=='ACTIVE_JOB' and m and t+c<=d:smis+=int(x!=expected(p,g,w))
 checks={'decision':R['decision']=='PASS_EVIDENCE_COMPUTE_DECISION_LATTICE_SCOPED','rows':R['rows']==rows,'counts':R['decision_counts']==counts,'mismatch':R['candidate_oracle_mismatch']==0,'invalid_reuse':R['invalid_reuse']==ireuse==0,'invalid_rebuild':R['invalid_rebuild_required']==irebuild==0,'hard_override':R['hard_gate_override']==hover==0,'selector':R['active_selector_mismatch']==smis==0,'bypass':R['rebuild_direct_run_wait_bypass']==bypass==0,'unknown':R['unknown_dispositions']==0,'directed':all(R['directed_controls'].values()),'corruptions':all(R['corruption_controls'].values()),'formal':R['formal_invocations']==1 and R['reruns']==0 and R['replacements']==0 and R['tuning']==0,'source_plan':h('PLAN.md')==FZ['sha256']['PLAN.md'],'source_analyze':h('analyze.py')==FZ['sha256']['analyze.py'],'source_audit':h('audit.py')==FZ['sha256']['audit.py']}
 z={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'result_sha256':h(a.result),'freeze_sha256':h(a.freeze)};o.write_text(json.dumps(z,indent=2,sort_keys=True)+'\n');print(json.dumps(z,indent=2,sort_keys=True));raise SystemExit(0 if z['status']=='PASS' else 1)
if __name__=='__main__':main()
