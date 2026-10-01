from __future__ import annotations
import hashlib,json,os,subprocess
from pathlib import Path
from multiprocessing import Barrier, Process, Queue
ZERO='0'*40

def task_ref(task_id:str)->str:
    return 'refs/experiment-claims/'+hashlib.sha256(task_id.encode()).hexdigest()

def claim_bytes(task_id,worker_id,base_sha,nonce):
    return (json.dumps({'base_sha':base_sha,'nonce':nonce,'task_id':task_id,'worker_id':worker_id},sort_keys=True,separators=(',',':'))+'\n').encode()

def git(repo,*args,input_bytes=None,check=True):
    cp=subprocess.run(['git','--git-dir',str(repo),*args],input=input_bytes,capture_output=True)
    if check and cp.returncode: raise RuntimeError(cp.stderr.decode(errors='replace'))
    return cp

def init_repo(path:Path):
    subprocess.run(['git','init','--bare',str(path)],check=True,capture_output=True)

def worker(repo,log_path,policy,task_id,worker_id,base_sha,nonce,barrier,q):
    ref=task_ref(task_id)
    pre_unclaimed=(git(repo,'show-ref','--verify','--quiet',ref,check=False).returncode!=0)
    b=claim_bytes(task_id,worker_id,base_sha,nonce)
    oid=git(repo,'hash-object','-w','--stdin',input_bytes=b).stdout.decode().strip()
    barrier.wait()
    if policy=='READ_APPEND':
        fd=os.open(log_path,os.O_WRONLY|os.O_CREAT|os.O_APPEND,0o644)
        os.write(fd,b); os.close(fd); owner=True; rc=0
    elif policy=='TASK_REF_CAS':
        cp=git(repo,'update-ref',ref,oid,ZERO,check=False); owner=(cp.returncode==0); rc=cp.returncode
    else: raise ValueError(policy)
    q.put({'worker_id':worker_id,'pre_unclaimed':pre_unclaimed,'claim_oid':oid,'owner':owner,'cas_returncode':rc})

def run_same_task_case(root:Path,case_id:str,policy:str,n:int,task_id:str,base_sha:str):
    repo=root/case_id/'repo.git'; repo.parent.mkdir(parents=True); init_repo(repo); log=repo.parent/'claims.log'
    barrier=Barrier(n); q=Queue(); ps=[]
    for i in range(n):
        wid=f'w{i}'; nonce=f'{case_id}-nonce-{i}'
        p=Process(target=worker,args=(repo,log,policy,task_id,wid,base_sha,nonce,barrier,q)); p.start(); ps.append(p)
    rows=[q.get(timeout=10) for _ in range(n)]
    for p in ps: p.join(10); assert p.exitcode==0
    ref=task_ref(task_id); final_oid=None; final_obj=None
    cp=git(repo,'rev-parse',ref,check=False)
    if cp.returncode==0:
        final_oid=cp.stdout.decode().strip(); final_obj=json.loads(git(repo,'cat-file','blob',final_oid).stdout)
    if policy=='TASK_REF_CAS':
        for row in rows:
            if not row['owner']:
                row['resolved_winner_oid']=final_oid
                row['resolved_winner']=final_obj
    return {'case_id':case_id,'policy':policy,'contenders':n,'task_id':task_id,'task_ref':ref,'rows':sorted(rows,key=lambda r:r['worker_id']),'owner_count':sum(r['owner'] for r in rows),'final_oid':final_oid,'final_object':final_obj,'append_log_lines':log.read_text().splitlines() if log.exists() else []}

def run_distinct_tasks_case(root:Path,case_id:str,n:int,base_sha:str):
    repo=root/case_id/'repo.git'; repo.parent.mkdir(parents=True); init_repo(repo); barrier=Barrier(n); q=Queue(); ps=[]
    tasks=[]
    for i in range(n):
        tid=f'{case_id}-task-{i}'; tasks.append(tid); wid=f'w{i}'; nonce=f'{case_id}-nonce-{i}'
        p=Process(target=worker,args=(repo,repo.parent/'unused.log','TASK_REF_CAS',tid,wid,base_sha,nonce,barrier,q)); p.start(); ps.append(p)
    rows=[q.get(timeout=10) for _ in range(n)]
    for p in ps:p.join(10);assert p.exitcode==0
    resolved=[]
    for tid in tasks:
        oid=git(repo,'rev-parse',task_ref(tid)).stdout.decode().strip(); obj=json.loads(git(repo,'cat-file','blob',oid).stdout); resolved.append({'task_id':tid,'oid':oid,'object':obj})
    return {'case_id':case_id,'tasks':tasks,'rows':sorted(rows,key=lambda r:r['worker_id']),'owner_count':sum(r['owner'] for r in rows),'resolved':resolved}
