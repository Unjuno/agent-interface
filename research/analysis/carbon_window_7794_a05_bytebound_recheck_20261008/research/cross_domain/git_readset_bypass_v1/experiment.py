from __future__ import annotations
import argparse,json,subprocess,time
from pathlib import Path

def run(repo,*args,check=True):
    p=subprocess.run(args,cwd=repo,text=True,capture_output=True)
    if check and p.returncode: raise RuntimeError((args,p.returncode,p.stderr))
    return p

def git(repo,*args): return run(repo,'git',*args).stdout.strip()
def blob(repo,oid,path): return git(repo,'rev-parse',f'{oid}:{path}')
def direct_text(repo,oid,path): return git(repo,'show',f'{oid}:{path}').rstrip('\n')

def write(repo,declared,hidden,unrelated,effect):
    for p,v in [('declared.txt',declared),('hidden.txt',hidden),('unrelated.txt',unrelated),('effect.txt',effect)]: (repo/p).write_text(v+'\n')
    git(repo,'add','.')
def commit(repo,msg):
    git(repo,'-c','user.name=fixture','-c','user.email=fixture@example.invalid','commit','-m',msg); return git(repo,'rev-parse','HEAD')

class Tracer:
    def __init__(self,repo,oid): self.repo=repo; self.oid=oid; self.reads=[]
    def read(self,path):
        b=blob(self.repo,self.oid,path); v=direct_text(self.repo,self.oid,path); self.reads.append({'path':path,'blob_oid':b}); return v

def predicate(tracer,mode):
    d=tracer.read('declared.txt')
    h=tracer.read('hidden.txt') if mode=='all_traced' else direct_text(tracer.repo,tracer.oid,'hidden.txt')
    return d=='allow' and h=='allow'

def setup(root):
    repo=root/'repo'; repo.mkdir(); git(repo,'init','-q')
    write(repo,'allow','allow','u0','old'); A=commit(repo,'A')
    write(repo,'allow','allow','u0','B'); B=commit(repo,'B')
    git(repo,'checkout','-q','-b','fixtures',A)
    write(repo,'allow','deny','u0','old'); H=commit(repo,'H hidden changed')
    git(repo,'reset','--hard',A); write(repo,'allow','allow','u1','old'); U=commit(repo,'U unrelated changed')
    git(repo,'checkout','-q','-B','target',A); return repo,{'A':A,'B':B,'H':H,'U':U}

def one(c,out):
    out.mkdir(parents=True,exist_ok=False); repo,ids=setup(out); A,B,H,U=[ids[k] for k in ['A','B','H','U']]
    tr=Tracer(repo,A); assert predicate(tr,c['policy']); reads=tr.reads; planned=time.perf_counter_ns()
    if c['schedule']=='hidden_changed': git(repo,'update-ref','refs/heads/target',H,A)
    elif c['schedule']=='unrelated_changed': git(repo,'update-ref','refs/heads/target',U,A)
    elif c['schedule']!='stable': raise ValueError(c['schedule'])
    cur=git(repo,'rev-parse','refs/heads/target'); expected={x['path']:x['blob_oid'] for x in reads}; valid=True; checks=[]
    for path,b0 in expected.items():
        b=blob(repo,cur,path); ok=b==b0; valid &= ok; checks.append({'path':path,'expected_blob':b0,'current_blob':b,'equal':ok})
    delivered=time.perf_counter_ns()
    if valid:
        p=run(repo,'git','update-ref','refs/heads/target',B,cur,check=False); rc=p.returncode; err=p.stderr
    else: rc=97; err='read-set validation failed'
    finished=time.perf_counter_ns(); final=git(repo,'rev-parse','refs/heads/target')
    exp=B if c['schedule'] in ('stable','unrelated_changed') else H
    r={**c,**ids,'plan_read_set':reads,'validated_paths':[x['path'] for x in reads],'planned_ns':planned,'delivered_ns':delivered,'finished_ns':finished,'returncode':rc,'stderr':err,'final_target':final,'expected_final':exp,'ground_truth_correct':final==exp,'reflog':git(repo,'reflog','show','--format=%H%x09%gs','refs/heads/target').splitlines()}
    (out/'result.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n'); return r

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('plan',type=Path); ap.add_argument('out',type=Path); a=ap.parse_args(); plan=json.loads(a.plan.read_text()); a.out.mkdir(parents=True,exist_ok=True); rows=[]
    for c in plan['cases']: rows.append(one(c,a.out/c['id']))
    (a.out/'rows.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
if __name__=='__main__': main()
