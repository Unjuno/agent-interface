"""Run the declared12 cells once; refuse existing output and stop on first error."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent

def main():
    freeze=json.loads((ROOT/'FREEZE.json').read_text())
    for name,digest in freeze['files'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('source differs from freeze: '+name)
    out=ROOT/'matrix'
    out.mkdir(exist_ok=False)
    rows=[];receipts=[]
    for condition in ('NO_HOLD','SHIFT_SAME','SHIFT_ALIAS','CTRL_DISJOINT','SHIFT_TEXT_UPPER','SHIFT_ALREADY_RELEASED'):
        for variant in ('current','proposal'):
            index=len(rows)
            case=out/f'{index:02d}'
            cmd=[sys.executable,'-B',str(ROOT/'run_case.py'),condition,variant,str(case)]
            start=time.monotonic_ns()
            with (out/f'{index:02d}.stdout').open('xb') as stdout, (out/f'{index:02d}.stderr').open('xb') as stderr:
                proc=subprocess.Popen(cmd,stdout=stdout,stderr=stderr)
                try:rc=proc.wait(timeout=25)
                except subprocess.TimeoutExpired:
                    proc.terminate();rc=proc.wait(timeout=8)
                    receipts.append(dict(argv=cmd,pid=proc.pid,returncode=rc,timeout=True))
                    (out/'LAUNCHER.json').write_text(json.dumps(receipts,indent=2)+'\n')
                    raise RuntimeError('case timeout; preserve partial data; no later cells')
            receipts.append(dict(argv=cmd,pid=proc.pid,returncode=rc,started_ns=start,ended_ns=time.monotonic_ns()))
            (out/'LAUNCHER.json').write_text(json.dumps(receipts,indent=2)+'\n')
            if rc!=0:raise RuntimeError('case failed; preserve partial data; no later cells')
            rows.append(json.loads((case/'record.json').read_text()))
            (out/'RECORDS.json').write_text(json.dumps(rows,sort_keys=True,separators=(',',':'))+'\n')
    print(json.dumps(dict(cases=len(rows),case_launches=len(receipts),source_freeze=hashlib.sha256((ROOT/'FREEZE.json').read_bytes()).hexdigest())))

if __name__=='__main__':main()
