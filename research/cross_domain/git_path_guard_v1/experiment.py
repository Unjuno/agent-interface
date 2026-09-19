from __future__ import annotations
import argparse, json, subprocess, time
from pathlib import Path
from typing import Callable

TARGET='refs/heads/target'

def run(repo:Path,*args:str,check:bool=True):
    p=subprocess.run(args,cwd=repo,text=True,capture_output=True)
    if check and p.returncode:
        raise RuntimeError((args,p.returncode,p.stderr))
    return p

def git(repo:Path,*args:str)->str:
    return run(repo,'git',*args).stdout.strip()

def commit_file(repo:Path, path:str, content:str, msg:str)->str:
    (repo/path).write_text(content)
    run(repo,'git','add',path)
    run(repo,'git','commit','-q','-m',msg)
    return git(repo,'rev-parse','HEAD')

def setup_repo(repo:Path):
    repo.mkdir(parents=True)
    run(repo,'git','init','-q')
    run(repo,'git','config','user.email','fixture@example.invalid')
    run(repo,'git','config','user.name','Fixture')
    (repo/'dependency.txt').write_text('allow=v1\n')
    (repo/'unrelated.txt').write_text('note=u0\n')
    (repo/'effect.txt').write_text('effect=base\n')
    run(repo,'git','add','.')
    run(repo,'git','commit','-q','-m','A')
    A=git(repo,'rev-parse','HEAD')
    # B is the desired delayed effect, based on A.
    B=commit_file(repo,'effect.txt','effect=B\n','B desired')
    run(repo,'git','reset','--hard','-q',A)
    C=commit_file(repo,'unrelated.txt','note=u1\n','C unrelated')
    run(repo,'git','reset','--hard','-q',A)
    D=commit_file(repo,'dependency.txt','allow=v2\n','D dependency')
    run(repo,'git','reset','--hard','-q',A)
    git(repo,'update-ref',TARGET,A)
    return A,B,C,D

def oid(repo:Path, ref:str)->str:
    return git(repo,'rev-parse',ref)

def tree(repo:Path, commit:str)->str:
    return git(repo,'rev-parse',f'{commit}^{{tree}}')

def dep_blob(repo:Path, commit:str)->str:
    return git(repo,'rev-parse',f'{commit}:dependency.txt')

def deliver(repo:Path, policy:str, A:str, B:str, before_cas:Callable[[str],None]|None=None):
    X=oid(repo,TARGET)
    if policy=='tree_current_cas':
        valid=tree(repo,X)==tree(repo,A)
    elif policy=='path_current_cas':
        valid=dep_blob(repo,X)==dep_blob(repo,A)
    else:
        raise ValueError(policy)
    if not valid:
        return {'returncode':3,'stderr':'predicate mismatch','observed_oid':X,'predicate_valid':False}
    if before_cas is not None:
        before_cas(X)
    p=run(repo,'git','update-ref',TARGET,B,X,check=False)
    return {'returncode':p.returncode,'stderr':p.stderr.strip(),'observed_oid':X,'predicate_valid':True}

def one(case:dict,out:Path):
    if out.exists() and any(out.iterdir()):
        raise RuntimeError(f'refuse existing output {out}')
    out.mkdir(parents=True,exist_ok=True)
    repo=out/'repo'
    A,B,C,D=setup_repo(repo)
    planned_ns=time.monotonic_ns()
    schedule=case['schedule']
    if schedule=='stable': current=A
    elif schedule=='unrelated_changed': current=C
    elif schedule=='dependency_changed': current=D
    else: raise ValueError(schedule)
    git(repo,'update-ref',TARGET,current,A)
    delivered_ns=time.monotonic_ns()
    d=deliver(repo,case['policy'],A,B)
    finished_ns=time.monotonic_ns()
    final=oid(repo,TARGET)
    ground=B if schedule in ('stable','unrelated_changed') else D
    row={**case,'A':A,'B':B,'C':C,'D':D,'A_tree':tree(repo,A),'C_tree':tree(repo,C),'D_tree':tree(repo,D),
         'A_dep_blob':dep_blob(repo,A),'C_dep_blob':dep_blob(repo,C),'D_dep_blob':dep_blob(repo,D),
         **d,'planned_ns':planned_ns,'delivered_ns':delivered_ns,'finished_ns':finished_ns,
         'final_target':final,'ground_truth_final':ground,'ground_truth_correct':final==ground,
         'reflog':git(repo,'reflog','show','--format=%H%x09%gs',TARGET).splitlines()}
    (out/'result.json').write_text(json.dumps(row,indent=2,sort_keys=True)+'\n')
    return row

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--plan',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    plan=json.loads(a.plan.read_text())
    a.out.mkdir(parents=True,exist_ok=True)
    rows=[]
    for case in plan['cases']:
        d=a.out/case['id']
        rows.append(one(case,d))
    print(json.dumps({'cases':len(rows),'correct':sum(r['ground_truth_correct'] for r in rows)},sort_keys=True))
if __name__=='__main__': main()
