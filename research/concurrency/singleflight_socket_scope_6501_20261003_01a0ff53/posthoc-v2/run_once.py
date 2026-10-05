"""Bound one supplemental raw-only CLI against a committed prospective freeze."""
import datetime
import hashlib
import importlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
REL = ROOT.relative_to(REPO)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def write(path, record):
    with path.open('x') as out:
        json.dump(record, out, indent=2, sort_keys=True); out.write('\n')


source = sys.argv[1]
freeze_bytes = (ROOT / 'FREEZE.json').read_bytes()
committed = subprocess.check_output(['git', 'show', f'{source}:{REL}/FREEZE.json'], cwd=REPO)
if freeze_bytes != committed:
    raise SystemExit('STOP freeze differs from committed source')
freeze = json.loads(freeze_bytes)
for name, wanted in freeze['source_sha256'].items():
    data = (ROOT / name).read_bytes()
    committed = subprocess.check_output(['git', 'show', f'{source}:{REL}/{name}'], cwd=REPO)
    if digest(data) != wanted or committed != data:
        raise SystemExit('STOP posthoc source mismatch: ' + name)
for name, wanted in freeze['original_input_sha256'].items():
    if digest((ROOT / name).read_bytes()) != wanted:
        raise SystemExit('STOP original retained input mismatch: ' + name)
if digest(Path(sys.executable).read_bytes()) != freeze['executable_sha256']:
    raise SystemExit('STOP interpreter mismatch')
for name, wanted in freeze['json_module_sha256'].items():
    if digest(Path(importlib.import_module(name).__file__).read_bytes()) != wanted:
        raise SystemExit('STOP JSON dependency mismatch: ' + name)
output = ROOT / 'run-01'
output.mkdir(exist_ok=False)
write(output / 'PRE_RUN.json', dict(source_commit=source, source_verified_utc=utc(),
      freeze_sha256=digest(freeze_bytes), raw_sha256=freeze['original_input_sha256']['../run-a01/raw.json'],
      candidate_invocations=0, supplemental_cli_invocations=1, retries=0))
argv = [sys.executable, '-B', 'audit_v2.py', '--fixtures', '../fixtures.json',
        '--raw', '../run-a01/raw.json', '--output', 'run-01/audit.json']
start = utc()
with (output / 'audit.stdout.txt').open('xb') as out, (output / 'audit.stderr.txt').open('xb') as err:
    try:
        result = subprocess.run(argv, cwd=ROOT, stdout=out, stderr=err,
                                timeout=freeze['timeout_seconds'], check=False)
        code, state = result.returncode, 'completed'
    except subprocess.TimeoutExpired:
        code, state = None, 'timeout'
record = dict(argv=['python3', *argv[1:]], cwd=str(REL), start_utc=start,
              end_utc=utc(), actual_exit=code, state=state, source_commit=source,
              candidate_invocations=0, supplemental_cli_invocations=1, retries=0)
write(output / 'EXECUTION.json', record)
print(json.dumps(record, sort_keys=True))
if code != 0:
    raise SystemExit('STOP first supplemental outcome retained')
if sum(p.stat().st_size for p in output.iterdir()) > freeze['output_max_bytes']:
    raise SystemExit('STOP supplemental output bound; original result retained')
