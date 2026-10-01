from __future__ import annotations
import argparse,hashlib,json,os,tempfile
from pathlib import Path
from common import run_session,evaluate,TASK as PARENT_TASK
TASK='MULTI-APP-GUARDED-RECOVERY-R3-DURABLE-A2-20260918-004'
PARENT_COMMON_SHA256='64fe895362ceb1bd5b66fafb64460b6ffa5ce14cc06d371d76a46b6380582cdb'

def atomic_json(path,obj):
    path=Path(path)
    if path.exists(): raise RuntimeError('output_exists:'+str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    data=(json.dumps(obj,indent=2,sort_keys=True)+'\n').encode()
    fd,tmp=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f:
            f.write(data); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
    return hashlib.sha256(data).hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--session',type=int,choices=(1,2,3,4),required=True);p.add_argument('--out',required=True);a=p.parse_args()
    row=run_session(a.session); errors=evaluate(row); row['errors']=errors; row['pass']=not errors
    row_bytes=(json.dumps(row,sort_keys=True,separators=(',',':'))+'\n').encode()
    env={'schema':'multi-app-guarded-recovery-r3-durable-batch-v1','task':TASK,'parent_science_task':PARENT_TASK,'parent_common_sha256':PARENT_COMMON_SHA256,'session_id':a.session,'batch_invocations':1,'reruns':0,'replacements':0,'tuning':0,'row_sha256':hashlib.sha256(row_bytes).hexdigest(),'row':row}
    digest=atomic_json(a.out,env)
    print(json.dumps({'session':a.session,'pass':env['row']['pass'],'errors':errors,'batch_file_sha256':digest},sort_keys=True),flush=True)
    raise SystemExit(0 if not errors else 2)
if __name__=='__main__':main()
