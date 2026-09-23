from dataclasses import dataclass, replace
from typing import Optional
import argparse,json,hashlib
from pathlib import Path
OPS=('OBS0','OBS1','VALIDATE','COMMIT','ADVANCE','CONTRADICT','REOBSERVE','ACTION')
DEPTH=8
@dataclass(frozen=True)
class S:
 current_gen:int=0; lifecycle:str='RAW'; value:Optional[int]=None; support_gen:Optional[int]=None; contradicted:bool=False; commit_count:int=0; last_committed_gen:Optional[int]=None; last_committed_value:Optional[int]=None

def cand(s,op):
 if op=='OBS0':return replace(s,lifecycle='TENTATIVE',value=0,support_gen=s.current_gen,contradicted=False),'OBSERVED'
 if op=='OBS1':return replace(s,lifecycle='TENTATIVE',value=1,support_gen=s.current_gen,contradicted=False),'OBSERVED'
 if op=='REOBSERVE':return replace(s,lifecycle='TENTATIVE',value=0 if s.value is None else s.value,support_gen=s.current_gen,contradicted=False),'REOBSERVED'
 if op=='VALIDATE':return (replace(s,lifecycle='VALIDATED'),'VALIDATED') if s.lifecycle=='TENTATIVE' and s.support_gen==s.current_gen and not s.contradicted else (s,'VALIDATE_REJECTED')
 if op=='COMMIT':return (replace(s,lifecycle='COMMITTED',commit_count=s.commit_count+1,last_committed_gen=s.support_gen,last_committed_value=s.value),'COMMITTED') if s.lifecycle=='VALIDATED' and s.support_gen==s.current_gen and not s.contradicted else (s,'COMMIT_REJECTED')
 if op=='ADVANCE':return replace(s,current_gen=s.current_gen+1),'GENERATION_ADVANCED'
 if op=='CONTRADICT':return replace(s,lifecycle='QUARANTINED',contradicted=True),'CONTRADICTED'
 if op=='ACTION':return s,('ACTION_SAFE' if s.lifecycle=='COMMITTED' and s.support_gen==s.current_gen and not s.contradicted else 'ACTION_BLOCKED')
 raise ValueError(op)

def oracle(s,op):
 d=s.__dict__.copy()
 if op in ('OBS0','OBS1'):d.update(lifecycle='TENTATIVE',value=0 if op=='OBS0' else 1,support_gen=d['current_gen'],contradicted=False);r='OBSERVED'
 elif op=='REOBSERVE':d.update(lifecycle='TENTATIVE',value=0 if d['value'] is None else d['value'],support_gen=d['current_gen'],contradicted=False);r='REOBSERVED'
 elif op=='VALIDATE':
  if d['lifecycle']=='TENTATIVE' and d['support_gen']==d['current_gen'] and not d['contradicted']:d['lifecycle']='VALIDATED';r='VALIDATED'
  else:r='VALIDATE_REJECTED'
 elif op=='COMMIT':
  if d['lifecycle']=='VALIDATED' and d['support_gen']==d['current_gen'] and not d['contradicted']:d['lifecycle']='COMMITTED';d['commit_count']+=1;d['last_committed_gen']=d['support_gen'];d['last_committed_value']=d['value'];r='COMMITTED'
  else:r='COMMIT_REJECTED'
 elif op=='ADVANCE':d['current_gen']+=1;r='GENERATION_ADVANCED'
 elif op=='CONTRADICT':d['lifecycle']='QUARANTINED';d['contradicted']=True;r='CONTRADICTED'
 elif op=='ACTION':r='ACTION_SAFE' if d['lifecycle']=='COMMITTED' and d['support_gen']==d['current_gen'] and not d['contradicted'] else 'ACTION_BLOCKED'
 else:raise ValueError(op)
 return S(**d),r

def account(s,n,r,op,st):
 st['transitions']+=1
 if op=='COMMIT' and r=='COMMITTED' and s.lifecycle!='VALIDATED':st['commit_from_unvalidated']+=1
 if op=='ACTION':
  if r=='ACTION_SAFE':
   st['candidate_safe']+=1
   st['candidate_stale_safe']+=int(s.support_gen!=s.current_gen)
   st['candidate_contradicted_safe']+=int(s.contradicted)
   st['fresh_recommit_safe']+=int(s.commit_count>=2 and s.last_committed_gen==s.current_gen)
  else:st['candidate_blocked']+=1
  st['committed_only_unsafe']+=int(s.lifecycle=='COMMITTED' and not(s.support_gen==s.current_gen and not s.contradicted))
 if op=='ADVANCE' and s.commit_count>0 and n.commit_count==s.commit_count and n.last_committed_gen==s.last_committed_gen:st['history_retained_after_advance']+=1

def run(prefix,construction=False):
 depth=5 if construction else DEPTH
 st={'nodes':0,'transitions':0,'mismatch':0,'candidate_stale_safe':0,'candidate_contradicted_safe':0,'commit_from_unvalidated':0,'fresh_recommit_safe':0,'history_retained_after_advance':0,'committed_only_unsafe':0,'candidate_safe':0,'candidate_blocked':0}
 root=S(); sc,rc=cand(root,prefix);so,ro=oracle(root,prefix);account(root,sc,rc,prefix,st);st['mismatch']+=int(sc!=so or rc!=ro)
 def dfs(a,b,d):
  st['nodes']+=1
  if d==depth:return
  for op in OPS:
   na,ra=cand(a,op);nb,rb=oracle(b,op);account(a,na,ra,op,st);st['mismatch']+=int(na!=nb or ra!=rb);dfs(na,nb,d+1)
 dfs(sc,so,1)
 return {'prefix':prefix,'construction':construction,'depth':depth,'stats':st}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--prefix',choices=OPS,required=True);ap.add_argument('--construction',action='store_true');ap.add_argument('--output',required=True);a=ap.parse_args();p=Path(a.output);assert not p.exists();r=run(a.prefix,a.construction);r['digest']=hashlib.sha256(json.dumps(r,sort_keys=True,separators=(',',':')).encode()).hexdigest();p.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps({'prefix':a.prefix,'construction':a.construction,'stats':r['stats'],'digest':r['digest']},sort_keys=True))
if __name__=='__main__':main()
