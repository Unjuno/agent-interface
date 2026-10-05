"""Ordinary repair regression; retained T0/T0A allocations are not repeated."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

p = Path(__file__).resolve().parent
pins = json.loads((p/'SOURCE_PINS.json').read_text())
old = p.parents[2] / pins['path']
names = ['Dockerfile', 'payload.txt', 'probe.py', 'build.output.txt', 'run.output.txt', 'POSTRUN_CHECK.json', 'RUN.json']

def utc():
    return datetime.now(timezone.utc).isoformat()

def run(script, evidence):
    argv = [sys.executable, '-B', str(script), '--root', str(evidence)]
    start = utc()
    child = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = child.communicate(timeout=10)
    return {'argv': argv, 'pid': child.pid, 'started_utc': start, 'ended_utc': utc(), 'exit_code': child.returncode, 'stdout': stdout, 'stderr': stderr}

def main():
    cases = [('original', None, None)]
    cases += [('hash_'+n, n, 'append') for n in names[3:]]
    cases += [('image_build', 'RUN.json', 'build'), ('image_postrun', 'RUN.json', 'postrun_check')]
    cases += [('source_'+n, n, 'append') for n in names[:3]]
    cases += [('missing_'+n, n, 'missing') for n in names]
    (p/'cases').mkdir() # refuse an existing output set
    matrix = {'kind': 'ordinary_saved_data_regression', 'worker_id': os.environ.get('CODEX_SESSION_ID'), 'host': platform.platform(), 'python':sys.version, 'started_utc':utc(), 'rows':[]}
    for cid, name, mutation in cases:
        dest = p/'cases'/cid
        dest.mkdir()
        for n in names:
            shutil.copyfile(old/n, dest/n)
        if mutation == 'append':
            with (dest/name).open('ab') as stream: stream.write(b' ')
        elif mutation == 'missing':
            (dest/name).unlink()
        elif mutation:
            data = json.loads((dest/name).read_text())
            key = 'result_image_id' if mutation == 'build' else 'image_id'
            data[mutation][key] = 'sha256:' + '0'*64
            (dest/name).write_text(json.dumps(data, indent=2)+'\n')
        audits = {}
        if cid == 'original' or cid.startswith(('hash_', 'image_')):
            audits['legacy'] = run(old/'audit_t0.py', dest)
        audits['v2'] = run(p/'audit_v2.py', dest)
        row = {'id':cid,'inputs':{n:hashlib.sha256((dest/n).read_bytes()).hexdigest() if (dest/n).exists() else None for n in names}, 'audits':audits}
        matrix['rows'].append(row)
        (p/'matrix.partial.json').write_text(json.dumps(matrix,indent=2)+'\n')
    matrix['ended_utc'] = utc()
    (p/'matrix.json').write_text(json.dumps(matrix,indent=2)+'\n')
    (p/'matrix.partial.json').unlink() # own provisional copy, final persisted above
    print(json.dumps({'rows':len(matrix['rows']), 'legacy_false_accepts':sum(r['id'] != 'original' and r['audits'].get('legacy',{}).get('exit_code') == 0 for r in matrix['rows']), 'v2_rejected':sum(r['audits']['v2']['exit_code'] == 1 for r in matrix['rows'])}))


if __name__ == "__main__":
    main()
