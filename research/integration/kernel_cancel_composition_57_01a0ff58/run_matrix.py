"""Once-only frozen source execution; preserve complete child outputs and exits."""
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
freeze_data = (HERE / 'FREEZE.json').read_bytes()
freeze = json.loads(freeze_data)
for name, digest in freeze['files'].items():
    if hashlib.sha256((HERE / name).read_bytes()).hexdigest() != digest:
        raise ValueError('freeze drift:' + name)
out = HERE / 'run-01'
out.mkdir(exist_ok=False)
records, arms = [], []
for arm, sources in sorted(freeze['arms'].items()):
    start = datetime.now(timezone.utc).isoformat()
    command = [sys.executable, '-I', '-B', str(HERE / 'child_arm.py'), arm]
    run = subprocess.run(command, cwd=HERE, capture_output=True)
    finished = datetime.now(timezone.utc).isoformat()
    (out / (arm + '.stdout.json')).write_bytes(run.stdout)
    (out / (arm + '.stderr.txt')).write_bytes(run.stderr)
    records.append({'arm': arm, 'command': ['python', '-I', '-B', 'child_arm.py', arm],
                    'started_utc': start, 'finished_utc': finished, 'exit': run.returncode,
                    'stdout_sha256': hashlib.sha256(run.stdout).hexdigest(),
                    'stderr_sha256': hashlib.sha256(run.stderr).hexdigest()})
    if run.returncode:
        break
    payload = json.loads(run.stdout)
    arms.append({**payload, 'source_sha256': sources})
record = {'study': freeze['study'], 'python': sys.version, 'platform': sys.platform,
          'children': records, 'backend_input_model_container_gpu_invocations': 0}
(out / 'RUN.json').write_text(json.dumps(record, sort_keys=True, indent=2) + '\n', encoding='utf-8')
raw = {'study': freeze['study'], 'freeze_sha256': hashlib.sha256(freeze_data).hexdigest(), 'arms': arms}
(out / 'raw.json').write_text(json.dumps(raw, sort_keys=True, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'children': len(records), 'exits': [r['exit'] for r in records],
                  'rows': sum(len(a['rows']) for a in arms)}))
raise SystemExit(len(arms) != 8 or any(r['exit'] for r in records))
