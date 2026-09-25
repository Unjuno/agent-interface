"""One finite, input-free compatibility measurement; does not start backends."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from cases import corpus

HERE = Path(__file__).resolve().parent
CLI_IDS = [0, 44, 88, 11, 55, 99, 138, 139]
SMOKE_IDS = [0, 4, 11, 44, 48, 55, 88, 92, 99]


def digest(b):
    return hashlib.sha256(b).hexdigest()


def encode(x):
    return json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=True)


def invoke(argv, cwd, env):
    started = time.monotonic_ns()
    child = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        out, err = child.communicate(timeout=10)
    except subprocess.TimeoutExpired:
        child.kill(); out, err = child.communicate()
        raise RuntimeError('owned child timeout; pid=' + str(child.pid))
    return {'argv': argv, 'pid': child.pid, 'exit': child.returncode,
            'start_ns': started, 'end_ns': time.monotonic_ns(),
            'stdout': out.decode('utf-8'), 'stderr': err.decode('utf-8'),
            'stdout_sha256': digest(out), 'stderr_sha256': digest(err)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('baseline', type=Path); p.add_argument('candidate', type=Path)
    p.add_argument('out', type=Path); p.add_argument('--construction', action='store_true')
    a = p.parse_args(); a.out.mkdir(parents=True, exist_ok=False)
    all_cases = corpus()
    rows = [x for x in all_cases if x['id'] in SMOKE_IDS] if a.construction else all_cases
    cp = a.out/'CASES.json'; cp.write_text(encode(rows)+'\n', encoding='utf-8')
    freeze = json.loads((HERE/'FREEZE.json').read_text()) if not a.construction else None
    document = {'schema': 'enum-types-measurement-e9q4-v1',
                'mode': 'construction' if a.construction else 'retained',
                'cases': rows, 'workers': {}, 'cli': [], 'sources': {},
                'python': sys.version, 'platform': platform.platform(),
                'display_removed': True, 'freeze_sha256': digest((HERE/'FREEZE.json').read_bytes()) if freeze else None}
    for arm, root in [('baseline', a.baseline.resolve()), ('candidate', a.candidate.resolve())]:
        entries = ['runtime/core_v1/contract.py','runtime/core_v1/__init__.py',
                   'runtime/core_v1/platform_probe.py','runtime/core_v1/sequence.py',
                   'runtime/cli_v1/validate_program.py']
        document['sources'][arm] = {k: digest((root/k).read_bytes()) for k in entries}
    if freeze and document['sources'] != freeze['runtime_sha256']:
        raise RuntimeError('SOURCE_FREEZE_MISMATCH')
    if freeze:
        for name, value in freeze['study_sha256'].items():
            if digest((HERE/name).read_bytes()) != value:
                raise RuntimeError('STUDY_FREEZE_MISMATCH:' + name)
    try:
        for arm, root in [('baseline', a.baseline.resolve()), ('candidate', a.candidate.resolve())]:
            env = {k:v for k,v in os.environ.items() if k not in ('DISPLAY','WAYLAND_DISPLAY','XAUTHORITY','PYTHONPATH')}
            env['PYTHONPATH'] = str(root); env['PYTHONDONTWRITEBYTECODE'] = '1'
            receipt = invoke([sys.executable, '-S', '-B', str(HERE/'worker.py'), str(root), str(cp.resolve())], str(root), env)
            document['workers'][arm] = receipt
            (a.out/'PARTIAL.json').write_text(encode(document)+'\n', encoding='utf-8')
            if receipt['exit'] != 0 or receipt['stderr']:
                raise RuntimeError('WORKER_FAILURE:' + arm)
            ids = [0,11] if a.construction else CLI_IDS
            for row in rows:
                if row['id'] not in ids: continue
                inp = a.out/(arm+'-'+str(row['id'])+'.json')
                inp.write_text(encode(row['program'])+'\n', encoding='utf-8')
                before = inp.read_bytes()
                rc = invoke([sys.executable, '-S', '-B', str(root/'runtime/cli_v1/validate_program.py'),
                             '--program', str(inp.resolve())], str(root), env)
                rc.update(arm=arm, id=row['id'], input_bytes=before.decode('utf-8'),
                          input_unchanged=inp.read_bytes()==before)
                document['cli'].append(rc)
                if rc['exit'] not in (0,1) or rc['stderr']:
                    raise RuntimeError('CLI_FAILURE:' + arm)
        for arm, root in [('baseline', a.baseline.resolve()), ('candidate', a.candidate.resolve())]:
            for name, expected in document['sources'][arm].items():
                if digest((root/name).read_bytes()) != expected: raise RuntimeError('SOURCE_CHANGED')
        document['complete'] = True
        (a.out/'RAW.json').write_text(encode(document)+'\n', encoding='utf-8')
        print(json.dumps({'case_count': len(rows), 'worker_count':2, 'cli_count':len(document['cli']),
                          'raw_sha256': digest((a.out/'RAW.json').read_bytes())}, sort_keys=True))
        return 0
    except Exception as e:
        document['stop'] = type(e).__name__ + ':' + str(e)
        (a.out/'STOP.json').write_text(encode(document)+'\n', encoding='utf-8')
        raise


if __name__ == '__main__':
    raise SystemExit(main())
