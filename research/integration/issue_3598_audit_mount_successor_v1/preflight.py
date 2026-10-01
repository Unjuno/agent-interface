"""Non-audit mount/hash preflight for the #3598 raw-only container."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile

parent = Path('/parent')
evidence = Path('/evidence')
out = Path('/out')
expected = {
    'parent/freeze/agent-interface-runtime.pyz':
        'e2f50196e7ac67372fd0c480dbee473d26cc84d33e09806900f1efe7c8e7e624',
    'parent/freeze/manifest.json':
        'cb4b63359ca75e082157b3a49159e5a4d2f9e5c81ae754a27b30f7c27c17bd2c',
    'parent/container_smoke.py':
        'c4ba017b3685d6d4ba78cea2b8ccbecdae6d769e41712da4c1c87e1b88135f75',
    'parent/audit.py':
        '5aaa31729068403e3bf52579ca6b16252395a3aaa7c3b54f992c3fa46b6b54d5',
    'audit_v2.py':
        'fd7ae177fd4b701ed45f4db35db8a0fedda41a2cbaaffa4ed3598dbb59be795a',
}
allocation_sha = {
    'formal-01': '4a68f9627d38c51caa8a6ae404782c0ec64b82a9324b68dbcbd29619c3181878',
    'formal-02': 'c60aed76983283bd13f4b74d9153b1d51e4aa0a1ab37a4b7f5abb00ccfdcd638',
    'formal-03': 'c713224bc73c3d13dc05ce15f0cc4c95b437e40a6330c1d7bffadf8dc3be6f0c',
}
checks = {}
failures = []

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

for rel, digest in expected.items():
    path = Path('/audit_v2.py') if rel == 'audit_v2.py' else (parent/rel.removeprefix('parent/'))
    actual = sha(path) if path.is_file() else None
    checks[rel] = {'exists': path.is_file(), 'sha256': actual, 'expected': digest,
                   'pass': actual == digest}
    if actual != digest:
        failures.append(rel)
with zipfile.ZipFile(parent/'freeze/agent-interface-runtime.pyz') as archive:
    build = json.loads(archive.read('BUILD.json'))
checks['parent_source_revision'] = {
    'actual': build.get('source_revision'),
    'expected': '02b6efb970e66f2169c01c49b1fa6a4ebb5e23f2',
    'pass': build.get('source_revision') == '02b6efb970e66f2169c01c49b1fa6a4ebb5e23f2'}
if not checks['parent_source_revision']['pass']:
    failures.append('parent_source_revision')
for name, digest in allocation_sha.items():
    path = evidence/name/'allocation.json'
    actual = sha(path) if path.is_file() else None
    checks[name+'/allocation.json'] = {'exists': path.is_file(), 'sha256': actual,
        'expected': digest, 'pass': actual == digest}
    if actual != digest:
        failures.append(name+'/allocation.json')
checks['output_mount'] = {'directory': out.is_dir(), 'writable_probe': None}
try:
    probe = out/'preflight.json'
    result = {'schema': 'agent-interface/issue-3598-preflight-v1',
              'outcome': 'PASS' if not failures else 'STOP_PREFLIGHT',
              'checks': checks, 'failures': failures,
              'container_python': sys.version}
    probe.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    checks['output_mount']['writable_probe'] = True
except OSError as error:
    failures.append('output_mount')
    checks['output_mount']['writable_probe'] = repr(error)
result = {'schema': 'agent-interface/issue-3598-preflight-v1',
          'outcome': 'PASS' if not failures else 'STOP_PREFLIGHT',
          'checks': checks, 'failures': failures,
          'container_python': sys.version}
(out/'preflight.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
print(json.dumps(result, sort_keys=True))
raise SystemExit(0 if not failures else 1)
