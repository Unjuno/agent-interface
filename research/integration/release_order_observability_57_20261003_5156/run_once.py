"""One finite analytical invocation per fixed output; preserve all actual outcomes."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

HERE=Path(__file__).resolve().parent
PRIVATE=HERE.parents[3]/'release-order-originals'
def sha(data):return hashlib.sha256(data).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def capture(label,args,timeout=15):
    PRIVATE.mkdir(parents=True,exist_ok=True)
    for suffix in ('stdout','stderr','receipt.json'):
        if (PRIVATE/(label+'.'+suffix)).exists():raise FileExistsError('retained original already exists')
    argv=[sys.executable,'-B',*args];start=now();timed_out=False
    p=subprocess.Popen(argv,cwd=HERE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:stdout,stderr=p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out=True;p.kill();stdout,stderr=p.communicate()
    end=now()
    original={'label':label,'argv':argv,'cwd':str(HERE),'start_utc':start,'end_utc':end,
        'pid':p.pid,'exit_code':p.returncode,'timed_out':timed_out,
        'python':platform.python_version(),'platform':platform.platform(),
        'streams':{name:{'bytes':len(data),'sha256':sha(data)} for name,data in [('stdout',stdout),('stderr',stderr)]}}
    original_bytes=(json.dumps(original,indent=2)+'\n').encode()
    (PRIVATE/(label+'.receipt.json')).write_bytes(original_bytes)
    streams={}
    for name,data in [('stdout',stdout),('stderr',stderr)]:
        (PRIVATE/(label+'.'+name)).write_bytes(data)
        published=data.replace(str(HERE).encode(),b'<study>')
        (HERE/'run01'/(label+'.'+name+'.txt')).write_bytes(published)
        streams[name]={'original_bytes':len(data),'original_sha256':sha(data),
            'published_bytes':len(published),'published_sha256':sha(published),
            'derivation':'Replace exact private study prefix only; otherwise byte-identical'}
    public={'label':label,'argv':['<python>','-B',*args],'cwd':'<study>',
        'start_utc':start,'end_utc':end,'exit_code':p.returncode,'timed_out':timed_out,
        'python':original['python'],'platform':original['platform'],'streams':streams,
        'original_receipt_bytes':len(original_bytes),'original_receipt_sha256':sha(original_bytes),
        'derivation':'Actual original receipt retained privately; argv interpreter/cwd placeholders and pid omitted. Times/status/environment unchanged.'}
    (HERE/'run01'/(label+'.receipt.json')).write_text(json.dumps(public,indent=2)+'\n',encoding='utf8')
    return public

def main():
    run=HERE/'run01';run.mkdir(exist_ok=True)
    freeze=(HERE/'FREEZE.json').read_bytes()
    for name,expected in json.loads(freeze)['sha256'].items():
        if sha((HERE/name).read_bytes())!=expected:raise ValueError('frozen source mismatch '+name)
    commit=subprocess.run(['git','rev-parse','HEAD'],cwd=HERE,capture_output=True,check=True).stdout.decode().strip()
    with (run/'ATTEMPT.json').open('x',encoding='utf8') as stream:
        json.dump({'execution_id':'release-order-observability-57-A01-20261003',
            'start_utc':now(),'freeze_sha256':sha(freeze),'prospective_commit':commit,
            'scope':'finite native analytical construction; no formal/live allocation'},stream,indent=2)
        stream.write('\n')
    candidate=capture('candidate',['candidate.py','run01/raw.json'])
    auditor=capture('auditor',['audit.py','run01/raw.json','run01/audit.json'])
    receipt={'execution_id':'release-order-observability-57-A01-20261003',
        'candidate':candidate,'auditor':auditor,'candidate_invocations':1,'auditor_invocations':1,'retries':0,
        'end_utc':now(),'scope':'finite sequential/common-clock source construction; no operating backend/model/input'}
    (run/'RUN_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'candidate_exit':candidate['exit_code'],'auditor_exit':auditor['exit_code'],
        'candidate_timed_out':candidate['timed_out'],'auditor_timed_out':auditor['timed_out'],'retries':0}))
    return 0 if candidate['exit_code']==auditor['exit_code']==0 else 1

if __name__=='__main__':sys.exit(main())
