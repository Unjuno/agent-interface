"""One-shot comparative custody runner, with exact first native streams."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from freeze import runtime_pins


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    root=Path(__file__).resolve().parent
    frozen=(root/'FREEZE.json').read_bytes();freeze=json.loads(frozen)
    if runtime_pins()!=freeze['runtime']:raise ValueError('runtime pins changed')
    for name,pin in freeze['source_sha256'].items():
        if sha((root/name).read_bytes())!=pin:raise ValueError('source changed:'+name)
    marker=root/'evidence/ATTEMPT.json'
    with marker.open('xb') as file:
        file.write((json.dumps({'allocation':freeze['allocation'],'freeze_sha256':sha(frozen),
                                'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                'counts_before':{'candidate':0,'audit':0},'caps':freeze['caps'],'retries':0},
                               sort_keys=True,indent=2)+'\n').encode())
    private=root.parents[3]/'6501-custody-private-comparison-receipts.json'
    rows=[]
    def publish():
        private.write_bytes((json.dumps(rows,sort_keys=True,indent=2)+'\n').encode())
        public=[]
        for row in rows:
            value=dict(row);value['argv']=['$PYTHON','-B',row['name']+'.py'];value['cwd']='$PACKAGE'
            public.append(value)
        (root/'evidence/commands.json').write_bytes((json.dumps(public,sort_keys=True,indent=2)+'\n').encode())
    for name in ('candidate','audit'):
        argv=[sys.executable,'-B',str(root/(name+'.py'))]
        receipt={'name':name,'argv':argv,'cwd':str(root),'freeze_sha256':sha(frozen),
                 'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
        rows.append(receipt);publish()
        try:
            result=subprocess.run(argv,cwd=root,capture_output=True,timeout=freeze['outer_timeout_s'],
                                  env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
            stdout,stderr,code=result.stdout,result.stderr,result.returncode
        except subprocess.TimeoutExpired as error:
            stdout,stderr,code=error.stdout or b'',error.stderr or b'',None
            receipt['timeout']=True
        (root/'evidence'/(name+'.stdout')).write_bytes(stdout)
        (root/'evidence'/(name+'.stderr')).write_bytes(stderr)
        receipt.update(ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                       exit_code=code,stdout_sha256=sha(stdout),stderr_sha256=sha(stderr))
        publish();print(name,code,stdout.decode(errors='replace')[:1000],stderr.decode(errors='replace')[:500],flush=True)
        if code!=0:return 1
    return 0


if __name__=='__main__':raise SystemExit(main())
