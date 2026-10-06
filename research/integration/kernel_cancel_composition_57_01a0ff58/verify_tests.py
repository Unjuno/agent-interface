"""Retain ordinary exact-source regression receipts after the primary matrix."""
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
out = HERE / 'verification-01'
out.mkdir(exist_ok=False)
records = []
for name, flags in (('normal', ['-B']), ('optimized', ['-O', '-B'])):
    args = ['-m', 'unittest', 'runtime.kernel.test_kernel', 'runtime.kernel.test_release_epoch',
            'runtime.kernel.test_cancel_release_epoch']
    start = datetime.now(timezone.utc).isoformat()
    run = subprocess.run([sys.executable, *flags, *args], cwd=HERE / 'checks', capture_output=True)
    end = datetime.now(timezone.utc).isoformat()
    (out / (name + '.stdout.txt')).write_bytes(run.stdout)
    (out / (name + '.stderr.txt')).write_bytes(run.stderr)
    records.append({'name': name, 'command': ['python', *flags, *args], 'cwd': 'checks',
                    'started_utc': start, 'finished_utc': end, 'exit': run.returncode,
                    'stdout_sha256': hashlib.sha256(run.stdout).hexdigest(),
                    'stderr_sha256': hashlib.sha256(run.stderr).hexdigest()})
result = {'ordinary_post_assay': True, 'python': sys.version, 'records': records,
          'initial_direct_normal_check': '36 methods, exit0, tool-captured combined output; separate stream/UTC receipts were not captured for that first direct check'}
(out / 'RUN.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'exits': [r['exit'] for r in records]}))
raise SystemExit(any(r['exit'] for r in records))
