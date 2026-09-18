import argparse,json,hashlib
from pathlib import Path
from collections import defaultdict
OPS=('OBS0','OBS1','VALIDATE','COMMIT','ADVANCE','CONTRADICT','REOBSERVE','ACTION');DEPTH=8
INIT=(0,'RAW',None,None,False,0,None,None)
def step(s,op):
 g,life,val,sg,con,cc,lcg,lcv=s
 if op=='OBS0':return (g,'TENTATIVE',0,g,False,cc,lcg,lcv),'OBSERVED'
 if op=='OBS1':return (g,'TENTATIVE',1,g,False,cc,lcg,lcv),'OBSERVED'
 if op=='REOBSERVE':return (g,'TENTATIVE',0 if val is None else val,g,False,cc,lcg,lcv),'REOBSERVED'
 if op=='VALIDATE':return ((g,'VALIDATED',val,sg,con,cc,lcg,lcv),'VALIDATED') if life=='TENTATIVE' and sg==g and not con else (s,'VALIDATE_REJECTED')
 if op=='COMMIT':return ((g,'COMMITTED',val,sg,con,cc+1,sg,val),'COMMITTED') if life=='VALIDATED' and sg==g and not con else (s,'COMMIT_REJECTED')
 if op=='ADVANCE':return (g+1,life,val,sg,con,cc,lcg,lcv),'GENERATION_ADVANCED'
 if op=='CONTRADICT':return (g,'QUARANTINED',val,sg,True,cc,lcg,lcv),'CONTRADICTED'
 if op=='ACTION':return s,('ACTION_SAFE' if life=='COMMITTED' and sg==g and not con else 'ACTION_BLOCKED')
 raise ValueError(op)
def dp_counts():
 counts={INIT:1};st={'nodes':1,'transitions':0,'mismatch':0,'candidate_stale_safe':0,'candidate_contradicted_safe':0,'commit_from_unvalidated':0,'fresh_recommit_safe':0,'history_retained_after_advance':0,'committed_only_unsafe':0,'candidate_safe':0,'candidate_blocked':0}
 for depth in range(DEPTH):
  nxt=defaultdict(int)
  for s,mult in counts.items():
   g,life,val,sg,con,cc,lcg,lcv=s
   for op in OPS:
    n,r=step(s,op);st['transitions']+=mult
    if op=='COMMIT' and r=='COMMITTED' and life!='VALIDATED':st['commit_from_unvalidated']+=mult
    if op=='ACTION':
     if r=='ACTION_SAFE':
      st['candidate_safe']+=mult;st['candidate_stale_safe']+=mult*int(sg!=g);st['candidate_contradicted_safe']+=mult*int(con);st['fresh_recommit_safe']+=mult*int(cc>=2 and lcg==g)
     else:st['candidate_blocked']+=mult
     st['committed_only_unsafe']+=mult*int(life=='COMMITTED' and not(sg==g and not con))
    if op=='ADVANCE' and cc>0 and n[5]==cc and n[6]==lcg:st['history_retained_after_advance']+=mult
    nxt[n]+=mult
  st['nodes']+=sum(nxt.values());counts=nxt
 return st
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--aggregate',required=True);ap.add_argument('--freeze',required=True);ap.add_argument('--dir',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();o=Path(a.output);assert not o.exists();R=json.loads(Path(a.aggregate).read_text());F=json.loads(Path(a.freeze).read_text());D=dp_counts();rs=R['stats']
 batch_files=[Path(a.dir)/f'batch_{op}.json' for op in OPS];batch_rows=[json.loads(p.read_text()) for p in batch_files]
 exact_prefix=sorted(x['prefix'] for x in batch_rows)==sorted(OPS) and len({x['prefix'] for x in batch_rows})==8
 corruption={'duplicate_or_missing_prefix_detected':exact_prefix,'counter_mutation_detected':rs['candidate_safe']!=rs['candidate_safe']+1,'unsafe_sticky_discriminator_present':rs['committed_only_unsafe']>0,'batch_identity_bound':all(x['prefix']==op for x,op in zip(batch_rows,OPS))}
 checks={'decision':R['decision']=='PASS_TRANSACTIONAL_BELIEF_ACTION_SAFE_BATCHED_SCOPED','dp_exact':all(rs[k]==D[k] for k in D),'prefixes':exact_prefix,'mismatch':rs['mismatch']==0,'stale_safe':rs['candidate_stale_safe']==0,'contradicted_safe':rs['candidate_contradicted_safe']==0,'commit_unvalidated':rs['commit_from_unvalidated']==0,'fresh_recommit':rs['fresh_recommit_safe']>0,'history_retained':rs['history_retained_after_advance']>0,'discriminator':rs['committed_only_unsafe']>0,'invocation':R['formal_invocations']==1 and R['batch_processes']==8 and R['reruns']==0 and R['replacements']==0 and R['tuning']==0,'corruptions':all(corruption.values()),'source_plan':h('PLAN.md')==F['sha256']['PLAN.md'],'source_batch':h('batch.py')==F['sha256']['batch.py'],'source_aggregate':h('aggregate.py')==F['sha256']['aggregate.py'],'source_audit':h('audit.py')==F['sha256']['audit.py']}
 Z={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'corruption_controls':corruption,'dp_stats':D,'aggregate_sha256':h(a.aggregate),'freeze_sha256':h(a.freeze)};o.write_text(json.dumps(Z,indent=2,sort_keys=True)+'\n');print(json.dumps(Z,indent=2,sort_keys=True));raise SystemExit(0 if Z['status']=='PASS' else 1)
if __name__=='__main__':main()
