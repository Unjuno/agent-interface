import argparse,json,hashlib
from pathlib import Path
OPS=('OBS0','OBS1','VALIDATE','COMMIT','ADVANCE','CONTRADICT','REOBSERVE','ACTION')
DEPTH=8
INIT=(0,'RAW',None,None,False,0,None,None)
def step(s,op):
 g,life,val,sg,con,cc,lcg,lcv=s
 if op=='OBS0': return (g,'TENTATIVE',0,g,False,cc,lcg,lcv),'OBSERVED'
 if op=='OBS1': return (g,'TENTATIVE',1,g,False,cc,lcg,lcv),'OBSERVED'
 if op=='REOBSERVE': return (g,'TENTATIVE',0 if val is None else val,g,False,cc,lcg,lcv),'REOBSERVED'
 if op=='VALIDATE':
  return ((g,'VALIDATED',val,sg,con,cc,lcg,lcv),'VALIDATED') if life=='TENTATIVE' and sg==g and not con else (s,'VALIDATE_REJECTED')
 if op=='COMMIT':
  return ((g,'COMMITTED',val,sg,con,cc+1,sg,val),'COMMITTED') if life=='VALIDATED' and sg==g and not con else (s,'COMMIT_REJECTED')
 if op=='ADVANCE': return (g+1,life,val,sg,con,cc,lcg,lcv),'GENERATION_ADVANCED'
 if op=='CONTRADICT': return (g,'QUARANTINED',val,sg,True,cc,lcg,lcv),'CONTRADICTED'
 if op=='ACTION': return s,('ACTION_SAFE' if life=='COMMITTED' and sg==g and not con else 'ACTION_BLOCKED')
 raise ValueError(op)
def enumerate_counts():
 st={'nodes':0,'transitions':0,'candidate_stale_safe':0,'candidate_contradicted_safe':0,'commit_from_unvalidated':0,'fresh_recommit_safe':0,'history_retained_after_advance':0,'committed_only_unsafe':0,'candidate_safe':0,'candidate_blocked':0}
 def dfs(s,d):
  st['nodes']+=1
  if d==DEPTH:return
  for op in OPS:
   n,r=step(s,op);st['transitions']+=1
   g,life,val,sg,con,cc,lcg,lcv=s
   if op=='COMMIT' and r=='COMMITTED' and life!='VALIDATED':st['commit_from_unvalidated']+=1
   if op=='ACTION':
    if r=='ACTION_SAFE':
     st['candidate_safe']+=1
     if sg!=g:st['candidate_stale_safe']+=1
     if con:st['candidate_contradicted_safe']+=1
     if cc>=2 and lcg==g:st['fresh_recommit_safe']+=1
    else:st['candidate_blocked']+=1
    if life=='COMMITTED' and not(sg==g and not con):st['committed_only_unsafe']+=1
   if op=='ADVANCE' and cc>0 and n[5]==cc and n[6]==lcg:st['history_retained_after_advance']+=1
   dfs(n,d+1)
 dfs(INIT,0);return st
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--result',required=True);ap.add_argument('--freeze',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();o=Path(a.output);assert not o.exists();R=json.loads(Path(a.result).read_text());F=json.loads(Path(a.freeze).read_text());S=enumerate_counts();rs=R['stats']
 checks={'decision':R['decision']=='PASS_TRANSACTIONAL_BELIEF_ACTION_SAFE_SCOPED','depth':R['depth']==8,'nodes':rs['nodes']==S['nodes'],'transitions':rs['transitions']==S['transitions'],'mismatch':rs['mismatch']==0,'stale_safe':rs['candidate_stale_safe']==S['candidate_stale_safe']==0,'contradicted_safe':rs['candidate_contradicted_safe']==S['candidate_contradicted_safe']==0,'commit_unvalidated':rs['commit_from_unvalidated']==S['commit_from_unvalidated']==0,'fresh_recommit':rs['fresh_recommit_safe']==S['fresh_recommit_safe'] and S['fresh_recommit_safe']>0,'history_retained':rs['history_retained_after_advance']==S['history_retained_after_advance'] and S['history_retained_after_advance']>0,'discriminator':rs['committed_only_unsafe']==S['committed_only_unsafe'] and S['committed_only_unsafe']>0,'formal':R['formal_invocations']==1 and R['reruns']==0 and R['replacements']==0 and R['tuning']==0,'directed':all(R['directed'].values()),'corruptions':all(R['corruptions'].values()),'source_plan':h('PLAN.md')==F['sha256']['PLAN.md'],'source_formal':h('formal.py')==F['sha256']['formal.py'],'source_audit':h('audit.py')==F['sha256']['audit.py']}
 Z={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'result_sha256':h(a.result),'freeze_sha256':h(a.freeze)};o.write_text(json.dumps(Z,indent=2,sort_keys=True)+'\n');print(json.dumps(Z,indent=2,sort_keys=True));raise SystemExit(0 if Z['status']=='PASS' else 1)
if __name__=='__main__':main()
