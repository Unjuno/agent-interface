from __future__ import annotations
import argparse,json,subprocess,time
from pathlib import Path
REF='refs/heads/target'
def sh(repo:Path,*args,check=True,env=None):
 p=subprocess.run(args,cwd=repo,text=True,capture_output=True,env=env)
 if check and p.returncode: raise RuntimeError((args,p.returncode,p.stderr))
 return p
def make_commit(repo:Path,text,msg):
 (repo/'f').write_text(text+'\n'); sh(repo,'git','add','f'); sh(repo,'git','commit','-q','-m',msg); return sh(repo,'git','rev-parse','HEAD').stdout.strip()
def setup(repo:Path):
 repo.mkdir(parents=True); sh(repo,'git','init','-q'); sh(repo,'git','config','user.name','AI Test'); sh(repo,'git','config','user.email','ai@test.invalid'); sh(repo,'git','config','core.logAllRefUpdates','true')
 A=make_commit(repo,'same','A'); TA=sh(repo,'git','rev-parse',A+'^{tree}').stdout.strip()
 B=make_commit(repo,'desired','B')
 # create a different commit identity over the exact same tree
 p=subprocess.run(['git','commit-tree',TA,'-p',A],cwd=repo,text=True,input='semantic same\n',capture_output=True,check=True); C=p.stdout.strip()
 # D different tree, create through ordinary commit then remember OID
 D=make_commit(repo,'different','D')
 assert C!=A and sh(repo,'git','rev-parse',C+'^{tree}').stdout.strip()==TA
 assert sh(repo,'git','rev-parse',D+'^{tree}').stdout.strip()!=TA
 sh(repo,'git','update-ref','-m','fixture A',REF,A)
 return A,B,C,D,TA

def one(case,out):
 repo=out/'repo'; A,B,C,D,TA=setup(repo)
 if case['schedule']=='semantic_same': sh(repo,'git','update-ref','-m','replace same tree',REF,C)
 elif case['schedule']=='semantic_different': sh(repo,'git','update-ref','-m','replace different tree',REF,D)
 elif case['schedule']!='stable': raise ValueError(case['schedule'])
 before=sh(repo,'git','rev-parse',REF).stdout.strip(); start=time.perf_counter_ns(); checked=None; checked_tree=None
 if case['policy']=='exact_old':
  p=sh(repo,'git','update-ref','-m','delayed exact-old',REF,B,A,check=False); rc=p.returncode; stderr=p.stderr; decision='attempted'
 elif case['policy']=='tree_current_cas':
  checked=sh(repo,'git','rev-parse',REF).stdout.strip(); checked_tree=sh(repo,'git','rev-parse',checked+'^{tree}').stdout.strip()
  if checked_tree==TA:
   p=sh(repo,'git','update-ref','-m','delayed tree-current-cas',REF,B,checked,check=False); rc=p.returncode; stderr=p.stderr; decision='attempted'
  else:
   rc=None; stderr=''; decision='predicate_reject'
 else: raise ValueError(case['policy'])
 end=time.perf_counter_ns(); final=sh(repo,'git','rev-parse',REF).stdout.strip(); reflog=sh(repo,'git','reflog','show','--format=%H%x09%gs',REF).stdout.splitlines()
 ground=B if case['schedule'] in ('stable','semantic_same') else D
 correct=(final==ground)
 r={**case,'A':A,'B':B,'C':C,'D':D,'A_tree':TA,'before':before,'checked_oid':checked,'checked_tree':checked_tree,'decision':decision,'returncode':rc,'stderr':stderr,'final':final,'ground':ground,'correct':correct,'start_ns':start,'end_ns':end,'reflog':reflog}
 (out/'result.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n'); return r

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--plan',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args(); plan=json.loads(a.plan.read_text());a.out.mkdir(parents=True,exist_ok=False);rows=[]
 for c in plan['cases']:
  d=a.out/c['id'];d.mkdir();r=one(c,d);rows.append(r);print(json.dumps({'id':r['id'],'correct':r['correct'],'decision':r['decision']}),flush=True)
  if c['policy']=='tree_current_cas' and not r['correct']: raise SystemExit('candidate failure '+c['id'])
 (a.out/'rows.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
if __name__=='__main__':main()
