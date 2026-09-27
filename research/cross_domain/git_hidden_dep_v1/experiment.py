from __future__ import annotations
import argparse,json,subprocess,time
from pathlib import Path
from typing import Callable
TARGET='refs/heads/target'

def run(repo:Path,*args:str,check:bool=True):
    p=subprocess.run(args,cwd=repo,text=True,capture_output=True)
    if check and p.returncode: raise RuntimeError((args,p.returncode,p.stderr))
    return p

def git(repo:Path,*args:str)->str: return run(repo,'git',*args).stdout.strip()
def oid(repo:Path,ref:str)->str: return git(repo,'rev-parse',ref)
def blob(repo:Path,commit:str,path:str)->str: return git(repo,'rev-parse',f'{commit}:{path}')

def commit_file(repo:Path,path:str,content:str,msg:str)->str:
    (repo/path).write_text(content); run(repo,'git','add',path); run(repo,'git','commit','-q','-m',msg); return oid(repo,'HEAD')

def setup_repo(repo:Path):
    repo.mkdir(parents=True); run(repo,'git','init','-q'); run(repo,'git','config','user.email','fixture@example.invalid'); run(repo,'git','config','user.name','Fixture')
    for p,c in [('declared.txt','declared=v1\n'),('hidden.txt','hidden=v1\n'),('unrelated.txt','u0\n'),('effect.txt','base\n')]: (repo/p).write_text(c)
    run(repo,'git','add','.'); run(repo,'git','commit','-q','-m','A'); A=oid(repo,'HEAD')
    B=commit_file(repo,'effect.txt','B\n','B desired')
    run(repo,'git','reset','--hard','-q',A); C=commit_file(repo,'declared.txt','declared=v2\n','C declared changed')
    run(repo,'git','reset','--hard','-q',A); D=commit_file(repo,'hidden.txt','hidden=v2\n','D hidden changed')
    run(repo,'git','reset','--hard','-q',A); E=commit_file(repo,'unrelated.txt','u1\n','E unrelated changed')
    run(repo,'git','reset','--hard','-q',A); git(repo,'update-ref',TARGET,A)
    return A,B,C,D,E

def deliver(repo:Path,policy:str,A:str,B:str,before_cas:Callable[[str],None]|None=None):
    X=oid(repo,TARGET)
    declared_ok=blob(repo,X,'declared.txt')==blob(repo,A,'declared.txt')
    hidden_ok=blob(repo,X,'hidden.txt')==blob(repo,A,'hidden.txt')
    if policy=='declared_only': valid=declared_ok
    elif policy=='complete_two_path': valid=declared_ok and hidden_ok
    else: raise ValueError(policy)
    if not valid: return {'returncode':3,'stderr':'predicate mismatch','observed_oid':X,'declared_ok':declared_ok,'hidden_ok':hidden_ok,'predicate_valid':False}
    if before_cas: before_cas(X)
    p=run(repo,'git','update-ref',TARGET,B,X,check=False)
    return {'returncode':p.returncode,'stderr':p.stderr.strip(),'observed_oid':X,'declared_ok':declared_ok,'hidden_ok':hidden_ok,'predicate_valid':True}

def one(case:dict,out:Path):
    if out.exists() and any(out.iterdir()): raise RuntimeError(f'refuse existing {out}')
    out.mkdir(parents=True,exist_ok=True); repo=out/'repo'; A,B,C,D,E=setup_repo(repo)
    planned_ns=time.monotonic_ns(); s=case['schedule']; current={'stable':A,'declared_changed':C,'hidden_changed':D,'unrelated_changed':E}[s]
    git(repo,'update-ref',TARGET,current,A); delivered_ns=time.monotonic_ns(); d=deliver(repo,case['policy'],A,B); finished_ns=time.monotonic_ns(); final=oid(repo,TARGET)
    ground=B if s in ('stable','unrelated_changed') else current
    row={**case,'A':A,'B':B,'C':C,'D':D,'E':E,
         'A_declared':blob(repo,A,'declared.txt'),'C_declared':blob(repo,C,'declared.txt'),'D_declared':blob(repo,D,'declared.txt'),'E_declared':blob(repo,E,'declared.txt'),
         'A_hidden':blob(repo,A,'hidden.txt'),'C_hidden':blob(repo,C,'hidden.txt'),'D_hidden':blob(repo,D,'hidden.txt'),'E_hidden':blob(repo,E,'hidden.txt'),
         **d,'planned_ns':planned_ns,'delivered_ns':delivered_ns,'finished_ns':finished_ns,'final_target':final,'ground_truth_final':ground,'ground_truth_correct':final==ground,
         'reflog':git(repo,'reflog','show','--format=%H%x09%gs',TARGET).splitlines()}
    (out/'result.json').write_text(json.dumps(row,indent=2,sort_keys=True)+'\n'); return row

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--plan',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); plan=json.loads(a.plan.read_text()); a.out.mkdir(parents=True,exist_ok=True)
    rows=[one(c,a.out/c['id']) for c in plan['cases']]; print(json.dumps({'cases':len(rows),'correct':sum(r['ground_truth_correct'] for r in rows)},sort_keys=True))
if __name__=='__main__': main()
