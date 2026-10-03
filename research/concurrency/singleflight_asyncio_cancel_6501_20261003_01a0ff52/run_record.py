"""Source/limit preflight and one child invocation; writes actual exit receipt."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

def main():
    parser=argparse.ArgumentParser();parser.add_argument('kind',choices=['candidate','audit']);parser.add_argument('--out',required=True)
    args=parser.parse_args();src=Path(__file__).resolve().parent;out=Path(args.out)
    freeze=json.loads((src/'FREEZE.json').read_bytes())
    hashes={name:hashlib.sha256((src/name).read_bytes()).hexdigest() for name in freeze['source_sha256']}
    cpu=Path('/sys/fs/cgroup/cpu.max').read_text().strip()
    memory=Path('/sys/fs/cgroup/memory.max').read_text().strip()
    environment=dict(python=sys.version,source_sha256=hashes,cpu_max=cpu,memory_max=memory,
                     started_utc=datetime.now(timezone.utc).isoformat())
    def write(name,obj):
        with (out/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,indent=2,sort_keys=True);f.write('\n')
    write(args.kind+'-environment.json',environment)
    if hashes!=freeze['source_sha256'] or sys.version.split()[0]!=freeze['python_version'] or cpu!='25000 100000' or memory!='134217728':
        write(args.kind+'-receipt.json',dict(exit_code=2,child_invocations=0,status='STOP_PREFLIGHT',environment=environment))
        return 2
    command=([sys.executable,str(src/'candidate.py'),'--output',str(out/'raw.json')] if args.kind=='candidate' else
             [sys.executable,str(src/'audit.py'),str(out/'raw.json'),'--output',str(out/'audit.json')])
    start=datetime.now(timezone.utc).isoformat()
    try:
        result=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30)
        with (out/(args.kind+'.log')).open('xb') as f:f.write(result.stdout)
        receipt=dict(argv=command,start_utc=start,end_utc=datetime.now(timezone.utc).isoformat(),exit_code=result.returncode,child_invocations=1,
                     log_sha256=hashlib.sha256(result.stdout).hexdigest())
    except subprocess.TimeoutExpired as exc:
        with (out/(args.kind+'.log')).open('xb') as f:f.write(exc.stdout or b'')
        receipt=dict(argv=command,start_utc=start,end_utc=datetime.now(timezone.utc).isoformat(),exit_code=None,child_invocations=1,status='STOP_TIMEOUT')
    write(args.kind+'-receipt.json',receipt)
    print(json.dumps(receipt,sort_keys=True))
    return receipt['exit_code'] if receipt['exit_code'] is not None else 124

if __name__=='__main__':raise SystemExit(main())
