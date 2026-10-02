"""Run one explicitly named local batch once and retain actual process receipt."""
from pathlib import Path
import json
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
if __name__ == '__main__':
    index = int(sys.argv[1])
    if index not in range(3):
        raise ValueError('batch must be 0, 1 or 2')
    output = ROOT/'raw'/f'batch{index}.json'
    receipt = ROOT/'raw'/f'batch{index}.process.json'
    output.parent.mkdir(exist_ok=True)
    if output.exists() or receipt.exists():
        raise FileExistsError('consumed batch; no retry')
    argv = [sys.executable, '-B', str(ROOT/'run.py'), str(output), str(index)]
    record = dict(argv=argv, batch=index, start_ns=time.monotonic_ns())
    with receipt.open('x') as f:
        f.write(json.dumps(record))
    p = subprocess.Popen(argv, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    record['pid'] = p.pid
    try:
        stdout, stderr = p.communicate(timeout=35)
        record.update(returncode=p.returncode, stdout=stdout.decode(), stderr=stderr.decode(), timeout=False)
    except subprocess.TimeoutExpired:
        p.kill()
        stdout, stderr = p.communicate()
        record.update(returncode=p.returncode, stdout=stdout.decode(), stderr=stderr.decode(), timeout=True)
    record['end_ns'] = time.monotonic_ns()
    receipt.write_text(json.dumps(record, sort_keys=True, indent=2)+'\n')
    print(json.dumps(record, sort_keys=True))
    raise SystemExit(0 if record['returncode']==0 and not record['timeout'] else 1)
