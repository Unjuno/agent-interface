from itertools import product
import argparse,hashlib,json
from pathlib import Path
KINDS=('LOCAL_COMPLETE','OPAQUE_SEMANTIC')
def oracle(pc,k,lt,fs,av,e):
 if pc:return ('KEEP_ACTION_SAFE',None)
 if k=='LOCAL_COMPLETE':return ('RECOMMIT_LOCAL',e+1) if lt else ('REJECT',None)
 if fs and av:return ('RECOMMIT_REUSED_APPROVAL',e+1)
 return ('YIELD_FOR_APPROVAL',None)
def counts():
 s={'rows':0,'mismatch':0,'current_path_keep':0,'stale_path_keep':0,'local_recommit':0,'local_reject':0,'opaque_recommit':0,'opaque_yield':0,'bad_recommit_epoch':0,'sticky_unsafe':0,'current_truth_auto_unsafe':0,'always_yield_false_yield':0,'reuse_old_epoch_violations':0}
 for pc,k,lt,fs,av,e in product((False,True),KINDS,(False,True),(False,True),(False,True),(1,2)):
  d,ne=oracle(pc,k,lt,fs,av,e);s['rows']+=1
  if pc:s['current_path_keep']+=int(d=='KEEP_ACTION_SAFE')
  else:s['stale_path_keep']+=int(d=='KEEP_ACTION_SAFE')
  if not pc and k=='LOCAL_COMPLETE':s['local_recommit']+=int(d=='RECOMMIT_LOCAL');s['local_reject']+=int(d=='REJECT')
  if not pc and k=='OPAQUE_SEMANTIC':s['opaque_recommit']+=int(d=='RECOMMIT_REUSED_APPROVAL');s['opaque_yield']+=int(d=='YIELD_FOR_APPROVAL')
  if d.startswith('RECOMMIT'):s['bad_recommit_epoch']+=int(ne is None or ne<=e);s['reuse_old_epoch_violations']+=1
  if not pc:s['sticky_unsafe']+=1
  if not pc and k=='OPAQUE_SEMANTIC' and not fs and lt:s['current_truth_auto_unsafe']+=1
  if not pc and d in ('RECOMMIT_LOCAL','RECOMMIT_REUSED_APPROVAL'):s['always_yield_false_yield']+=1
 return s
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--result',required=True);ap.add_argument('--freeze',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();o=Path(a.output);assert not o.exists();R=json.loads(Path(a.result).read_text());F=json.loads(Path(a.freeze).read_text());S=counts();checks={'decision':R['decision']=='PASS_BELIEF_REPAIR_DECISION_LATTICE_SCOPED','stats':R['stats']==S,'mismatch':R['stats']['mismatch']==0,'current_keep':R['stats']['current_path_keep']>0,'stale_keep_zero':R['stats']['stale_path_keep']==0,'local':R['stats']['local_recommit']>0 and R['stats']['local_reject']>0,'opaque':R['stats']['opaque_recommit']>0 and R['stats']['opaque_yield']>0,'epoch':R['stats']['bad_recommit_epoch']==0,'comparators':R['stats']['sticky_unsafe']>0 and R['stats']['current_truth_auto_unsafe']>0 and R['stats']['always_yield_false_yield']>0 and R['stats']['reuse_old_epoch_violations']>0,'directed':all(R['directed'].values()),'corruptions':all(R['corruptions'].values()),'formal':R['formal_invocations']==1 and R['reruns']==0 and R['replacements']==0 and R['tuning']==0,'source_plan':h('PLAN.md')==F['sha256']['PLAN.md'],'source_formal':h('formal.py')==F['sha256']['formal.py'],'source_audit':h('audit.py')==F['sha256']['audit.py']};Z={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'audit_stats':S,'result_sha256':h(a.result),'freeze_sha256':h(a.freeze)};o.write_text(json.dumps(Z,indent=2,sort_keys=True)+'\n');print(json.dumps(Z,indent=2,sort_keys=True));raise SystemExit(0 if Z['status']=='PASS' else 1)
if __name__=='__main__':main()
