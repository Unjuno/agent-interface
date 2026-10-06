"""Freeze exact four-module subsets without changing any Git ref or checkout."""
import hashlib
import itertools
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent / 'agent-interface'
BASE = 'a394fcdd4254679df4265622b8ae6d0f8e251849'
REFS = {'R': 'f3ecf397ae8618cf700e8f6b927bb688e32a42b4',
        'C': 'd06e636a8c35715d371dc6ba00632aab4b3bad3c',
        'U': 'fa276a1c5b85c45251f2ffd175e65fb18836d664'}
PARENTS = {'R': '11f1bae6f8dbfd280b6ccbd0def0bc23fa5da68d',
           'C': 'cb13a10dce358649458f5aea00947b8aa43fc5b8',
           'U': 'cb13a10dce358649458f5aea00947b8aa43fc5b8'}
MODULES = ('__init__.py', 'backend.py', 'contracts.py', 'lifecycle.py')


def git(*args):
    return subprocess.check_output(['git', *args], cwd=REPO)


snap = HERE / 'snapshots'
snap.mkdir(exist_ok=False)
baseline = {name: git('show', BASE + ':runtime/kernel/' + name) for name in MODULES}
for name, data in baseline.items():
    (snap / ('base-' + name)).write_bytes(data)
selected = {}
for role, ref in REFS.items():
    name = 'contracts.py' if role == 'R' else 'lifecycle.py'
    if baseline[name] != git('show', PARENTS[role] + ':runtime/kernel/' + name):
        raise ValueError('base production drift:' + role)
    selected[role] = git('show', ref + ':runtime/kernel/' + name)
    (snap / (role + '-' + name)).write_bytes(selected[role])
merged = subprocess.run(['git', 'merge-file', '--stdout', str(snap / 'C-lifecycle.py'),
                         str(snap / 'base-lifecycle.py'), str(snap / 'U-lifecycle.py')],
                        capture_output=True)
(snap / 'merge.stderr.txt').write_bytes(merged.stderr)
if merged.returncode:
    raise ValueError('source-only composition conflict:' + str(merged.returncode))
(snap / 'CU-lifecycle.py').write_bytes(merged.stdout)
arms = {}
for bits in itertools.product('01', repeat=3):
    arm = ''.join(bits)
    directory = HERE / 'sources' / arm / 'runtime/kernel'
    directory.mkdir(parents=True, exist_ok=False)
    files = dict(baseline)
    if bits[0] == '1':
        files['contracts.py'] = selected['R']
    c, u = bits[1:] == ('1', '1'), bits[2] == '1'
    if c:
        files['lifecycle.py'] = merged.stdout
    elif bits[1] == '1':
        files['lifecycle.py'] = selected['C']
    elif u:
        files['lifecycle.py'] = selected['U']
    for name, data in files.items():
        (directory / name).write_bytes(data)
    arms[arm] = {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
checks = HERE / 'checks/runtime/kernel'
checks.mkdir(parents=True, exist_ok=False)
for name in MODULES:
    (checks / name).write_bytes((HERE / 'sources/111/runtime/kernel' / name).read_bytes())
for role, name in (('R', 'test_release_epoch.py'), ('C', 'test_cancel_release_epoch.py'), ('U', 'test_kernel.py')):
    (checks / name).write_bytes(git('show', REFS[role] + ':runtime/kernel/' + name))
all_files = [p for p in HERE.rglob('*') if p.is_file()]
freeze = {'study': 'KERNEL-CANCEL-COMPOSITION-57-01a0ff58-20261003-01',
          'policy': 'FINAL-v5', 'base_main': BASE, 'roles': REFS, 'parents': PARENTS,
          'frozen_utc': datetime.now(timezone.utc).isoformat(), 'arms': arms,
          'files': {p.relative_to(HERE).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in all_files},
          'merge_command': ['git', 'merge-file', '--stdout', 'C-lifecycle.py', 'base-lifecycle.py', 'U-lifecycle.py'],
          'merge_exit': merged.returncode, 'rows': 96}
with (HERE / 'FREEZE.json').open('x', encoding='utf-8', newline='\n') as handle:
    handle.write(json.dumps(freeze, sort_keys=True, indent=2) + '\n')
print(json.dumps({'frozen_files': len(all_files), 'arms': len(arms), 'merge_exit': merged.returncode,
                  'freeze_sha256': hashlib.sha256((HERE / 'FREEZE.json').read_bytes()).hexdigest()}))
