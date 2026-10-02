"""Offline source/process/raw verification only; never runs native or GUI code."""
from pathlib import Path
import hashlib,json,subprocess,sys,os
from audit import audit,check
HERE=Path(__file__).resolve().parent

def verify():
    freeze=json.loads((HERE/'FREEZE.json').read_text())
    for name,sha in freeze['files'].items():check(hashlib.sha256((HERE/name).read_bytes()).hexdigest()==sha,'source hash '+name)
    root=HERE/'formal';last=0
    for i in range(5):
        x=json.loads((root/f'batch{i}.exit.json').read_text());srv=json.loads((root/f'batch{i}'/'SERVER.json').read_text())
        check(type(x['returncode']) is int and x['returncode']==0,'outer exit')
        check(x['before_ns']>=last and x['before_ns']<=srv['before_ns']<srv['after_ns']<=x['after_ns'],'batch chronology')
        check(x['argv'][-2:]==[str(i),'32'] and Path(x['argv'][2]).name=='run.py','batch command')
        for ext in ('stdout','stderr'):
            data=(root/f'batch{i}.{ext}').read_bytes();check(hashlib.sha256(data).hexdigest()==x[ext+'_sha256'],'outer '+ext)
            check(not data,'unexpected outer output')
        check((root/f'batch{i}.consumed').exists(),'consumed marker');last=x['after_ns']
    result=audit(root,range(5),32)
    check(result==json.loads((HERE/'AUDIT.json').read_text()),'retained audit parity')
    env=dict(os.environ,EVIDENCE_BLOCK=str(root/'batch0'),PYTHONDONTWRITEBYTECODE='1')
    t=subprocess.run([sys.executable,'-B','-m','unittest','-v','test_audit'],cwd=HERE,env=env,capture_output=True,timeout=10)
    check(t.returncode==0,'semantic controls')
    return dict(status='PASS_OFFLINE_VERIFICATION',blocks=result['blocks'],timed_samples=result['timed_samples'],warmups=result['warmups'],semantic_controls=12,formal_reruns=0)
if __name__=='__main__':print(json.dumps(verify(),sort_keys=True))
