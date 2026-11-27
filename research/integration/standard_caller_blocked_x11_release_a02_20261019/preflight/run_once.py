"""A02 offline candidate runner: verify staged dependencies, then execute once."""
import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys

repo = Path('/repo')
out = Path('/out')
bundle = Path('/deps_bundle')
deps = bundle / 'site-packages'
out.mkdir(parents=True, exist_ok=True)
env = os.environ.copy()
env['PYTHONPATH'] = str(deps) + os.pathsep + env.get('PYTHONPATH', '')
manifest = json.loads((bundle / 'dependency-files.json').read_text(encoding='utf-8'))
observed_files = []
for row in manifest:
    path = deps / row['path']
    data = path.read_bytes()
    observed_files.append({'path':row['path'], 'bytes':len(data),
                           'sha256':hashlib.sha256(data).hexdigest()})
cache_hash = hashlib.sha256(json.dumps(observed_files, sort_keys=True,
    separators=(',', ':')).encode()).hexdigest()
manifest_paths = {row['path'] for row in manifest}
actual_paths = {str(path.relative_to(deps)).replace('\\', '/')
                for path in deps.rglob('*') if path.is_file()}
cache_valid = (observed_files == manifest and cache_hash ==
    json.loads((bundle / 'stage-result.json').read_text(encoding='utf-8'))[
        'dependency_tree_sha256'] and actual_paths == manifest_paths)
(out / 'dependency-cache-validation.json').write_text(json.dumps({
    'status':'PASS' if cache_valid else 'FAIL',
    'file_count':len(observed_files), 'tree_sha256':cache_hash,
    'unlisted_file_count':len(actual_paths - manifest_paths),
    'missing_file_count':len(manifest_paths - actual_paths)},
    sort_keys=True, indent=2), encoding='utf-8')
if not cache_valid:
    raise SystemExit('staged dependency cache does not match its frozen manifest')
freeze = subprocess.run([sys.executable, '-m', 'pip', 'freeze', '--path', str(deps)],
    text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
(out / 'pip-freeze.txt').write_text(freeze.stdout, encoding='utf-8')
(out / 'pip-freeze-exit-code.txt').write_text(str(freeze.returncode), encoding='ascii')
if freeze.returncode:
    raise SystemExit(freeze.returncode)
expected = {line.split('==', 1)[0].lower().replace('_', '-'):line.split('==', 1)[1]
            for line in (repo / 'preflight/requirements.lock').read_text(
                encoding='utf-8').splitlines() if line.strip()}
actual = {}
for line in freeze.stdout.splitlines():
    if '==' in line:
        name, version = line.split('==', 1)
        actual[name.lower().replace('_', '-')] = version
missing = {name:version for name,version in expected.items()
           if actual.get(name) != version}
if missing:
    (out / 'dependency-mismatch.json').write_text(json.dumps({
        'expected':expected, 'actual':actual, 'mismatch':missing}, sort_keys=True, indent=2),
        encoding='utf-8')
    raise SystemExit('staged dependency versions differ from frozen lock')
env['AGENT_INTERFACE_A02_OUT'] = str(out)
probe = subprocess.run([sys.executable, '-B', str(repo / 'probe.py')],
    cwd=repo, env=env, text=True, stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT)
(out / 'probe-console.log').write_text(probe.stdout, encoding='utf-8')
(out / 'probe-exit-code.txt').write_text(str(probe.returncode), encoding='ascii')
raise SystemExit(probe.returncode)
