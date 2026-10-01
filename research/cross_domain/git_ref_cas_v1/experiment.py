from __future__ import annotations
import argparse, json, subprocess, time
from pathlib import Path

REF='refs/heads/target'; OTHER='refs/heads/unrelated'

def sh(repo:Path,*args:str,check=True):
    p=subprocess.run(args,cwd=repo,text=True,capture_output=True)
    if check and p.returncode:
        raise RuntimeError({'args':args,'rc':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
    return p

def commit(repo:Path, text:str, msg:str)->str:
    (repo/'payload.txt').write_text(text+'\n',encoding='utf-8')
    sh(repo,'git','add','payload.txt')
    sh(repo,'git','commit','-q','-m',msg)
    return sh(repo,'git','rev-parse','HEAD').stdout.strip()

def setup_repo(repo:Path):
    repo.mkdir(parents=True)
    sh(repo,'git','init','-q')
    sh(repo,'git','config','user.name','Agent Interface Experiment')
    sh(repo,'git','config','user.email','experiment@example.invalid')
    sh(repo,'git','config','core.logAllRefUpdates','true')
    A=commit(repo,'A','A')
    B=commit(repo,'B','B')
    C=commit(repo,'C','C')
    sh(repo,'git','update-ref','-m','fixture target A',REF,A)
    sh(repo,'git','update-ref','-m','fixture unrelated A',OTHER,A)
    return A,B,C

def one(case:dict,out:Path)->dict:
    repo=out/'repo'; A,B,C=setup_repo(repo)
    planned_ns=time.perf_counter_ns()
    target_plan=sh(repo,'git','rev-parse',REF).stdout.strip()
    assert target_plan==A
    if case['schedule']=='target_changed':
        sh(repo,'git','update-ref','-m','intervening target C',REF,C)
    elif case['schedule']=='unrelated_changed':
        sh(repo,'git','update-ref','-m','intervening unrelated C',OTHER,C)
    elif case['schedule']!='stable':
        raise ValueError(case['schedule'])
    pre_target=sh(repo,'git','rev-parse',REF).stdout.strip()
    pre_other=sh(repo,'git','rev-parse',OTHER).stdout.strip()
    delivered_ns=time.perf_counter_ns()
    if case['policy']=='naive':
        p=sh(repo,'git','update-ref','-m','delayed B naive',REF,B,check=False)
    elif case['policy']=='cas':
        p=sh(repo,'git','update-ref','-m','delayed B cas',REF,B,A,check=False)
    else: raise ValueError(case['policy'])
    finished_ns=time.perf_counter_ns()
    final_target=sh(repo,'git','rev-parse',REF).stdout.strip()
    final_other=sh(repo,'git','rev-parse',OTHER).stdout.strip()
    reflog=sh(repo,'git','reflog','show','--format=%H%x09%gs',REF).stdout.splitlines()
    expected_final=C if case['schedule']=='target_changed' else B
    expected_rc_nonzero=(case['policy']=='cas' and case['schedule']=='target_changed')
    correct=(final_target==expected_final and ((p.returncode!=0)==expected_rc_nonzero))
    row={**case,'A':A,'B':B,'C':C,'planned_ns':planned_ns,'delivered_ns':delivered_ns,'finished_ns':finished_ns,
         'pre_target':pre_target,'pre_other':pre_other,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr,
         'final_target':final_target,'final_other':final_other,'expected_final':expected_final,'correct':correct,'reflog':reflog}
    (out/'result.json').write_text(json.dumps(row,indent=2,sort_keys=True)+'\n')
    return row

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--plan',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    plan=json.loads(a.plan.read_text())
    a.out.mkdir(parents=True,exist_ok=False)
    rows=[]
    for case in plan['cases']:
        d=a.out/case['id']; d.mkdir()
        row=one(case,d); rows.append(row)
        print(json.dumps({'id':row['id'],'correct':row['correct'],'rc':row['returncode'],'final':row['final_target'][:8]}),flush=True)
        if not row['correct'] and row['policy']=='cas':
            raise SystemExit(f"candidate integrity failure {row['id']}")
    (a.out/'rows.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
if __name__=='__main__': main()
