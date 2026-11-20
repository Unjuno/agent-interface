"""Restore saved data, then run only offline audit and candidate regressions."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from restore_results import restore

ROOT = Path(__file__).resolve().parent
out = Path(sys.argv[1]).resolve()
meta = json.loads((ROOT / 'PACK.json').read_text())
wire = ''.join((ROOT / ('results.xz.b64.part%02d' % i)).read_text() for i in (1, 2, 3, 4))
count = restore(meta, wire, out)
freeze = json.loads((ROOT / 'FREEZE.json').read_text())
for name in ['FREEZE.json'] + [n for n in freeze['sha256'] if not n.startswith('candidate/')]:
    p = out / name
    p.parent.mkdir(exist_ok=True, parents=True)
    shutil.copyfile(ROOT / name, p)
commands = []

def checked(args, env=None):
    result = subprocess.run([sys.executable, '-B'] + args, cwd=out, env=env,
                            capture_output=True, timeout=20)
    commands.append({'argv': result.args, 'returncode': result.returncode,
                     'stdout': result.stdout.decode(), 'stderr': result.stderr.decode()})
    if result.returncode != 0:
        raise RuntimeError(commands[-1])
    return result.stdout

checked(['prepare.py'])
audit = checked(['audit.py', 'results/raw.json', '--controls'])
if audit != (out / 'results/AUDIT.json').read_bytes():
    raise ValueError('saved audit byte mismatch')
for name in ('run', 'audit'):
    receipt = json.loads((out / ('results/' + name + '.receipt.json')).read_text())
    if type(receipt['returncode']) is not int or receipt['returncode'] != 0 or receipt['timed_out'] is not False:
        raise ValueError('saved process receipt')
    if (out / ('results/' + name + '.stderr')).read_bytes():
        raise ValueError('unexpected saved stderr')
env = dict(os.environ)
env['PYTHONPATH'] = os.pathsep.join([str(out/'candidate'), str(out/'source')])
checked(['test_elapsed.py'], env)
for name, spec in meta['files'].items():
    data = (out / name).read_bytes()
    if len(data) != spec['bytes'] or hashlib.sha256(data).hexdigest() != spec['sha256']:
        raise ValueError('retained bytes changed: ' + name)
result = {'status': 'PASS_SAVED_DATA_REVALIDATION', 'restored_files': count,
          'new_matrix_invocations': 0, 'same_author_review': True, 'commands': commands,
          'raw_sha256': hashlib.sha256((out/'results/raw.json').read_bytes()).hexdigest()}
print(json.dumps(result, sort_keys=True, indent=2))
